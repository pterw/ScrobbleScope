# Statistics module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every listening statistic a page shows is computed in Python, in UTC, with its population stated in code and published with the figure. `static/js/heatmap.js`, `static/js/results.js` and `templates/results.html` only render what they are given (review card B-4).

**Architecture:** A new pure module `scrobblescope/listening_stats.py` (a leaf: standard library only) holds the rules that today live in the browser and in a Jinja sum: current streak, best day, daily average and total for the heatmap; plays listed and plays matched for the Results page. The heatmap job publishes them as `statistics` beside its existing keys. The Results route computes the album figures from the rows it is about to render and hands them to the template. Six tasks on `refactor/statistics-module`, each one atomic commit. Design sources: `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` (PR #6 in its table) and `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` (section P6).

**Tech Stack:** Python 3.13, Flask/Jinja2, vanilla JS (IIFE modules), pytest, Playwright Chromium (`browser` marker), the frontend gate, pre-commit, docsync.

## Assumptions checked against `C:/ssw/kb` (5dde407)

The Task 28 brief and card B-4 predate PR #245. Each claim was checked in the include-unmatched head.

| Claim in the brief or card | Held? | What the code says |
|---|---|---|
| `heatmap.js` has `computeStreak` and `renderKpis` doing streak, best day, daily average | Held | Both exist; line numbers moved, so cite names. `renderKpis(data, dailyCounts, toDate)` is called from `renderHeatmapDesktop` and `renderHeatmapMobile`. |
| The average divides by a window constant | Held, with a consequence the brief missed | `WINDOW_DAYS = 365` in `heatmap.js` is a declared copy: `config/docsync.toml` has sites for `WINDOW_DAYS = (\d+)` and for the comment text `whole (\d+)-day window` in that file. Deleting the code without the declarations fails DOC009. Task 3 handles it. |
| Best day is "reduce over daily_counts" | Held | `dayKeys.reduce(a >= b ? a : b)` over zero-filled ascending keys: the **earliest** day wins a tie. The Python rule must keep that. |
| Streak may end yesterday | Held | Same rule, `computeStreak`. Counting stops at the first day with no plays, so it never reaches past the window's first day. |
| `results.html` sums "Scrobbles" over displayed rows | Held, refined | `total_scrobbles = album_list | sum(attribute='play_count')`, where `album_list` is `filtered_results` from `_filter_results_for_display`. So the population is "rows on the page": it includes include-unmatched rows, and it drops zero-duration albums on a playtime ranking. |
| (not in the brief) | New | `results.js` `setUnmatchedHidden` recomputes the same figure in the browser by summing `data-play-count` when the Unmatched albums control switches. That is a second copy of the rule, in scope. |
| Facts are "published on the album job result" | Did NOT hold as written | The album job result is a bare list of rows, and the population depends on a display filter that lives in the route (`_filter_results_for_display`). Publishing at job completion would change the number users see on a playtime run. The plan computes at render time instead; see Owner question 1. |
| `heatmap.py` returns only `daily_counts`, `max_count`, `total_scrobbles` | Held, plus three keys | It also returns `username`, `from_date`, `to_date`, and records `active_days` as a job stat. `heatmap_data` returns `{"ready": True, **results}`, so a new key reaches the browser with no route change. |
| `_results.py` percent-of-max/total over filtered rows | Held, out of scope | `proportion_of_max` and `proportion_of_total` are ranking aids, not statistics the page states as figures. Left alone. |
| Q14 deferred `computeStreak` tests to WP-6 | Held | The docstring of `tests/frontend/test_heatmap_pure_functions.py` says so; Task 1 and Task 4 update it. |
| Task 28 "After: 23 (normalized plays and the typed aggregate)" | Not needed | This PR consumes day counts and result rows, both of which exist today. See the PR #4 table. |

## Assumptions about PR #4 (merged; checked at eb0db9e)

PR #4 (`refactor/lastfm-scrobbles`) and PR #3 (`refactor/album-request-module`) are merged into the base. The assumptions this plan made while #4 had no plan on disk are resolved below; the plan names no type #4 introduced beyond these.

| Name this plan relies on | Where | Relied-on behaviour | Status at eb0db9e |
|---|---|---|---|
| `plays.aggregate_daily_counts` output (was `heatmap._aggregate_daily_counts`) | `scrobblescope/plays.py`, called from `heatmap._fetch_and_process_heatmap` as `aggregate_daily_counts(fetch.plays, from_date, to_date)` | Returns a zero-filled `{"YYYY-MM-DD": int}` dict covering `[from_date, to_date]`, keyed by the play's UTC date. Task 4 does not edit it. | Renamed; same contract. |
| The heatmap job result keys | `heatmap._fetch_and_process_heatmap` | `username`, `from_date`, `to_date`, `total_scrobbles`, `max_count`, `daily_counts` stay; Task 4 adds `statistics`. | Unchanged. |
| Result rows of the album job | `orchestrator/_results.py` (`_build_results`, `merge_unmatched_rows`) | Dicts with `play_count` (int) and, for an included unmatched row only, a truthy `unmatched_reason`. | Unchanged; `_row_plays` and `_is_unmatched` in `listening_stats.py` hold. |
| `heatmap._fetch_and_process_heatmap` body | `scrobblescope/heatmap.py` | Task 4 edits `to_date`, the statistics call and the `jobs.succeed` payload, a few lines from the log-line edits #4 made. | #4 is merged; no textual conflict is pending. |
| Test helpers for the fetch | `tests/test_heatmap.py` | `_play(day)` (a `Play` at noon UTC) and `_fetch(plays, expected=1, received=1)` (a `ScrobbleFetch`), with `UTC` imported. Task 4's new test uses them. | Replaces `_make_track` and `_wrap_tracks`, which no longer exist. |
| Fetch patch target and return shape | `scrobblescope/heatmap.py`, `tests/test_heatmap.py` | `scrobblescope.heatmap.fetch_scrobbles` returns a `ScrobbleFetch`. The happy-path test and `test_statistics_reach_the_browser_through_heatmap_data` share this shape. | Replaces `fetch_all_recent_tracks_async` returning `([page], meta)`. |
| #4's one publish step | `orchestrator`, `jobs.succeed` | `finish_album_job` -> `_process_filtered_albums` -> `jobs.succeed(job_id, results, ...)` stores the bare list of row dicts (the empty branch stores `[]`), and `routes/album_flow.py` reads `job_context["results"]` as that list. Tasks 1 and 5 call `jobs.succeed(job_id, rows, ...)` the same way. | Holds; no F-B23-1 container exists. |
| PR #3 edits `routes/album_flow.py` | `_filter_results_for_display(results_data, sort_mode)`, `_render_results_page`, `TEST_JOB_PARAMS` | Task 5 adds one import, one line after `_filter_results_for_display` and `play_stats=` on both `render_template("results.html", ...)` calls. | Merged; `TEST_JOB_PARAMS` gained `"mode": "album"` and `/results_complete` still renders. |
| `_frontend_gate_*` heatmap fixtures | `scripts/dev/_frontend_gate_heatmap_access.py`, `_frontend_gate_theme.py`, `_frontend_gate_pipeline.py`, `_frontend_gate_figures.py` | Seed `jobs.succeed(job_id, {...})` payloads by hand (the last holds its payload as the constant `_HEATMAP_RESULT`). | Four files, eight payloads (Task 4 Step 5). |

## Global Constraints

- Every commit is atomic and carries its own untagged PLAYBOOK Section 4 entry, placed directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` line (AGENTS.md "Side-Task Handling").
- Commit procedure, every commit, in this order (AGENTS.md "Commit Rules"): write the Section 4 entry; `pytest -q` and measure N; `doc_state_sync.py --fix --test-count N` (bare `--fix` when N is unchanged); stage by name, never `git add -A` or `git add .`; `pre-commit run --all-files` and re-stage anything a hook rewrote; `doc_state_sync.py --check` exits 0; commit.
- Commit subject `<type>(<scope>): <Capitalised imperative>`, at most 72 characters; body explains why. No `Co-authored-by` trailer.
- From the linked worktree `C:/ssw/st`, every Python command uses the primary checkout's interpreter: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"` (and `pre-commit.exe`, `ruff.exe` beside it).
- Markdown is ASCII only (`--`, never an em dash). Cite code by name, not line number.
- New tests assert intended behaviour, not the code as written, and each comes with mutation evidence: the planted defect named and the test shown failing.
- `WT003 refactor/statistics-module` and `WT010` are expected advisories from the `worktree-alignment` hook; the hook still passes.
- Do not push. The controller pushes and opens the PR (Task 6).
- A refactor starts from parity tests in a preceding commit (AGENTS.md "Refactor requires parity tests"): Task 1 pins today's behaviour before Tasks 4 and 5 move it. A task that edits an existing test names it in its commit body.
- Docstrings: every new function has a docstring; comments say why (AGENTS.md "Docstrings and comments").
- Hosting cost ceiling (spec): nothing in this PR keeps the production database awake, adds a machine or adds a service. It adds no I/O at all: the module is pure and runs on data the job already holds.
- Browser harness and frontend gate runs happen one at a time on the owner's machine. The harness command is `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest tests/frontend -q -p no:cacheprovider`; the gate is `... scripts/dev/frontend_gate.py`.
- Rows from the include-unmatched control (spec amendment, WP-6, 2026-10-20) carry no provider metadata and no durations. Their plays count in `plays_listed`, never in `plays_matched`, and they contribute no listening time (this PR computes none).

## File Structure

| File | Responsibility |
|---|---|
| `scrobblescope/listening_stats.py` (new) | Pure statistics: `utc_date`, `current_streak`, `best_day`, `daily_average`, `heatmap_statistics`, `album_play_statistics`. Standard library only. |
| `tests/test_listening_stats.py` (new) | Unit tests for every function, tz-aware timestamps included. |
| `tests/fixtures/heatmap_kpi_cases.json` (new) | One table of heatmap windows and the KPI text each must show; read by the Python tests and the browser harness, so the two implementations are held to the same numbers. |
| `tests/helpers.py` | Gains `load_kpi_cases`, `kpi_window`, `kpi_payload`, `expected_kpi_blocks`. |
| `scrobblescope/heatmap.py` | Publishes `statistics`; takes `to_date` through `utc_date`. |
| `static/js/heatmap.js` | `kpiModel` formats published statistics; `computeStreak`, `WINDOW_DAYS` and the best-day reduce go. |
| `scrobblescope/routes/album_flow.py` | Computes `play_stats` from the rows it renders. |
| `templates/results.html` | Renders `play_stats`; the Jinja `sum` goes. |
| `static/js/results.js` | Switches between two published figures; stops summing rows. |
| `config/docsync.toml` | Drops two declared sites that name deleted `heatmap.js` code (Task 3). |
| Gate fixtures `scripts/dev/_frontend_gate_heatmap_access.py`, `_frontend_gate_theme.py`, `_frontend_gate_pipeline.py`, `_frontend_gate_figures.py`, `scripts/dev/results_behavior_tests.py` | Seed the published figures the pages now require. |

---

### Task 1: Pin the heatmap KPIs and the Scrobbles figure (parity tests)

**Touches:** `tests/fixtures/heatmap_kpi_cases.json` (new), `tests/helpers.py`, `tests/frontend/test_heatmap_pure_functions.py`, `static/js/heatmap.js` (test seam only), `tests/test_routes.py`, `.claude/SESSION_CONTEXT.md` (Section 6, one sentence), `docs/agents/PLAYBOOK.md`
**After:** none

**Interfaces:**
- Consumes: the `js_page` fixture (`tests/frontend/conftest.py`), `_render_include_results`, `_render_results`, `_provider_row` in `tests/test_routes.py`, and `TEST_JOB_PARAMS` from `tests/helpers.py`.
- Produces: `heatmap_kpi_cases.json` and the four helpers, which Task 2 and Task 4 reuse; the test-seam hook `renderKpisInto(row, data)`, whose signature Task 4 keeps.

Why: Tasks 4 and 5 move the streak, best-day, average and Scrobbles rules out of the browser and Jinja. Nothing tests them today (the harness file says `computeStreak` is deferred to WP-6). These tests pin what a reader sees now, so the move is provably behaviour-neutral. They are intended-behaviour tests: each expected value is worked out by hand from the rule stated in the case name, not copied from a run.

- [ ] **Step 1: Write the case table**

Create `tests/fixtures/heatmap_kpi_cases.json`. Every case is a 365-day window ending 2026-03-10 (so it starts 2025-03-11); `plays` maps "days before the end" to a count, every other day is 0.

```json
[
  {
    "name": "streak_ends_today",
    "end": "2026-03-10",
    "plays": {"0": 1, "1": 3, "2": 1},
    "expected": {"scrobbles": "5", "daily_average": "0.0", "best_count": "3", "best_label": "MAR 9", "streak": "3"}
  },
  {
    "name": "streak_may_end_yesterday",
    "end": "2026-03-10",
    "plays": {"1": 2, "2": 1},
    "expected": {"scrobbles": "3", "daily_average": "0.0", "best_count": "2", "best_label": "MAR 9", "streak": "2"}
  },
  {
    "name": "a_gap_ends_the_streak",
    "end": "2026-03-10",
    "plays": {"0": 1, "2": 5},
    "expected": {"scrobbles": "6", "daily_average": "0.0", "best_count": "5", "best_label": "MAR 8", "streak": "1"}
  },
  {
    "name": "two_quiet_days_make_the_streak_zero",
    "end": "2026-03-10",
    "plays": {"5": 4},
    "expected": {"scrobbles": "4", "daily_average": "0.0", "best_count": "4", "best_label": "MAR 5", "streak": "0"}
  },
  {
    "name": "a_tie_for_best_day_goes_to_the_earlier_day",
    "end": "2026-03-10",
    "plays": {"10": 2, "3": 2},
    "expected": {"scrobbles": "4", "daily_average": "0.0", "best_count": "2", "best_label": "FEB 28", "streak": "0"}
  },
  {
    "name": "average_is_over_every_day_of_the_window",
    "end": "2026-03-10",
    "plays": {"0": 365, "1": 365},
    "expected": {"scrobbles": "730", "daily_average": "2.0", "best_count": "365", "best_label": "MAR 9", "streak": "2"}
  },
  {
    "name": "average_shows_one_decimal_and_thousands_separator",
    "end": "2026-03-10",
    "plays": {"0": 1000},
    "expected": {"scrobbles": "1,000", "daily_average": "2.7", "best_count": "1000", "best_label": "MAR 10", "streak": "1"}
  },
  {
    "name": "a_streak_stops_at_the_first_day_of_the_window",
    "end": "2026-03-10",
    "every_day": 1,
    "expected": {"scrobbles": "365", "daily_average": "1.0", "best_count": "1", "best_label": "MAR 11", "streak": "365"}
  }
]
```

Hand check of the two least obvious rows: 2026-03-10 minus 10 days is 2026-02-28 (2026 is not a leap year), which precedes 2026-03-07, so the tie goes to FEB 28; and the window starts 364 days before the end, 2025-03-11, the earliest of 365 equal days.

- [ ] **Step 2: Write the helpers**

Add to `tests/helpers.py` (add `import json`, `from datetime import date, timedelta` and `from pathlib import Path` at the top; the file starts with `import contextlib` and `from unittest.mock import AsyncMock, MagicMock, patch` today, and ruff's isort rule places the new imports):

```python
KPI_CASES_PATH = Path(__file__).parent / "fixtures" / "heatmap_kpi_cases.json"
KPI_WINDOW_DAYS = 365


def load_kpi_cases():
    """Return the heatmap KPI case table (``tests/fixtures/heatmap_kpi_cases.json``)."""
    return json.loads(KPI_CASES_PATH.read_text(encoding="utf-8"))


def kpi_window(case):
    """Expand *case* to ``(from_iso, to_iso, daily_counts)``.

    ``daily_counts`` is zero-filled and ascending, the shape the heatmap job
    publishes: one key per UTC day of a 365-day window ending on ``case["end"]``.
    """
    end = date.fromisoformat(case["end"])
    counts = {
        (end - timedelta(days=k)).isoformat(): 0
        for k in range(KPI_WINDOW_DAYS - 1, -1, -1)
    }
    if "every_day" in case:
        counts = {day: case["every_day"] for day in counts}
    for offset, count in case.get("plays", {}).items():
        counts[(end - timedelta(days=int(offset))).isoformat()] = count
    return next(iter(counts)), case["end"], counts


def kpi_payload(case):
    """Return the heatmap result dict a job would store for *case*, without statistics."""
    from_iso, to_iso, counts = kpi_window(case)
    return {
        "username": "kpi-user",
        "from_date": from_iso,
        "to_date": to_iso,
        "total_scrobbles": sum(counts.values()),
        "max_count": max(counts.values()),
        "daily_counts": counts,
    }


def expected_kpi_blocks(case):
    """Return the four KPI blocks the page must show for *case*, in order."""
    e = case["expected"]
    return [
        {"label": "SCROBBLES", "value": e["scrobbles"], "sub": ""},
        {"label": "DAILY AVERAGE", "value": e["daily_average"], "sub": ""},
        {"label": "BEST DAY", "value": e["best_count"], "sub": e["best_label"]},
        {"label": "CURRENT STREAK", "value": e["streak"], "sub": "DAYS"},
    ]
```

- [ ] **Step 3: Add the test-seam hook**

In `static/js/heatmap.js`, extend the `window.__scrobbleHeatmapTestHooks` object (the guarded block near the end of the file) with one entry. It mirrors the call `renderHeatmapDesktop` makes, so the harness exercises the real KPI path:

```js
      renderKpisInto: function (row, data) {
        kpiRow = row;
        renderKpis(data, data.daily_counts, parseLocalDate(data.to_date));
      },
```

Update the comment above the block: "These five functions" becomes "These functions". No behaviour changes on a real page: the hook exists only when `window.__scrobbleHeatmapTestMode` is set first.

- [ ] **Step 4: Write the browser test**

In `tests/frontend/test_heatmap_pure_functions.py`: replace the sentence in the module docstring that says `computeStreak` is out of scope with "The KPI blocks (streak, best day, daily average) joined with PR #6; their cases live in `tests/fixtures/heatmap_kpi_cases.json`, shared with the Python tests." Add `from tests.helpers import expected_kpi_blocks, kpi_payload, load_kpi_cases` and:

```python
KPI_CASES = load_kpi_cases()

RENDER_KPIS_JS = """(data) => {
    const row = document.createElement('div');
    window.__scrobbleHeatmapTestHooks.renderKpisInto(row, data);
    return Array.from(row.querySelectorAll('.heatmap-kpi')).map((item) => ({
        label: item.querySelector('.heatmap-kpi-label').textContent,
        value: item.querySelector('.heatmap-kpi-value').textContent,
        sub: (item.querySelector('.heatmap-kpi-sub') || { textContent: '' }).textContent,
    }));
}"""


@pytest.mark.parametrize("case", KPI_CASES, ids=lambda c: c["name"])
def test_kpi_blocks_show_what_the_window_holds(js_page, case):
    """The four KPI blocks state the window's total, daily average, best day
    and current streak, as the case name says they must.

    Mutation: make the streak start from the window's first day instead of
    its last (``computeStreak``'s ``toDate``), and every case with a streak
    other than 0 fails; make the best-day reduce use ``>`` instead of ``>=``
    and ``a_tie_for_best_day_goes_to_the_earlier_day``,
    ``average_is_over_every_day_of_the_window`` and
    ``a_streak_stops_at_the_first_day_of_the_window`` fail.
    """
    assert js_page.evaluate(RENDER_KPIS_JS, kpi_payload(case)) == expected_kpi_blocks(
        case
    )
```

- [ ] **Step 5: Write the route parity tests**

In `tests/test_routes.py`, after `test_results_include_run_marks_unmatched_rows_and_locks_listening_time`:

```python
def _scrobbles_figure(page):
    """The text of the Results page's Scrobbles stat."""
    return re.search(r'id="stat-scrobbles"[^>]*>([\d,]+)<', page).group(1)


def test_scrobbles_figure_is_the_plays_of_the_albums_the_page_lists(client):
    """
    GIVEN a run of three matched albums, and an include run that also lists
    two unmatched albums
    WHEN the Results page renders
    THEN Scrobbles states the plays of every album listed: 50 + 40 + 30, and
    with the unmatched rows 50 + 45 + 40 + 35 + 30.

    Mutation: sum only the matched rows on an include run and the second
    assertion reads 120; sum only the first row and both fail.
    """
    matched = _render_results(
        client,
        [
            {**_provider_row("spotify", 0), "play_count": 50},
            {**_provider_row("spotify", 1), "play_count": 40},
            {**_provider_row("spotify", 2), "play_count": 30},
        ],
    )
    assert _scrobbles_figure(matched) == "120"
    assert _scrobbles_figure(_render_include_results(client)) == "200"


def test_scrobbles_figure_leaves_out_albums_a_playtime_ranking_drops(client):
    """
    GIVEN a playtime-ranked run in which one album has no listening time
    WHEN the Results page renders
    THEN that album is not listed, and its plays are not in Scrobbles: the
    figure describes the rows on the page.

    Mutation: sum the stored rows before the playtime filter and the figure
    reads 90.
    """
    rows = [
        {**_provider_row("spotify", 0), "play_count": 50},
        {**_provider_row("spotify", 1), "play_count": 40, "play_time_seconds": 0},
    ]
    job_id = jobs.create({**TEST_JOB_PARAMS, "sort_mode": "playtime"})
    jobs.succeed(job_id, rows, "Done!")
    response = client.post("/results_complete", data={"job_id": job_id})
    assert response.status_code == 200
    assert _scrobbles_figure(response.data.decode("utf-8")) == "50"
```

- [ ] **Step 6: Run everything; it passes on the unchanged code**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest tests/frontend/test_heatmap_pure_functions.py tests/test_routes.py -k "kpi_blocks or scrobbles_figure" -q -p no:cacheprovider`
Expected: 8 + 2 passed. A failure here means the hand-worked expectation or today's code disagrees: stop and report it, do not edit the expectation to match.

- [ ] **Step 7: Mutation evidence**

In a scratch copy only: (a) in `computeStreak` replace `while (dailyCounts[isoDate(d)])` with `while (false)`; expect `streak_ends_today`, `streak_may_end_yesterday`, `a_gap_ends_the_streak`, `average_is_over_every_day_of_the_window`, `average_shows_one_decimal_and_thousands_separator` and `a_streak_stops_at_the_first_day_of_the_window` to FAIL. (b) In `renderKpis` change `dailyCounts[a] >= dailyCounts[b]` to `>`; expect `a_tie_for_best_day_goes_to_the_earlier_day`, `average_is_over_every_day_of_the_window` and `a_streak_stops_at_the_first_day_of_the_window` to FAIL. (c) In `results.html` change the `sum(attribute='play_count')` to `sum(attribute='play_time_seconds')`; expect both route tests to FAIL. Record the failing names; discard the copy.

- [ ] **Step 8: Docs, entry, gates, commit**

`.claude/SESSION_CONTEXT.md` Section 6 (Test structure): the sentence "`tests/fixtures/` holds provider response bodies transcribed from Last.fm's and Spotify's own docs (`lastfm_recenttracks_page.json`, `spotify_get_album.json`), read by `tests/test_provider_fixtures.py`'s shape tests." gains: "It also holds `heatmap_kpi_cases.json`, the table of heatmap windows and the KPI text each must show, read by `tests/test_listening_stats.py` and the browser harness."

Entry heading: `### <commit date, date +%F> - The heatmap KPIs and the Scrobbles figure are pinned before they move`. Body: scope, why (B-4; the next two commits move these rules), the case table, the mutation evidence, Validation `pytest -q` N. Commit: `test(stats): Pin the heatmap KPIs and Scrobbles figure`.

---

### Task 2: The listening statistics module

**Touches:** `scrobblescope/listening_stats.py` (new), `tests/test_listening_stats.py` (new), `.claude/SESSION_CONTEXT.md` (Sections 3 and 4), `docs/agents/PLAYBOOK.md`
**After:** Task 1 (the case table and helpers)

**Interfaces:**
- Consumes: `tests.helpers.load_kpi_cases`, `kpi_window`.
- Produces, for Tasks 4 and 5:
  - `utc_date(moment: datetime) -> date`
  - `current_streak(daily_counts: Mapping[str, int], today: date) -> int`
  - `best_day(daily_counts: Mapping[str, int]) -> tuple[date | None, int]`
  - `daily_average(daily_counts: Mapping[str, int]) -> float`
  - `heatmap_statistics(daily_counts: Mapping[str, int], today: date) -> dict`
  - `album_play_statistics(rows: Iterable[Mapping]) -> dict`

  Both aggregate functions return `{name: {"value": ..., "population": "<sentence>"}}`, JSON-serialisable as published.

Why: B-4 wants the rules in one place with ordinary pytest coverage. UTC is by construction: the module imports no clock and no timezone database, `today` is passed in, day keys are ISO dates the pipeline already attributed in UTC, and the one function that takes a moment (`utc_date`) refuses a naive datetime.

- [ ] **Step 1: Write the failing tests first**

Create `tests/test_listening_stats.py`:

```python
"""Listening statistics: every figure, its rule and its stated population."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from scrobblescope.listening_stats import (
    album_play_statistics,
    best_day,
    current_streak,
    daily_average,
    heatmap_statistics,
    utc_date,
)
from tests.helpers import kpi_window, load_kpi_cases

NEW_YORK = timezone(timedelta(hours=-5))
TOKYO = timezone(timedelta(hours=9))


def _window(first, days, plays=None):
    """A zero-filled window of *days* days from *first* with *plays* by ISO date."""
    counts = {(first + timedelta(days=n)).isoformat(): 0 for n in range(days)}
    counts.update(plays or {})
    return counts


class TestUtcDate:
    def test_a_late_evening_in_new_york_is_the_next_utc_day(self):
        moment = datetime(2026, 3, 1, 23, 30, tzinfo=NEW_YORK)
        assert utc_date(moment) == date(2026, 3, 2)

    def test_an_early_morning_in_tokyo_is_the_previous_utc_day(self):
        moment = datetime(2026, 3, 2, 6, 0, tzinfo=TOKYO)
        assert utc_date(moment) == date(2026, 3, 1)

    def test_a_naive_moment_is_refused(self):
        """A naive datetime has no zone to convert from, so any answer is a guess."""
        with pytest.raises(ValueError, match="timezone"):
            utc_date(datetime(2026, 3, 1, 23, 30))


class TestCurrentStreak:
    def test_utc_midnight_decides_which_day_a_play_belongs_to(self):
        """A play at 23:30 in New York on 1 March is 2 March in UTC, so 2 March
        has a play and the streak is 3. Read in local time the play lands on
        1 March, 2 March is quiet, and the streak is 2."""
        counts = _window(date(2026, 2, 25), 6)
        for moment in (
            datetime(2026, 2, 28, 12, 0, tzinfo=UTC),
            datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            datetime(2026, 3, 1, 23, 30, tzinfo=NEW_YORK),
        ):
            counts[utc_date(moment).isoformat()] += 1
        assert current_streak(counts, date(2026, 3, 2)) == 3

    def test_a_streak_may_end_yesterday(self):
        counts = _window(date(2026, 3, 1), 10, {"2026-03-08": 1, "2026-03-09": 2})
        assert current_streak(counts, date(2026, 3, 10)) == 2

    def test_two_quiet_days_end_the_streak(self):
        # Today 03-10 and 03-09 are quiet, so the streak is 0. The run on
        # 03-07/03-08 is two days old: a count that began at 03-08 would say 2.
        counts = _window(date(2026, 3, 1), 10, {"2026-03-07": 4, "2026-03-08": 2})
        assert current_streak(counts, date(2026, 3, 10)) == 0

    def test_a_single_day_streak(self):
        counts = _window(date(2026, 3, 1), 10, {"2026-03-10": 1})
        assert current_streak(counts, date(2026, 3, 10)) == 1

    def test_counting_stops_at_the_first_day_of_the_window(self):
        counts = {d: 1 for d in _window(date(2026, 3, 1), 10)}
        assert current_streak(counts, date(2026, 3, 10)) == 10

    def test_an_empty_window_has_no_streak(self):
        assert current_streak({}, date(2026, 3, 10)) == 0


class TestBestDay:
    def test_the_busiest_day_and_its_count(self):
        # Busiest is 03-06 (7 plays); the first day with a play is 03-04 (3) and
        # the last is 03-08 (2), so "first" and "last" both give another answer.
        counts = _window(
            date(2026, 3, 1),
            10,
            {"2026-03-04": 3, "2026-03-06": 7, "2026-03-08": 2},
        )
        assert best_day(counts) == (date(2026, 3, 6), 7)

    def test_a_tie_goes_to_the_earlier_day(self):
        counts = _window(date(2026, 3, 1), 10, {"2026-03-02": 4, "2026-03-09": 4})
        assert best_day(counts) == (date(2026, 3, 2), 4)

    def test_a_window_with_no_plays_has_no_best_day(self):
        """Not 'the first day with 0 plays': nothing was played, so no day is best."""
        assert best_day(_window(date(2026, 3, 1), 10)) == (None, 0)

    def test_an_empty_mapping_has_no_best_day(self):
        assert best_day({}) == (None, 0)


class TestDailyAverage:
    def test_quiet_days_count_as_zero(self):
        counts = _window(date(2026, 3, 1), 10, {"2026-03-02": 30})
        assert daily_average(counts) == 3.0

    def test_the_average_is_not_rounded(self):
        counts = _window(date(2026, 3, 1), 3, {"2026-03-01": 1})
        assert daily_average(counts) == pytest.approx(1 / 3)

    def test_an_empty_window_averages_zero_not_an_error(self):
        assert daily_average({}) == 0.0


@pytest.mark.parametrize("case", load_kpi_cases(), ids=lambda c: c["name"])
def test_the_published_figures_are_the_ones_the_pinned_kpis_show(case):
    """Same table the browser harness checks, so the Python rules agree with
    what readers saw before the move.

    Mutation: anchor the streak on the window's first day, or break ties
    toward the later day, and the matching cases fail.
    """
    _, to_iso, counts = kpi_window(case)
    stats = heatmap_statistics(counts, date.fromisoformat(to_iso))
    expected = case["expected"]
    best = stats["best_day"]["value"]
    best_date = date.fromisoformat(best["date"])

    assert f"{stats['total_plays']['value']:,}" == expected["scrobbles"]
    assert f"{stats['daily_average']['value']:.1f}" == expected["daily_average"]
    assert str(best["count"]) == expected["best_count"]
    assert f"{best_date:%b}".upper() + f" {best_date.day}" == expected["best_label"]
    assert str(stats["current_streak"]["value"]) == expected["streak"]


class TestHeatmapStatistics:
    def test_every_figure_states_its_population(self):
        stats = heatmap_statistics(_window(date(2026, 3, 1), 10), date(2026, 3, 10))
        assert set(stats) == {
            "total_plays",
            "daily_average",
            "best_day",
            "current_streak",
        }
        for name, fact in stats.items():
            assert fact["population"].strip(), f"{name} states no population"
        assert len({fact["population"] for fact in stats.values()}) == 4

    def test_a_window_with_no_plays_publishes_null_for_best_day(self):
        stats = heatmap_statistics(_window(date(2026, 3, 1), 10), date(2026, 3, 10))
        assert stats["best_day"]["value"] == {"date": None, "count": 0}
        assert stats["current_streak"]["value"] == 0


class TestAlbumPlayStatistics:
    ROWS = [
        {"play_count": 50},
        {"play_count": 45, "unmatched_reason": "no_spotify_match"},
        {"play_count": 40},
        {"play_count": 35, "unmatched_reason": "provider_unavailable"},
    ]

    def test_listed_counts_every_row_and_matched_leaves_out_unmatched(self):
        stats = album_play_statistics(self.ROWS)
        assert stats["plays_listed"]["value"] == 170
        assert stats["plays_matched"]["value"] == 90

    def test_without_unmatched_rows_the_two_figures_agree(self):
        stats = album_play_statistics([{"play_count": 50}, {"play_count": 40}])
        assert stats["plays_listed"]["value"] == stats["plays_matched"]["value"] == 90

    def test_no_rows_is_zero_not_an_error(self):
        stats = album_play_statistics([])
        assert stats["plays_listed"]["value"] == 0
        assert stats["plays_matched"]["value"] == 0

    def test_a_missing_or_null_play_count_is_zero(self):
        stats = album_play_statistics([{"play_count": None}, {}, {"play_count": 4}])
        assert stats["plays_listed"]["value"] == 4

    def test_each_figure_says_what_it_leaves_out(self):
        stats = album_play_statistics(self.ROWS)
        assert "unmatched" in stats["plays_matched"]["population"]
        assert stats["plays_listed"]["population"] != stats["plays_matched"]["population"]
```

- [ ] **Step 2: Run them; they fail on the missing module**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest tests/test_listening_stats.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'scrobblescope.listening_stats'`.

- [ ] **Step 3: Write the module**

Create `scrobblescope/listening_stats.py`:

```python
"""Listening statistics -- the rules behind the figures a page states.

Pure functions, standard library only: no clock, no timezone database, no I/O.
Two things keep every figure in UTC without a runtime check:

* Day keys are ISO dates (``"2026-03-01"``) that the pipeline already
  attributed to a UTC day when it counted plays (``plays.aggregate_daily_counts``
  reads each play's date from its UTC timestamp, and ``Play`` refuses a
  timestamp that is not UTC). This module never re-reads a time of day.
* The reference day a streak counts back from is passed in. It is the window's
  last day, which the pipeline took from a UTC clock, so a server in another
  timezone cannot move it.

The one function that accepts a moment, ``utc_date``, converts it to UTC and
refuses a naive datetime.

Each ``*_statistics`` function returns ``{name: {"value": ..., "population":
"<sentence>"}}``. The population is the answer to "what is this figure a
figure of?" and travels with the value, so a page, a CSV column or a test can
quote it and the two cannot drift apart. Dependency chain: this module is a
leaf (standard library only); ``heatmap`` and ``routes.album_flow`` import it.
"""

from __future__ import annotations

from datetime import UTC, date, timedelta


def utc_date(moment):
    """Return the UTC calendar date of *moment*.

    Args:
        moment: A timezone-aware ``datetime`` in any zone.

    Raises:
        ValueError: *moment* is naive. Reading a naive time as UTC would be a
            guess about the server's zone, which is the bug this module exists
            to rule out.
    """
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("utc_date needs a timezone-aware datetime")
    return moment.astimezone(UTC).date()


def _plays_on(daily_counts, day):
    """Return the plays recorded for *day*, 0 when the window holds no such day."""
    return daily_counts.get(day.isoformat(), 0)


def current_streak(daily_counts, today):
    """Count the consecutive days with a play, ending *today* or the day before.

    If *today* has no play yet the streak may still end yesterday: a listener
    who opens the page in the morning, before playing anything, keeps the
    streak they had. Counting stops at the first quiet day, and a day outside
    the window is a quiet day, so a streak never reaches past the window's
    first day.

    Args:
        daily_counts: ``{"YYYY-MM-DD": plays}``, UTC days.
        today: The window's last day (a ``date``, not a ``datetime``).
    """
    day = today
    if not _plays_on(daily_counts, day):
        day -= timedelta(days=1)
    streak = 0
    while _plays_on(daily_counts, day):
        streak += 1
        day -= timedelta(days=1)
    return streak


def best_day(daily_counts):
    """Return ``(day, plays)`` for the busiest day, the earliest on a tie.

    Returns ``(None, 0)`` when no day has a play: with nothing played, no day
    is the best one.
    """
    best, best_count = None, 0
    for key in sorted(daily_counts):
        if daily_counts[key] > best_count:
            best, best_count = key, daily_counts[key]
    return (date.fromisoformat(best) if best else None), best_count


def daily_average(daily_counts):
    """Return plays per day over every day of the window, quiet days included.

    The result is not rounded: how many decimals to show is the renderer's
    business. An empty window averages 0.0.
    """
    if not daily_counts:
        return 0.0
    return sum(daily_counts.values()) / len(daily_counts)


def heatmap_statistics(daily_counts, today):
    """Return the heatmap's published figures, each with its population.

    Args:
        daily_counts: The zero-filled ``{"YYYY-MM-DD": plays}`` window.
        today: The window's last UTC day.
    """
    day, count = best_day(daily_counts)
    return {
        "total_plays": {
            "value": sum(daily_counts.values()),
            "population": "all plays inside the window",
        },
        "daily_average": {
            "value": daily_average(daily_counts),
            "population": (
                "all plays inside the window, over every UTC day of the window "
                "including the days with none"
            ),
        },
        "best_day": {
            "value": {"date": day.isoformat() if day else None, "count": count},
            "population": (
                "the UTC day with the most plays inside the window; "
                "the earliest day wins a tie"
            ),
        },
        "current_streak": {
            "value": current_streak(daily_counts, today),
            "population": (
                "consecutive UTC days with a play, ending on the window's last "
                "day or the day before it, counted back no further than the "
                "window's first day"
            ),
        },
    }


def _row_plays(row):
    """Return a result row's play count as an int (missing or null is 0)."""
    return int(row.get("play_count") or 0)


def _is_unmatched(row):
    """Return True for a row listed through include-unmatched, which no provider matched."""
    return bool(row.get("unmatched_reason"))


def album_play_statistics(rows):
    """Return the Results page's play figures, each with its population.

    Args:
        rows: The result rows the page is about to list, after every filter the
            page applies (release window, limit, playtime ranking).

    ``plays_listed`` counts every row; ``plays_matched`` leaves out rows listed
    through the include-unmatched control. On a run without that control the
    two are equal.
    """
    rows = list(rows)
    return {
        "plays_listed": {
            "value": sum(_row_plays(row) for row in rows),
            "population": (
                "plays of every album row the page lists, including albums "
                "listed through include-unmatched"
            ),
        },
        "plays_matched": {
            "value": sum(_row_plays(row) for row in rows if not _is_unmatched(row)),
            "population": (
                "plays of the album rows a provider matched; albums listed "
                "through include-unmatched (unmatched) are left out"
            ),
        },
    }
```

Import only what is used: the module above needs `from datetime import UTC, date, timedelta` and no `typing` or `collections.abc` import (ruff fails an unused import). The repo writes `UTC`, never `timezone.utc` (ruff `UP017`, `target-version = "py313"`); `tests/test_listening_stats.py` keeps `timezone` only for the fixed-offset `NEW_YORK` and `TOKYO`.

- [ ] **Step 4: Run the tests; they pass**

Run: the Step 2 command. Expected: all pass (about 30).

- [ ] **Step 5: Mutation evidence**

Plant each defect in a scratch copy, run `tests/test_listening_stats.py`, record the failing names, discard. Every new test appears below.

| Test | Planted defect | Fails |
|---|---|---|
| `test_a_late_evening_in_new_york_is_the_next_utc_day`, `test_an_early_morning_in_tokyo_is_the_previous_utc_day`, `test_utc_midnight_decides_which_day_a_play_belongs_to` | `utc_date` returns `moment.date()` (the local calendar day) | all three |
| `test_a_naive_moment_is_refused` | `utc_date` accepts a naive datetime (drop the `tzinfo` check) | itself |
| `test_a_streak_may_end_yesterday` | `current_streak` drops the "start from yesterday" step | itself and case `streak_may_end_yesterday` |
| `test_two_quiet_days_end_the_streak` | `current_streak` starts from `today - 2` when today is quiet (one quiet day forgiven too many) | itself: asserts `== 0`, gets 2 (03-08 and 03-07 both have plays; correct code stops at the quiet 03-09) |
| `test_a_single_day_streak` | `current_streak` returns `streak + 1` | itself |
| `test_counting_stops_at_the_first_day_of_the_window` | `current_streak` reads a missing day as a play (`.get(key, 1)`); the mutated loop is capped at 400 iterations so it ends | itself |
| `test_an_empty_window_has_no_streak` | `current_streak` indexes `daily_counts[key]` instead of `.get` | itself (KeyError) |
| `test_the_busiest_day_and_its_count` | `best_day` returns the last day with a play | itself: asserts `(03-06, 7)`, gets `(03-08, 2)` |
| `test_a_tie_goes_to_the_earlier_day` | `best_day` uses `>=` | itself: asserts `(03-02, 4)`, gets `(03-09, 4)` (sorted ascending, `>=` lets the later day replace the earlier); also the tie case |
| `test_a_window_with_no_plays_has_no_best_day` | `best_day` returns the first key with count 0 | itself |
| `test_an_empty_mapping_has_no_best_day` | `best_day` takes `sorted(daily_counts)[0]` unguarded | itself (IndexError) |
| `test_quiet_days_count_as_zero` | `daily_average` divides by the number of days with plays | itself |
| `test_the_average_is_not_rounded` | `daily_average` returns `round(..., 1)` | itself |
| `test_an_empty_window_averages_zero_not_an_error` | `daily_average` drops the empty guard | itself (ZeroDivisionError) |
| `test_the_published_figures_are_the_ones_the_pinned_kpis_show` (8 cases) | streak anchored on the window's first day; ties toward the later day | the matching cases |
| `test_every_figure_states_its_population` | one population left blank, or two facts sharing a sentence | itself |
| `test_a_window_with_no_plays_publishes_null_for_best_day` | `heatmap_statistics` publishes the string `"None"` for the date | itself |
| `test_listed_counts_every_row_and_matched_leaves_out_unmatched` | `plays_matched` ignores `_is_unmatched` | itself |
| `test_without_unmatched_rows_the_two_figures_agree` | `plays_matched` is `plays_listed` minus a fixed count of 1 | itself |
| `test_no_rows_is_zero_not_an_error` | `album_play_statistics` reads `rows[0]` | itself |
| `test_a_missing_or_null_play_count_is_zero` | `_row_plays` uses `row["play_count"]` | itself |
| `test_each_figure_says_what_it_leaves_out` | the matched population loses the word "unmatched", or both sentences are identical | itself |

- [ ] **Step 6: Docs in the same commit**

`.claude/SESSION_CONTEXT.md`, two edits and no others:
- Section 3 (Project structure), in the `scrobblescope/` tree directly after the line `  spotlight.py              # pure artist aggregation and stable sample selection`, insert `  listening_stats.py        # pure listening statistics (streak, best day, daily average, plays listed vs matched), each with its population stated`.
- Section 4 (Module dependency graph), directly after the line `spotlight.py     <- utils`, insert `listening_stats.py <- (leaf; standard library only)`.

Section 5 is not edited. Run `doc_state_sync.py --check`; expected exit 0.

- [ ] **Step 7: Section 4 entry, gates, commit**

Entry heading: `### <commit date, date +%F> - Listening statistics have one module`. Commit: `feat(stats): Add the listening statistics module`.

---

### Task 3: Retire the two docsync sites that name `heatmap.js`'s window code

**Touches:** `config/docsync.toml`, `docs/agents/PLAYBOOK.md`
**After:** none (any time before Task 4)

**Interfaces:** none.

Why: `config/docsync.toml` declares the 365-day window and ties it to a `WINDOW_DAYS = (\d+)` site and a `whole (\d+)-day window` comment site in `static/js/heatmap.js`. Task 4 deletes both pieces of text (the browser stops dividing by a window length; the Python module divides by the window's own days). A declaration whose pattern no longer matches fails DOC009, so the declarations go first, in their own commit, through the documented escape: a staged `config/docsync.toml` change other than the `[test_count]` pin is control-plane (AGENTS.md "Doc Sync Rules"). The remaining sites still guard the fetch range (`HEATMAP_WINDOW_DAYS`), the exported caption (`LAST (\d+) DAYS`) and all copy.

- [ ] **Step 1: Remove the two sites**

In `config/docsync.toml`, delete the `[[value.sites]]` table with `pattern = 'WINDOW_DAYS = (\d+)'` and the one with `pattern = 'whole (\d+)-day window'` (both `file = "static/js/heatmap.js"`). Keep the `LAST (\d+) DAYS` site and its comment. In the comment above the declaration (the one beginning with the `static/js/loading.js is deliberately absent` note) nothing needs changing.

- [ ] **Step 2: Check**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/doc_state_sync.py --check`
Expected: exit 0 (the code still has the constants, now unguarded for one commit; the declaration lists fewer sites).

- [ ] **Step 3: Section 4 entry, gates, commit through the named escape**

1. Entry heading `### <commit date, date +%F> - The window declaration drops two heatmap.js sites`; body: which two sites, why (Task 4 deletes the text they match, because the average now divides by the zero-filled window in Python), that the Python constant and the exported caption stay guarded, and why the escape was used.
2. `pytest -q` (N unchanged), bare `--fix`, stage by name, `pre-commit run --all-files` (the docsync hook reports the control-plane refusal; every other hook must pass).
3. `SKIP=doc-state-sync-check git commit` with subject `chore(docsync): Drop the heatmap.js window-length sites`.
4. Immediately run `... scripts/doc_state_sync.py --check`; expected exit 0. Quote it in the report. Never `--no-verify`.

---

### Task 4: The heatmap publishes its statistics; the browser renders them

**Touches:** `scrobblescope/heatmap.py`, `static/js/heatmap.js`, `tests/test_heatmap.py`, `tests/frontend/test_heatmap_pure_functions.py`, `scripts/dev/_frontend_gate_heatmap_access.py`, `scripts/dev/_frontend_gate_theme.py`, `scripts/dev/_frontend_gate_pipeline.py`, `scripts/dev/_frontend_gate_figures.py`, `docs/architecture/runtime-system.md`, `docs/architecture/heatmap-sequence.md`, `.claude/SESSION_CONTEXT.md`, `docs/agents/PLAYBOOK.md`
**After:** Task 1, Task 2, Task 3

**Interfaces:**
- Consumes: `listening_stats.heatmap_statistics`, `utc_date`; the hook `renderKpisInto(row, data)` and the case table from Task 1.
- Produces: the heatmap result's new key `statistics` (`total_plays`, `daily_average`, `best_day`, `current_streak`, each `{"value", "population"}`); JS `kpiModel(statistics)`.

Why: this is the B-4 move for the heatmap. `computeStreak`, `WINDOW_DAYS` and the best-day reduce are the browser carrying a domain rule. Existing keys (`total_scrobbles`, `max_count`, `daily_counts`) stay: the grid, its colour scale and the SVG's `aria-label` read them.

- [ ] **Step 1: Failing tests for the published statistics**

In `tests/test_heatmap.py`, inside the class that holds `test_happy_path_stores_correct_result_dict`, extend that test's assertions (name this edit in the commit body) after the `max_count` line:

```python
        # Python publishes the KPI figures; the browser renders them.
        assert stored_result["statistics"]["total_plays"]["value"] == 3
        assert stored_result["statistics"]["best_day"]["value"] == {
            "date": yesterday.isoformat(),
            "count": 2,
        }
        assert stored_result["statistics"]["current_streak"]["value"] == 2
        assert stored_result["statistics"]["daily_average"]["value"] == pytest.approx(
            3 / 365
        )
```

and add, beside `test_success_is_readable_through_repository_at_100_percent`:

```python
    @pytest.mark.asyncio
    async def test_statistics_reach_the_browser_through_heatmap_data(self, client):
        """
        GIVEN a heatmap job run through the real pipeline: 2 plays yesterday
        and 1 today, stored by ``_fetch_and_process_heatmap``
        WHEN the browser asks /heatmap_data
        THEN the response carries the published statistics with their
        populations, so the whole path (task, store, route) is covered.

        Worked by hand: total 3, best day yesterday with 2, streak 2
        (today and yesterday both have plays).

        Mutation: delete ``"statistics": statistics,`` from the ``jobs.succeed``
        payload in heatmap.py and ``body["statistics"]`` raises KeyError; build
        the /heatmap_data response from named keys that omit ``statistics`` and
        the same line fails.
        """
        today = datetime.now(UTC).date()
        yesterday = today - timedelta(days=1)
        job_id = jobs.create({"username": "stats-user", "mode": "heatmap"})
        try:
            with (
                patch("scrobblescope.heatmap.cleanup_expired_cache"),
                patch("scrobblescope.jobs.expire_stale"),
                patch(
                    "scrobblescope.heatmap.fetch_scrobbles",
                    new_callable=AsyncMock,
                    return_value=_fetch(
                        [_play(yesterday), _play(yesterday), _play(today)]
                    ),
                ),
            ):
                await _fetch_and_process_heatmap(job_id, "stats-user")
            body = client.get(f"/heatmap_data?job_id={job_id}").get_json()
        finally:
            jobs.delete(job_id)

        assert body["ready"] is True
        assert body["statistics"]["total_plays"]["value"] == 3
        assert body["statistics"]["current_streak"]["value"] == 2
        assert body["statistics"]["best_day"]["value"]["count"] == 2
        assert all(fact["population"] for fact in body["statistics"].values())
```

`pytest`, `AsyncMock`, `patch`, `jobs`, `UTC`, `_play` and `_fetch` are already imported or defined in `tests/test_heatmap.py` (the neighbouring tests use them; `timezone` is not imported there and the repo writes `UTC`, so use `UTC`), so do not add `import pytest` again (ruff F811). `client` is the fixture in `tests/conftest.py`. This test runs the real task and so depends on the `fetch_scrobbles` patch and the `_fetch`/`_play` helpers, like the happy-path test (PR #4 table).

Run: `... -m pytest tests/test_heatmap.py -k "happy_path or statistics_reach" -q -p no:cacheprovider`. Expected: the happy-path test FAILS with `KeyError: 'statistics'`; `test_statistics_reach_the_browser_through_heatmap_data` FAILS the same way (`KeyError: 'statistics'` on `body["statistics"]`), because the task does not publish the key yet.

- [ ] **Step 2: Publish the statistics**

In `scrobblescope/heatmap.py`:
- Add `from scrobblescope.listening_stats import heatmap_statistics, utc_date` (alphabetical among the package imports).
- In `_fetch_and_process_heatmap` replace `to_date = now.date()` with `to_date = utc_date(now)`, and keep the comment that all datetimes are UTC.
- After `active_days = ...` add `statistics = heatmap_statistics(daily_counts, to_date)`.
- In the `jobs.succeed` payload add `"statistics": statistics,` after `"daily_counts": daily_counts,`.
- Module docstring dependency line: `heatmap <- errors, jobs, lastfm, listening_stats, plays, utils, worker`.
- The comment above `HEATMAP_WINDOW_DAYS` ends: "The renderer divides the total by it for the daily average, and six lines of copy say the number out loud, so a change here that does not reach them fetches one range while displaying and averaging another." Replace that one sentence with: "The statistics module averages over every day of the zero-filled window this constant sizes, and six lines of copy say the number out loud, so a change here that does not reach them fetches one range while displaying another." Keep every other sentence of the comment (it has no `last 365 days` wording; that is in the module docstring, which `config/docsync.toml` matches and which does not change).

Run the Step 1 command. Expected: PASS.

- [ ] **Step 3: Failing browser tests for rendering published values**

In `tests/frontend/test_heatmap_pure_functions.py` add `from datetime import date` and `from scrobblescope.listening_stats import heatmap_statistics` at the top with the other imports, then replace Task 1's `test_kpi_blocks_show_what_the_window_holds` body so the payload carries the published statistics (name this edit in the commit body):

```python
def _published(case):
    payload = kpi_payload(case)
    payload["statistics"] = heatmap_statistics(
        payload["daily_counts"], date.fromisoformat(payload["to_date"])
    )
    return payload


@pytest.mark.parametrize("case", KPI_CASES, ids=lambda c: c["name"])
def test_kpi_blocks_show_what_the_window_holds(js_page, case):
    """(docstring unchanged) The blocks read the same after the rules moved
    to Python as they did when the browser computed them."""
    assert js_page.evaluate(RENDER_KPIS_JS, _published(case)) == expected_kpi_blocks(
        case
    )


def test_kpi_blocks_render_the_published_figures_and_compute_nothing(js_page):
    """
    GIVEN a payload whose statistics disagree with its own daily counts
    WHEN the KPI row renders
    THEN it shows the published figures, not figures worked out from the
    counts: the page states what the server decided.

    Mutation: bring back a browser-side streak or best-day computation and
    the row shows 0 and 1 instead of 7 and 9.
    """
    published = {
        "total_plays": {"value": 14, "population": "p"},
        "daily_average": {"value": 0.04, "population": "p"},
        "best_day": {"value": {"date": "2026-03-05", "count": 9}, "population": "p"},
        "current_streak": {"value": 7, "population": "p"},
    }
    data = {
        "from_date": "2026-03-01",
        "to_date": "2026-03-10",
        "daily_counts": {"2026-03-10": 1},
        "statistics": published,
    }
    assert js_page.evaluate(RENDER_KPIS_JS, data) == [
        {"label": "SCROBBLES", "value": "14", "sub": ""},
        {"label": "DAILY AVERAGE", "value": "0.0", "sub": ""},
        {"label": "BEST DAY", "value": "9", "sub": "MAR 5"},
        {"label": "CURRENT STREAK", "value": "7", "sub": "DAYS"},
    ]


def test_a_window_with_no_best_day_shows_no_date(js_page):
    """A window with no plays has no best day: the block shows 0 and no date.

    Mutation: format ``best.date`` without the null guard and the block shows
    'NaN' or the render throws instead of an empty label.
    """
    published = {
        "total_plays": {"value": 0, "population": "p"},
        "daily_average": {"value": 0, "population": "p"},
        "best_day": {"value": {"date": None, "count": 0}, "population": "p"},
        "current_streak": {"value": 0, "population": "p"},
    }
    data = {"from_date": "2026-03-01", "to_date": "2026-03-10", "statistics": published}
    blocks = js_page.evaluate(RENDER_KPIS_JS, data)
    assert blocks[2] == {"label": "BEST DAY", "value": "0", "sub": ""}
```

Run the harness file. Expected: the two new tests and the 8 table cases still pass or fail as follows: the table cases PASS (the old JS ignores `statistics`), `test_kpi_blocks_render_the_published_figures_and_compute_nothing` FAILS (old JS computes `0` and `1`), `test_a_window_with_no_best_day_shows_no_date` FAILS (it throws on the missing `daily_counts`).

- [ ] **Step 4: Render only**

In `static/js/heatmap.js`:
1. Delete `const WINDOW_DAYS = 365;` and the `//: The heatmap window...` comment above it.
2. Delete `computeStreak` entirely.
3. Replace `renderKpis` with the pair below, keeping the existing comment about one decimal (the `Math.round showed 0` reasoning) above the `toLocaleString` call:

```js
  /**
   * Turn the published statistics into the four KPI blocks, in order.
   *
   * Pure formatting. The server decided every figure and which population it
   * covers (scrobblescope/listening_stats.py); nothing here recomputes a streak,
   * a best day or an average. Formatting stays in the browser because it
   * follows the reader's locale.
   */
  function kpiModel(statistics) {
    var best = statistics.best_day.value;
    // One decimal, always. Math.round showed 0 for anyone under 183
    // scrobbles in the window -- a positive total reported as no listening
    // at all, which is the one number this KPI must never say. It also read
    // 49.9 as 50. A fixed decimal keeps the column aligned.
    var dailyAverage = Number(statistics.daily_average.value || 0)
      .toLocaleString(undefined, {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      });
    return [
      { label: 'SCROBBLES',
        value: Number(statistics.total_plays.value || 0).toLocaleString(),
        sub: '' },
      { label: 'DAILY AVERAGE', value: dailyAverage, sub: '' },
      { label: 'BEST DAY',
        value: String(best.count),
        sub: best.date ? formatMonthDayUpper(parseLocalDate(best.date)) : '' },
      { label: 'CURRENT STREAK',
        value: String(statistics.current_streak.value),
        sub: 'DAYS' },
    ];
  }

  function renderKpis(data) {
    clearChildren(kpiRow);
    // Every result the server stores carries statistics. A payload without
    // them is a server bug: say so in the console and leave the row empty,
    // rather than computing a figure here.
    if (!data.statistics) {
      console.error('heatmap result carries no statistics');
      return;
    }
    kpiModel(data.statistics).forEach(function (kpi) {
      appendKpi(kpi.label, kpi.value, kpi.sub);
    });
  }
```

4. Change both call sites, `renderKpis(data, dailyCounts, toDate);` in `renderHeatmapDesktop` and `renderHeatmapMobile`, to `renderKpis(data);`.
5. Change the Task 1 hook to `renderKpisInto: function (row, data) { kpiRow = row; renderKpis(data); },`.
6. Fix the comments the change makes false. The test-seam comment above `window.__scrobbleHeatmapTestHooks` says the functions are "side effect free, so the seam is safe to expose"; add "except `renderKpisInto`, which points `kpiRow` at the harness's element and exists only under the test flag". `git grep -n "streak" static/js/heatmap.js` then returns the `CURRENT STREAK` label, the `current_streak` key and the `kpiModel` docstring, and nothing that computes one.

`parseLocalDate` stays: it still turns an ISO date into a Date for display. The tooltip and grid code keep reading `daily_counts` and `max_count`.

- [ ] **Step 5: Seed statistics in the gate fixtures**

Every hand-seeded heatmap payload in the gate now needs the key the page renders. `git grep -n '"daily_counts"' scripts tests` at eb0db9e finds these eight payloads in the gate; re-run it and reconcile before editing:
- `scripts/dev/_frontend_gate_heatmap_access.py`: four `jobs.succeed(...)` payloads, including `_seed_year_job` and the one in `check_heatmap_focus_survives_breakpoint`.
- `scripts/dev/_frontend_gate_theme.py`: two payloads (`total_scrobbles` 3 and 4).
- `scripts/dev/_frontend_gate_pipeline.py`: one payload (the 1920x945 check; it also lacks `max_count`, which stays as it is).
- `scripts/dev/_frontend_gate_figures.py`: one payload, held as the module constant `_HEATMAP_RESULT` (seeded by `jobs.succeed(heatmap_job, _HEATMAP_RESULT, "Done")`; its check waits for `.heatmap-kpi-value`, so a payload without `statistics` renders an empty KPI row and fails the gate). Bind its counts to a module constant first (`_HEATMAP_COUNTS = {"2025-01-01": 4, "2025-01-02": 0}`), use it for `"daily_counts"`, and add `"statistics": heatmap_statistics(_HEATMAP_COUNTS, date.fromisoformat("2025-01-05")),` (the constant's own `to_date`). `tests/scripts/dev/test_frontend_gate_figures.py` patches `jobs` and reads no payload key, so it needs no change.

Tests that seed `daily_counts` outside the gate (`tests/test_heatmap.py`, the `heatmap_data` tests in `tests/test_routes.py`, `tests/frontend/`) render no KPI row and need no change. In each of the eight, add:

```python
            "statistics": heatmap_statistics(counts, date.fromisoformat(to_date)),
```

using each fixture's own counts dict and window end (`counts`/`daily_counts` and `to_date` under whatever local names the fixture has), with `from datetime import date` and `from scrobblescope.listening_stats import heatmap_statistics` at each module's top. In `_frontend_gate_heatmap_access.py` also fix the comment "(WINDOW_DAYS in heatmap.js)" to "(HEATMAP_WINDOW_DAYS in heatmap.py)". Where a fixture builds its counts inline in the dict literal, bind the dict to a local first.

- [ ] **Step 6: Run the tests and the gate**

Run: the Step 1 command and the harness file; expected all PASS.
Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/frontend_gate.py`
Expected: last line `[frontend_gate] N checks passed ...`, no heatmap check failing. Then `... scripts/doc_state_sync.py --check`: expected exit 0 (DOC009 holds because Task 3 removed the two sites).

- [ ] **Step 7: Mutation evidence**

Scratch copy only: (a) make `current_streak` start from `today - 1` unconditionally: `test_statistics_reach_the_browser_through_heatmap_data` FAILS (asserts streak 2, gets 1: today has a play, the mutant skips it) and so do the `streak_ends_today` cases (expect 3, get 2). (b) Restore a three-line browser streak in `kpiModel`: `test_kpi_blocks_render_the_published_figures_and_compute_nothing` FAILS. (c) Delete `"statistics": statistics,` from the `jobs.succeed` payload in heatmap.py: the happy-path test FAILS (`KeyError: 'statistics'` on `stored_result["statistics"]`) and `test_statistics_reach_the_browser_through_heatmap_data` FAILS (`KeyError: 'statistics'` on `body["statistics"]`, because it runs the real task and reads the real response); the gate's heatmap checks seed their own payloads and are not expected to fail (record whether any does). (c2) In `heatmap_data` build the response from named keys that omit `statistics`: only `test_statistics_reach_the_browser_through_heatmap_data` FAILS (the happy-path test never touches the route). (d) For `test_a_window_with_no_best_day_shows_no_date`: remove the `best.date ?` guard in `kpiModel`; it FAILS. Record the failing names; discard.

- [ ] **Step 8: Docs in the same commit**

- `docs/architecture/runtime-system.md`: add the node `Stats[listening_stats.py<br/>statistics, populations stated]` in the Flask runtime subgraph after `Spotlight`, the edge `Heatmap --> Stats`, and `Stats` to the `class App,Routes,...,AlbumRequest runtime` line (without it the node renders unstyled). Run the Mermaid validator on the block before committing (`.github/instructions/mermaid.instructions.md`).
- `docs/architecture/heatmap-sequence.md`: in the aggregation step of the pipeline sequence (the line `Heatmap->>Heatmap: plays.aggregate_daily_counts: ...`) add `Heatmap->>Heatmap: heatmap_statistics(daily_counts, UTC window end)` with a one-line Note that streak, best day and average are computed here, change the existing `Heatmap->>Heatmap: Total and peak-day statistics` line to name `heatmap_statistics` (streak, best day, average, total, each with its population), change `succeed: daily_counts and progress 100%, in one write` to `succeed: daily_counts, statistics and progress 100%, in one write`, and change the final UI step to `UI->>UI: Render responsive SVG and the published KPIs`. Validate the diagram.
- `.claude/SESSION_CONTEXT.md`. Section 3: the `heatmap.py` tree comment `# heatmap_task, _fetch_and_process_heatmap` becomes `# heatmap_task, _fetch_and_process_heatmap; publishes the KPI statistics`. Section 4, current text then new text:
  - `heatmap.py       <- errors, jobs, lastfm, plays, utils, worker` becomes `heatmap.py       <- errors, jobs, lastfm, listening_stats, plays, utils, worker`
  - `dev/_frontend_gate_heatmap_access.py <- dev/_frontend_gate_shared; jobs` becomes `dev/_frontend_gate_heatmap_access.py <- dev/_frontend_gate_shared; jobs, listening_stats`
  - `dev/_frontend_gate_pipeline.py <- dev/_frontend_gate_shared; jobs` becomes `dev/_frontend_gate_pipeline.py <- dev/_frontend_gate_shared; jobs, listening_stats`
  - `dev/_frontend_gate_theme.py <- dev/_frontend_gate_colour, dev/_frontend_gate_shared; jobs` becomes `dev/_frontend_gate_theme.py <- dev/_frontend_gate_colour, dev/_frontend_gate_shared; jobs, listening_stats`
  - `dev/_frontend_gate_figures.py <- jobs` becomes `dev/_frontend_gate_figures.py <- jobs, listening_stats`
- README's module table is the documentation PR's (#8); this commit does not touch README.

- [ ] **Step 9: Section 4 entry, gates, commit**

Entry heading: `### <commit date, date +%F> - The heatmap KPIs come from Python`. Body: scope; the deleted `computeStreak`, `WINDOW_DAYS` and reduce; the published key; the two named edited tests (`test_happy_path_stores_correct_result_dict`, `test_kpi_blocks_show_what_the_window_holds`); the mutation evidence; the gate result; one sentence that `jobs._context_view` deep-copies only `daily_counts`, so `statistics` is returned by reference (nothing in this PR mutates it). Commit: `refactor(heatmap): Publish KPI statistics from Python`.

---

### Task 5: The Scrobbles figure comes from Python

**Touches:** `scrobblescope/routes/album_flow.py`, `templates/results.html`, `static/js/results.js`, `tests/test_routes.py`, `tests/test_template_shell.py`, `scripts/dev/results_behavior_tests.py`, `docs/architecture/runtime-system.md`, `docs/architecture/top-albums-sequence.md` (only if it states the figure), `.claude/SESSION_CONTEXT.md`, `docs/agents/PLAYBOOK.md`
**After:** Task 1, Task 2

**Interfaces:**
- Consumes: `listening_stats.album_play_statistics`.
- Produces: template variable `play_stats` (`plays_listed`, `plays_matched`, each `{"value", "population"}`); the stat element's `data-plays-listed` and `data-plays-matched` attributes, which `results.js` reads.

Why: the figure is a Jinja `sum`, and `results.js` sums it again whenever the Unmatched albums control switches. Both become reads of two published numbers. (The control is titled "Unmatched albums" with Hide and Include labels; its radio ids, `results_albums_matched` and `results_albums_all`, are what the tests click.) The displayed value is unchanged (Task 1 pins it), so no owner stop under the brief's rule applies; the population is now named in code. The route computes from the rows it renders, not at job completion, because the page filters rows after the job ends (playtime ranking) and the figure describes the rows on the page (Owner question 1).

- [ ] **Step 1: Failing tests**

In `tests/test_routes.py` add, after Task 1's two tests:

```python
def test_scrobbles_stat_publishes_both_populations_for_the_albums_control(client):
    """
    GIVEN an include run: three matched albums and two unmatched
    WHEN the Results page renders
    THEN the Scrobbles stat shows the listed plays and carries both figures
    as data attributes, so switching the Unmatched albums control (Hide/Include) needs no arithmetic.

    Mutation: render only one attribute, or derive matched from listed in the
    template, and the matched assertion fails.
    """
    page = _render_include_results(client)
    stat = re.search(r'<span id="stat-scrobbles"[^>]*>', page).group(0)
    assert 'data-plays-listed="200"' in stat
    assert 'data-plays-matched="120"' in stat
    assert _scrobbles_figure(page) == "200"


def test_scrobbles_stat_on_a_run_without_unmatched_rows_has_equal_figures(client):
    """A run without the include control states one figure twice.

    Mutation: have the template write 0 into ``data-plays-matched`` unless
    an unmatched row exists; the attribute reads 0 and this fails.
    """
    page = _render_results(
        client, [{**_provider_row("spotify", 0), "play_count": 50}]
    )
    stat = re.search(r'<span id="stat-scrobbles"[^>]*>', page).group(0)
    assert 'data-plays-listed="50"' in stat
    assert 'data-plays-matched="50"' in stat
```

Run: `... -m pytest tests/test_routes.py -k "scrobbles_stat" -q -p no:cacheprovider`. Expected: both FAIL (no data attributes).

In `scripts/dev/results_behavior_tests.py` add to the class holding `test_matched_only_hides_rows_renumbers_and_offers_listening_time`:

```python
    def test_scrobbles_stat_shows_the_published_figures_not_a_sum_of_rows(self):
        """Choosing Hide shows the published matched figure; Include shows
        the published listed figure. The numbers are deliberately not the sum of
        the rows, so a script that still adds up row play counts is caught.

        Mutation: restore the reduce over ``data-play-count`` in
        ``setUnmatchedHidden`` and the stat reads 120 instead of 999.
        """
        self.include_run()
        self.page.evaluate(
            "() => { const s = document.getElementById('stat-scrobbles');"
            " s.dataset.playsMatched = '999'; s.dataset.playsListed = '1001'; }"
        )
        self.page.locator("label[for=results_albums_matched]").click()
        self.assertEqual(self.page.locator("#stat-scrobbles").inner_text(), "999")
        self.page.locator("label[for=results_albums_all]").click()
        self.assertEqual(self.page.locator("#stat-scrobbles").inner_text(), "1,001")
```

(The attribute holds the plain number `1001`; the script formats it, so the stat must read `1,001`.)

Run the behaviour script (CI's test workflow runs it; `frontend_gate.py` does not; run it alone with `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/results_behavior_tests.py`). Expected: the new test FAILS (stat reads 120).

- [ ] **Step 2: Compute in the route**

In `scrobblescope/routes/album_flow.py` add `from scrobblescope.listening_stats import album_play_statistics` with the other package imports. After `filtered_results = _filter_results_for_display(results_data, sort_mode)` add:

```python
    # The figures describe the rows this page lists, after every filter it
    # applies, so they are computed here and not at job completion.
    play_stats = album_play_statistics(filtered_results)
```

and pass `play_stats=play_stats,` to both `render_template("results.html", ...)` calls (the `no_matches` branch too: its figures are 0).

- [ ] **Step 3: Render the published figures**

In `templates/results.html`:
- Delete `{% set total_scrobbles = album_list | sum(attribute='play_count') %}`.
- Replace the `stat-scrobbles` span with:

```html
                <span id="stat-scrobbles" data-plays-listed="{{ play_stats.plays_listed.value }}" data-plays-matched="{{ play_stats.plays_matched.value }}" class="font-serif text-xl md:text-[calc(1.9375rem*var(--results-scale))] text-[var(--color-base-content)] leading-tight">{{ "{:,}".format(play_stats.plays_listed.value) }}</span>
```

(the class list is the existing one, unchanged).

In `static/js/results.js`, inside `setUnmatchedHidden`, replace the `scrobbles` block with:

```js
        const scrobbles = document.getElementById('stat-scrobbles');
        if (scrobbles) {
            // Both figures were computed on the server (listening_stats.py);
            // the control only chooses which one to show.
            const plays = Number(hidden
                ? scrobbles.dataset.playsMatched
                : scrobbles.dataset.playsListed);
            scrobbles.textContent = plays.toLocaleString('en-US');
        }
```

In `scripts/dev/results_behavior_tests.py` `include_run`, build the fixture span from the rows the call renders, not from constants: `include_run(self, has_durations=True, include_rows=None)` takes custom rows, and `test_hiding_every_row_clears_the_top_artist_and_including_restores_it` passes two all-unmatched rows (45 and 35 plays) and asserts the stat reads `0` under Hide and `80` under Include, so a fixed 200/120 span would break it. Inside `include_run`, bind `rows_in_use = include_rows or self.INCLUDE_ROWS` (use it in the `enumerate` call too), compute `listed = sum(int(r[1]) for r in rows_in_use)` and `matched = sum(int(r[1]) for r in rows_in_use if not r[4])` (each row is `(name, plays, seconds, duration, unmatched)`) and write the span as an f-string: `f'<span id="stat-scrobbles" data-plays-listed="{listed}" data-plays-matched="{matched}">{listed}</span>'` (200 and 120 for the default `INCLUDE_ROWS`). Name this edit, the reason and `test_hiding_every_row_clears_the_top_artist_and_including_restores_it` (the first existing test it protects) in the commit body. Two direct renderers in `tests/test_template_shell.py` lack `play_stats`, and Jinja raises on the missing name. `TEMPLATE_CONTEXT["results.html"]` gains `"play_stats": album_play_statistics([])`; the helper `_results_html(app, **overrides)` (one album, renders `results.html`) passes `play_stats=album_play_statistics([album])` unless an override supplies it. Import `album_play_statistics` at the top of the file. Name both edits in the commit body. Run `git grep -n "results.html" tests scripts` and fix any further direct renderer the same way.

- [ ] **Step 4: Run tests and gate**

Run: `... -m pytest tests/test_routes.py tests/test_template_shell.py -q -p no:cacheprovider`, then `scripts/dev/results_behavior_tests.py`, then `scripts/dev/frontend_gate.py` (which covers the gate's own results pages).
Expected: all PASS; Task 1's `test_scrobbles_figure_*` still PASS unmodified (the displayed number did not move).

- [ ] **Step 5: Mutation evidence**

Scratch copy: (a) template renders `plays_matched` as the visible text: `test_scrobbles_stat_publishes_both_populations_for_the_albums_control` and Task 1's include assertion FAIL. (b) `album_play_statistics` computed from `results_data` instead of `filtered_results`: `test_scrobbles_figure_leaves_out_albums_a_playtime_ranking_drops` FAILS. (c) restore the reduce in `results.js`: the new behaviour test FAILS. Record names; discard.

- [ ] **Step 6: Docs in the same commit**

- `docs/architecture/runtime-system.md`: add the edge `Routes --> Stats` (the node and its `class` entry come from Task 4; if Task 4 has not landed in this tree, add node, class entry and edge here and drop them from Task 4's patch). Validate the block.
- `docs/architecture/top-albums-sequence.md`: `git grep -n -i "scrobbles\|stat" docs/architecture/top-albums-sequence.md`; if its Results-render step states how the stat block is computed, correct it to "play figures computed by listening_stats from the rows listed"; if it states nothing about it, change nothing and say so in the entry.
- `.claude/SESSION_CONTEXT.md` Section 4: `routes/album_flow.py    <- admission, album_request, jobs, orchestrator, precheck, spotlight, unmatched; routes (facade)` becomes `routes/album_flow.py    <- admission, album_request, jobs, listening_stats, orchestrator, precheck, spotlight, unmatched; routes (facade)`.

- [ ] **Step 7: Section 4 entry, gates, commit**

Entry heading: `### <commit date, date +%F> - The Scrobbles figure comes from Python`. Body: scope; the two removed copies of the sum (Jinja and `results.js`); the named edited tests and fixtures (`TEMPLATE_CONTEXT["results.html"]`, the `include_run` fixture span); the unchanged displayed number (Task 1's tests pass unmodified); the mutation evidence. Commit: `refactor(results): Compute the Scrobbles figure in Python`.

---

### Task 6: Amend WP-6, point Section 3 at the PR, push, PR (controller)

**Touches:** `BATCH23_DEFINITION.md`, `docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`
**After:** Task 4, Task 5; and PR #4 merged

- [ ] **Step 1:** `git fetch origin` and `git merge --no-ff origin/main` into `refactor/statistics-module`; resolve bookkeeping conflicts by keeping every dated entry from both sides; no `heatmap.py` conflict with PR #4 is expected, because #4 is already in the base (see the PR #4 table); `--fix --test-count N`.

- [ ] **Step 2: The WP-6 amendment.** In `BATCH23_DEFINITION.md`, WP-6, directly after the "Statistics contract before implementation" paragraph (whose last sentence is the include-unmatched amendment of 2026-10-20), add this paragraph verbatim. It states only what PR #6 builds and needs no other amendment to be true:

```
**The module exists (amended 2026-10-20, pre-Batch-23 PR #6).**
`scrobblescope/listening_stats.py` is the pure helper this work package
extends; it is not created here. It already computes the heatmap's current
streak, best day, daily average and total from the zero-filled UTC
`{date: plays}` window, and the Results page's plays listed and plays matched,
each published with a one-sentence population
(`{"value": ..., "population": ...}`). `heatmap.js`, `results.js` and
`results.html` render published values and compute none, and WP-6 keeps it so.
WP-6 adds its further statistics to that module as pure functions; its
specialized plan decides what data the aggregators keep for them, since the
daily window carries only plays per UTC day. An album listed through
include-unmatched counts in "plays listed" and in no duration-based figure,
because it has no durations.
```

- [ ] **Step 2b: Reconcile.** Read the merged PR #4's WP-2 amendment in `BATCH23_DEFINITION.md`. The paragraph above makes no claim about the export parser's record, so it should need no change; if #4's merge made any sentence of it untrue, correct that sentence and say so in the Section 4 entry.

- [ ] **Step 3:** In PLAYBOOK Section 3's "Before WP-1" bullet, change the sentence Task 0 appended ("PR #6, the statistics module, is under way on `refactor/statistics-module`; ...") to say the statistics-module PR is done (keep its branch and plan names), and reword "the other two seams remain, one album-metadata encoding and the statistics module" to match. In `.claude/SESSION_CONTEXT.md` Section 1's Batch 23 row, nothing changes unless it lists the tranche PRs by name; if it does, update that one entry. One Section 4 entry, heading `### <commit date, date +%F> - WP-6 builds on the statistics module`. Commit: `docs(batch23): Amend WP-6 for the statistics module`.

- [ ] **Step 4:** Gate-runner on the final head (all gates, plus `scripts/dev/results_behavior_tests.py`, which `frontend_gate.py` does not run), grep every log, then push, open the PR against `main`, and dispatch the CI watcher. Browser checks flake on Linux CI; re-run a suspected flake before calling it one.

---

## Self-Review

- **Spec coverage.** Python statistics module, UTC by construction (Task 2: `utc_date`, injected `today`, no clock import); each figure with its population stated (Task 2: `population` on every published fact, tested non-empty and distinct; include-unmatched policy in `plays_listed`/`plays_matched` and the amendment); facts published on the job result (Task 4, heatmap) and, for the album page, on the render path (Task 5; deviation explained, Owner question 1); `heatmap.js` and `results.html` render only (Tasks 4 and 5, plus `results.js`, the second copy of the Scrobbles sum); pure-function tests with tz-aware timestamps (`TestUtcDate`, `test_utc_midnight_decides_which_day_a_play_belongs_to`); the WP-6 amendment text (Task 6, exact).
- **Parity first.** Task 1 pins the KPIs through the real JS and the Scrobbles figure through the real route, before Tasks 4 and 5 move them; the same case table then holds the Python rules to the same numbers (Task 2) and the new renderer (Task 4). Edited tests are named per task.
- **Docs.** Diagrams made untrue: `runtime-system.md` (Tasks 4, 5) and `heatmap-sequence.md` (Task 4); `top-albums-sequence.md` checked in Task 5; SESSION_CONTEXT Section 3 (tree) and Section 4 (dependency lines, gate modules included) in Tasks 2, 4, 5 and Section 6 in Task 1. The README module table is #8's. The docsync declarations that the JS deletion would break are retired first in their own control-plane commit (Task 3).
- **Atomicity and ordering.** Six commits, each green alone: Task 1 and Task 3 change no behaviour; Task 2 adds an unused module; Task 4 leaves the album page alone; Task 5 leaves the heatmap alone. Parallelism for the controller: Tasks 1, 2 and 3 land serially in that order (every task writes PLAYBOOK Section 4 at the same marker, and Task 1 moves the `[test_count]` pin in `config/docsync.toml` that Task 3's `pytest -q` N follows); their code phases may be prepared in parallel. Task 2 follows Task 1; Tasks 4 and 5 may run as parallel code phases (disjoint code files) but share `runtime-system.md`, `SESSION_CONTEXT.md` and bookkeeping, so their landings are serial and the second rebuilds the shared docs (the node is created by whichever lands first).
- **One source for the total.** The KPI row reads `statistics.total_plays`; the SVG's `aria-label` and the loading code read `total_scrobbles` (key unchanged). Both derive from the same `daily_counts`, and Task 4's happy-path test asserts both equal 3.
- **Known limits, stated.** `listening_stats.best_day` returns no date for an all-quiet window where the old JS labelled the window's first day with a count of 0; the heatmap job fails before publishing such a window (`no_scrobbles_in_range`), so no page changes. The loading page's `stat-scrobbles` (all scrobbles fetched, a different population from Results) is untouched. `results.js` still picks the Top Artist from the first visible row (Owner question 3). No new I/O, no database traffic, no machine or service.
- **Placeholder scan.** Every code step shows code; the only discovery left to the implementer is the local variable names inside the eight gate fixtures and the `client` fixture's availability in `tests/test_heatmap.py`, both named where they occur.

## Owner questions

1. **Does the owner ratify a departure from the approved design?** The spec says facts are "published on the job result". For the heatmap they are. For the Results page's Scrobbles figure this plan computes it at render time in the Results route, from the rows on the page, instead of publishing it on the job result, because the page filters rows after the job ends (a playtime ranking drops albums with no listening time) and publishing at job completion would change the number users see on those runs. The displayed number does not change. Recommendation: yes, ratify.

## Decisions recorded (engineering calls, not owner questions)

- **A result without `statistics`.** The heatmap KPI row logs a console error and stays empty; it never computes a figure in the browser. The state is unreachable (jobs are in memory and a restored page refetches by job id), so no visible fallback is built.
- **Top Artist stat.** Left out: P6's scope is statistics, the Top Artist is a ranking choice shared with `select_spotlight_artists`, and the instructions allow nothing beyond the scope. It goes into the PR description as a candidate for WP-5/WP-6.

## Revision 1 (2026-10-20)

Fix round for `plan-review.md` (4 Important, 12 Minor) and the controller's six rulings.

| Finding | Change |
|---|---|
| Important 1 and ruling 1: `_frontend_gate_pipeline.py` payload missed | Added to Task 4 Touches, Step 5 (seven payloads listed by file, with the sweep command) and the PR #4 table; its Section 4 dependency line is in Step 8. |
| Important 2 and ruling 2: no named planted defect for about a dozen tests | Task 2 Step 5 is a table naming a planted defect for every new test; Task 4 names it for the no-best-day test (docstring and Step 7(d)); Task 5's equal-figures test carries its mutation in its docstring. |
| Important 3 and ruling 3: wrong SESSION_CONTEXT sections | Task 2 Step 6, Task 4 Step 8 and Task 5 Step 6 give exact Section 3 and Section 4 edits with current and new text, gate modules included; the prose bullet is dropped; Task 1 edits Section 6. |
| Important 4 and ruling 4: WP-6 amendment | Rewritten to stand alone: no WP-2 claim, no commitment to per-hour or per-weekday storage. Task 6 Step 2b reconciles against #4's merged text. |
| Minor 1 | Task 1 Step 7(b) and the test docstring list the third failing case. |
| Minor 2 | Task 1 Step 2 names the `json`, `date`, `timedelta` and `Path` imports. |
| Minor 3 | Task 5 Step 1 and Task 6 Step 4: CI and a manual run execute `results_behavior_tests.py`, not `frontend_gate.py`. |
| Minor 4 | Task 5 Step 3 names `_results_html` and `TEMPLATE_CONTEXT`. |
| Minor 5 | Task 4 Step 4 item 6 fixes the seam comment and the `streak` grep expectation; Step 5 fixes the `WINDOW_DAYS` comment in the gate. |
| Minor 6 | Task 4 Step 8: `Stats` joins the `class ... runtime` line; both `heatmap-sequence.md` lines updated. |
| Minor 7 | Task 1 Step 8 updates the Section 6 sentence on `tests/fixtures/`. |
| Minor 8 | The streak docstring now says 3 against 2. |
| Minor 9 | Self-Review: Tasks 1-3 land serially. |
| Minor 10 | Self-Review states which total each reader uses. |
| Minor 11 | Task 4 Step 3 imports are at the module top. |
| Minor 12 | Task 1 Interfaces cite `tests/helpers.py` for `TEST_JOB_PARAMS`. |
| Ruling 5 | Only Q1 remains, restated narrowly. The old Q2 is decided (console error plus an empty row, per the review's note on silent failure) and the old Q3 is decided (out of scope); both recorded above. |
| Ruling 6 | Three rows added to the PR #4 table: #4's publish step and `jobs.succeed`; the `fetch_all_recent_tracks_async` patch target and return shape (Task 4's publication test now drives the real task, so it and the happy-path test depend on it); PR #3's edits to `routes/album_flow.py`. |

## Revision 2 (2026-10-20)

Fix round for `plan-rereview-1.md` New Important 1 (mutation evidence that did not bite).

| Row | Change |
|---|---|
| Task 2 Step 5, `test_two_quiet_days_end_the_streak` | Test data now has plays on 03-07 and 03-08 (today 03-10), with a one-line comment of the hand values. Planted defect changed to "starts from `today - 2` when today is quiet": asserts 0, gets 2. The old defect (start from yesterday unconditionally) differs from correct code only when today has a play, so it is caught by `streak_ends_today` and Task 4 Step 7(a), not by this test. |
| Task 2 Step 5, `test_the_busiest_day_and_its_count` | Test data adds 2 plays on 03-08: busiest 03-06 (7), first play day 03-04 (3), last play day 03-08 (2). "Last day with a play" now gives `(03-08, 2)` against `(03-06, 7)`; the table states the assertion. |
| Task 4 Step 1 and Step 7(c), `test_statistics_reach_the_browser_through_heatmap_data` | Test now runs the real `_fetch_and_process_heatmap` (patched fetch) then GETs `/heatmap_data`, instead of seeding a stored result. Deleting `"statistics"` in heatmap.py now raises KeyError in it; Step 7(c2) adds the route-side defect only it catches. Step 1 expectation changed from "already passes" to "fails with KeyError". The PR #4 table and the Revision 1 ruling-6 row now say two tests depend on the fetch mock. The `heatmap_statistics` import and the duplicate `import pytest` instruction are gone from that step. |
| Task 4 Step 7(a) | Re-worked by hand: unconditional "start from yesterday" gives streak 1 against 2 in the publication test and 2 against 3 in `streak_ends_today`; values stated. |
| Task 2 Step 5, tie row | Failing assertion stated. Every other row was worked by hand against the module code and test data; all bite. |

## Revision 3 (2026-10-21)

Drift review of this plan against `eb0db9e` (`main` after PRs #256-#260), folded in when the branch was cut. The review's detail is in the SDD workspace; each item below was verified at source in `C:/ssw/st` before it was applied.

| Item | Change |
|---|---|
| S1: Task 4 Step 1's publication test | Re-pointed at `scrobblescope.heatmap.fetch_scrobbles` with the `_fetch` and `_play` helpers and `UTC`; `_make_track`, `_wrap_tracks` and `fetch_all_recent_tracks_async` no longer exist. The closing paragraph names `_play` and `_fetch`. |
| S2: Task 5 Step 3's `include_run` span | Built from the rows `include_run` renders, so `test_hiding_every_row_clears_the_top_artist_and_including_restores_it` (custom all-unmatched rows) keeps passing. |
| S3: Task 4's gate payloads | `scripts/dev/_frontend_gate_figures.py` (`_HEATMAP_RESULT`) added to Touches, the File Structure row, Step 5 (eight payloads, not seven) and the Step 8 dependency lines. |
| R1-R3: renames | `plays.aggregate_daily_counts`; `_play`/`_fetch`; `fetch_scrobbles`. The PR #4 table is rewritten as resolved. |
| R4: `UTC` | Task 2's module and tests use `UTC` (ruff `UP017`); `timezone` stays for the fixed-offset zones. |
| R5-R6: dependency lines and quotes | The `heatmap` docstring line and the SESSION_CONTEXT Section 3 and 4 current-text quotes now match the tree; `routes/album_flow.py`'s line and the `figures` gate line are corrected. |
| R7: module docstring | Names `plays.aggregate_daily_counts` and `Play`'s UTC refusal. |
| C1-C9 | Helper imports; the `HEATMAP_WINDOW_DAYS` comment replacement; `runtime-system.md` class line ends in `AlbumRequest`; `heatmap-sequence.md` anchor named; Unmatched albums / Hide / Include wording; entry headings take the commit date; Task 6 Step 1 conflict note is moot and Step 3 updates the sentence Task 0 appended; `jobs._context_view` sentence in Task 4's commit body. C3 and C7 needed no change. |

## Owner answers (2026-10-20)

Q1, owner (verbatim): "Yes, that sounds good." The Scrobbles figure is computed at render time in the Results route from the rows on the page; the departure from "published on the job result" is ratified.
