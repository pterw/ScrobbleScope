# Batch 21 WP-7: Unmatched Page & Backend Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the unmatched album grouping bug by introducing a stable `reason_code` contract, address concrete SoC and DRY violations across routing and worker event loops, and rebuild `templates/unmatched.html` on Tailwind CSS v4 and daisyUI.

**Architecture:** The unmatched domain logic is extracted into a dedicated `scrobblescope/unmatched.py` module (matching the precedent of `spotlight.py`), decoupling domain categorization from `routes.py`. `orchestrator.py` tags Spotify search misses with `no_spotify_match` and release-scope filter exclusions with `release_scope`. The committed backend contract left the heatmap pipeline untouched. During frontend reconciliation, the existing F-B21-1 worker-cleanup defect required the same bounded fix in `scrobblescope/orchestrator.py` and `scrobblescope/heatmap.py`; the deviation record below supersedes the original isolation claim. `unmatched.html` is migrated to Tailwind v4 and daisyUI with semantic reason cards, 1px hairlines, and no resting drop shadows, allowing the removal of `bootstrap.bundle.min.js`. Cached album artwork remains primary; missing artwork progressively hydrates an artist portrait through the existing `/api/artist_spotlight` route with viewport deferral and per-artist request deduplication.

**Tech Stack:** Python 3.13, Flask, Jinja2, Tailwind CSS v4, daisyUI v5, Playwright, pytest.

**Spec:** `BATCH21_DEFINITION.md` (Section WP-7), `DESIGN.md`, `docs/design/README.md` (Screen 5: Unmatched).

## Global Constraints

- Pinned dependencies only: no new entries in `requirements.txt` or `requirements-dev.txt`.
- ASCII-only characters in all Python source and Markdown documentation; `--` for dashes, never em-dash.
- Original two-commit sequence mandated by `BATCH21_DEFINITION.md`:
  1. `feat(unmatched): add stable reason_code to the unmatched contract` (Tasks 1-3)
  2. `feat(ui): rebuild unmatched page on tailwind` (Tasks 4-5)
- Execution adds the owner-authorized non-rewrite `fix(workers)` deviation
  commit between those rollback units; deviation 4 records why.
- The original reason codes were `release_scope` and `no_spotify_match`.
  The owner-approved 2026-09-11 extension adds one de-duplicated
  `below_threshold` code; its separate design and execution contract is the
  dated threshold-extension plan under `docs/superpowers/plans/`.
- Spacing and type in CSS must use `rem` (divide px by 16); hairline borders, outlines, radii remain `px`.
- Touch targets on coarse pointers (`@media (any-pointer: coarse)`) must be at least 44px on their smaller side.
- No `font-weight: 500` or `font-weight: 600` (the Adobe Fonts kit serves 300, 400, 700 only).
- The worktree virtualenv is `.venv/` in the primary checkout (`C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe`). Run all commands through the qualified path.
- Conventional Commits, imperative mood, no trailing period, no `Co-authored-by`.

## File Structure

- Create: `scrobblescope/unmatched.py` -- stable reason codes (`REASON_RELEASE_SCOPE`, `REASON_NO_SPOTIFY_MATCH`), category presentation metadata, and pure grouping function `group_unmatched_albums`.
- Modify: `scrobblescope/orchestrator.py` -- tag search misses (`no_spotify_match`) and release scope exclusions (`release_scope`) with `reason_code`.
- Modify: `scrobblescope/routes.py` -- replace `_group_unmatched_by_reason` with `group_unmatched_albums` from `scrobblescope.unmatched`.
- Modify: `templates/unmatched.html` -- opt out of legacy Bootstrap CSS (`{% block legacy_css %}{% endblock %}`), link `tailwind.css` and `unmatched.css`, remove `bootstrap.bundle.min.js`, rebuild with Tailwind reason cards and expander.
- Modify: `static/css/unmatched.css` -- purge legacy `.card`/`.table` Bootstrap rules, author token-based styles with 44px touch targets.
- Modify: `static/js/unmatched.js` -- client-side keyboard-accessible expander for categories with more than 10 albums plus lazy, deduplicated artist-portrait hydration through `/api/artist_spotlight`.
- Create: `tests/test_unmatched.py` -- unit tests for `scrobblescope/unmatched.py` grouping and fallback.
- Modify: `tests/test_routes.py` -- update `/api/unmatched` and `/unmatched` route tests for `reason_code` and single-group grouping across years.
- Modify: `tests/services/test_orchestrator_helpers.py` & `tests/services/test_orchestrator_fetch_spotify.py` -- assert `add_job_unmatched` receives `reason_code`.
- Modify: `tests/test_template_shell.py` -- move `"unmatched.html"` into `MIGRATED` set.
- Modify: `scripts/dev/frontend_gate.py` -- add `/unmatched` to `MIGRATED_PAGES`.

---

## Part 1: Backend Contract (`feat(unmatched): add stable reason_code to the unmatched contract`)

### Task 1: Unmatched domain module (`scrobblescope/unmatched.py`)

**Files:**
- Create: `scrobblescope/unmatched.py`
- Create: `tests/test_unmatched.py`

**Interfaces:**
- Produces:
  - `REASON_RELEASE_SCOPE = "release_scope"`
  - `REASON_NO_SPOTIFY_MATCH = "no_spotify_match"`
  - `CATEGORY_METADATA: dict[str, dict[str, str]]`
  - `group_unmatched_albums(unmatched_data: dict[str, dict]) -> tuple[dict[str, list[dict]], dict[str, int], dict[str, dict[str, str]]]`

- [x] **Step 1: Write the failing unit tests**

Create `tests/test_unmatched.py`:

```python
from scrobblescope.unmatched import (
    REASON_NO_SPOTIFY_MATCH,
    REASON_RELEASE_SCOPE,
    group_unmatched_albums,
)


def test_group_unmatched_albums_groups_by_reason_code():
    """Albums with different release years must group under the single release_scope code."""
    data = {
        "art1|alb1": {
            "artist": "Artist 1",
            "album": "Album 1",
            "reason": "Released in 2018 (filter requires 2024)",
            "reason_code": REASON_RELEASE_SCOPE,
        },
        "art2|alb2": {
            "artist": "Artist 2",
            "album": "Album 2",
            "reason": "Released in 2019 (filter requires 2024)",
            "reason_code": REASON_RELEASE_SCOPE,
        },
        "art3|alb3": {
            "artist": "Artist 3",
            "album": "Album 3",
            "reason": "No Spotify match",
            "reason_code": REASON_NO_SPOTIFY_MATCH,
        },
    }

    groups, counts, metadata = group_unmatched_albums(data)

    assert len(groups) == 2
    assert counts[REASON_RELEASE_SCOPE] == 2
    assert counts[REASON_NO_SPOTIFY_MATCH] == 1
    assert len(groups[REASON_RELEASE_SCOPE]) == 2
    assert len(groups[REASON_NO_SPOTIFY_MATCH]) == 1
    assert metadata[REASON_RELEASE_SCOPE]["title"] == "Outside Release Filter"
    assert metadata[REASON_NO_SPOTIFY_MATCH]["title"] == "No Spotify Match"
    # Row detail preserved
    assert groups[REASON_RELEASE_SCOPE][0]["reason"] == "Released in 2018 (filter requires 2024)"


def test_group_unmatched_albums_handles_legacy_missing_reason_code():
    """Legacy jobs with missing reason_code must fall back gracefully to prose reason."""
    data = {
        "art1|alb1": {
            "artist": "Artist 1",
            "album": "Album 1",
            "reason": "Custom unclassified reason",
        }
    }

    groups, counts, metadata = group_unmatched_albums(data)

    assert "Custom unclassified reason" in groups
    assert counts["Custom unclassified reason"] == 1
    assert metadata["Custom unclassified reason"]["title"] == "Custom unclassified reason"
```

- [x] **Step 2: Run test to verify it fails**

Run: `& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe" tests/test_unmatched.py -v`
Expected: FAIL (ModuleNotFoundError: No module named 'scrobblescope.unmatched')

- [x] **Step 3: Implement `scrobblescope/unmatched.py`**

Create `scrobblescope/unmatched.py`:

```python
"""Domain logic, category definitions, and grouping for unmatched albums.

Separates unmatched aggregation and presentation metadata from Flask routes
and async background workers.
"""

from __future__ import annotations

from typing import Any

#: Stable reason codes stored on unmatched items.
REASON_RELEASE_SCOPE = "release_scope"
REASON_NO_SPOTIFY_MATCH = "no_spotify_match"

#: Human copy, badges, and fix hints associated with each reason code.
CATEGORY_METADATA = {
    REASON_RELEASE_SCOPE: {
        "title": "Outside Release Filter",
        "description": "Albums released outside your selected release-date scope.",
        "badge": "Release date",
        "fix_hint": 'Choose "All years (no filter)" on a new search to include these releases.',
    },
    REASON_NO_SPOTIFY_MATCH: {
        "title": "No Spotify Match",
        "description": "Albums found in your Last.fm history that could not be matched on Spotify.",
        "badge": "Not on Spotify",
        "fix_hint": "Check album title formatting or artist naming on Last.fm.",
    },
}


def group_unmatched_albums(
    unmatched_data: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int], dict[str, dict[str, str]]]:
    """Group unmatched album items by their stable ``reason_code``.

    If an item lacks ``reason_code`` (legacy jobs), it falls back to the
    per-album ``reason`` string so historical data remains viewable.

    Returns:
        tuple of ``(groups, counts, metadata)`` where:
        - ``groups`` maps each group key to its list of album items.
        - ``counts`` maps each group key to the count of items in that group.
        - ``metadata`` maps each group key to a dict with ``title``,
          ``description``, ``badge``, and ``fix_hint``.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    metadata: dict[str, dict[str, str]] = {}

    for item in unmatched_data.values():
        code = item.get("reason_code")
        if code and code in CATEGORY_METADATA:
            group_key = code
            meta = CATEGORY_METADATA[code]
        else:
            prose = item.get("reason", "Unknown reason")
            group_key = prose
            meta = {
                "title": prose,
                "description": "Excluded from results based on search criteria.",
                "badge": "Excluded",
                "fix_hint": "Excluded from results based on criteria.",
            }

        groups.setdefault(group_key, []).append(item)
        if group_key not in metadata:
            metadata[group_key] = meta

    # Deterministic sort: canonical codes first, then alphabetical
    def _sort_key(k: str) -> tuple[int, str]:
        order = [REASON_RELEASE_SCOPE, REASON_NO_SPOTIFY_MATCH]
        return (order.index(k) if k in order else 99, k)

    sorted_groups = {k: groups[k] for k in sorted(groups.keys(), key=_sort_key)}
    counts = {k: len(v) for k, v in sorted_groups.items()}

    return sorted_groups, counts, metadata
```

- [x] **Step 4: Run test to verify it passes**

Run: `& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe" tests/test_unmatched.py -v`
Expected: PASS (2 passed)

---

### Task 2: Orchestrator `reason_code` contract

**Files:**
- Modify: `scrobblescope/orchestrator.py:255-267,470-480`
- Test: `tests/services/test_orchestrator_fetch_spotify.py`, `tests/services/test_orchestrator_helpers.py`

**Interfaces:**
- Consumes: `REASON_RELEASE_SCOPE`, `REASON_NO_SPOTIFY_MATCH` from `scrobblescope.unmatched`
- Produces: `reason_code` field on all newly recorded unmatched albums

- [x] **Step 1: Write failing tests asserting `reason_code` in unmatched records**

In `tests/services/test_orchestrator_fetch_spotify.py`, update `test_run_spotify_search_phase_all_misses_returns_empty_maps`:

```python
@pytest.mark.asyncio
async def test_run_spotify_search_phase_records_reason_code():
    """Spotify search misses must be recorded with reason_code='no_spotify_match'."""
    job_id = create_job(TEST_JOB_PARAMS)
    cache_misses = {
        ("Artist A", "Album A"): {
            "original_artist": "Artist A",
            "original_album": "Album A",
        }
    }
    with patch("scrobblescope.orchestrator.search_for_spotify_album_id", return_value=None):
        async with aiohttp.ClientSession() as session:
            await _run_spotify_search_phase(
                job_id, session, cache_misses, "token", len(cache_misses)
            )

    unmatched = get_job_unmatched(job_id)
    key = "artist a|album a"
    assert key in unmatched
    assert unmatched[key]["reason_code"] == "no_spotify_match"
```

In `tests/services/test_orchestrator_helpers.py`, add `test_build_results_records_reason_code`:

```python
def test_build_results_records_reason_code():
    """Albums excluded by release criteria must record reason_code='release_scope'."""
    job_id = create_job(TEST_JOB_PARAMS)
    cache_hits = {
        ("artist", "album"): {
            "cached": {
                "spotify_id": "sp1",
                "release_date": "2018-01-01",
                "album_image_url": "https://img.example.com/a.jpg",
                "track_durations": {},
            },
            "original": {
                "play_count": 20,
                "track_counts": {"song a": 5},
                "original_artist": "Artist",
                "original_album": "Album",
            },
        }
    }

    results = _build_results(
        cache_hits, job_id, year=2024, sort_mode="playcount", release_scope="same"
    )

    assert len(results) == 0
    unmatched = get_job_unmatched(job_id)
    key = "artist|album"
    assert key in unmatched
    assert unmatched[key]["reason_code"] == "release_scope"
```

- [x] **Step 2: Run tests to verify failure**

Run: `& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe" tests/services/test_orchestrator_helpers.py -k "test_build_results_records_reason_code" -v`
Expected: FAIL (KeyError: 'reason_code')

- [x] **Step 3: Update `scrobblescope/orchestrator.py`**

1. Import reason codes:
   ```python
   from scrobblescope.unmatched import REASON_NO_SPOTIFY_MATCH, REASON_RELEASE_SCOPE
   ```
2. In `_run_spotify_search_phase` line 258:
   ```python
            add_job_unmatched(
                job_id,
                unmatched_key,
                {
                    "artist": original_artist,
                    "album": original_album,
                    "reason": "No Spotify match",
                    "reason_code": REASON_NO_SPOTIFY_MATCH,
                },
            )
   ```
3. In `_build_results` line 474:
   ```python
            add_job_unmatched(
                job_id,
                unmatched_key,
                {
                    "artist": artist,
                    "album": album,
                    "reason": reason,
                    "reason_code": REASON_RELEASE_SCOPE,
                },
            )
   ```
4. In `_detect_spotify_total_failure` line 697 (remedy for missed P0 upstream failure check):
   Check `reason_code == REASON_NO_SPOTIFY_MATCH` with legacy fallback to prose:
   ```python
        spotify_no_match = sum(
            1
            for v in unmatched.values()
            if v.get("reason_code") == REASON_NO_SPOTIFY_MATCH
            or (not v.get("reason_code") and v.get("reason") == "No Spotify match")
        )
   ```
   Verified via TDD mutest: reverting to prose-only fails `test_detect_spotify_total_failure_bases_detection_on_reason_code`.

- [x] **Step 4: Run tests to verify pass**

Run: `& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe" tests/services/test_orchestrator_*.py -q`
Expected: PASS (all orchestrator tests pass)

---

### Task 3: Routes integration & Commit 1 verification

**Files:**
- Modify: `scrobblescope/routes.py:97-110,682-698`
- Modify: `tests/test_routes.py`

- [x] **Step 1: Write updated route tests in `tests/test_routes.py`**

Update `test_unmatched_view_success_renders_grouped_reasons`:

```python
def test_unmatched_view_success_renders_grouped_reasons(client):
    """Multiple albums outside the release scope must group together by reason_code."""
    job_id = create_job(TEST_JOB_PARAMS)
    add_job_unmatched(
        job_id,
        "a|one",
        {"artist": "Artist A", "album": "Album One", "reason": "No Spotify match", "reason_code": "no_spotify_match"},
    )
    add_job_unmatched(
        job_id,
        "b|two",
        {"artist": "Artist B", "album": "Album Two", "reason": "Released in 2018 (filter requires 2024)", "reason_code": "release_scope"},
    )
    add_job_unmatched(
        job_id,
        "c|three",
        {"artist": "Artist C", "album": "Album Three", "reason": "Released in 2019 (filter requires 2024)", "reason_code": "release_scope"},
    )

    response = client.post("/unmatched_view", data={"job_id": job_id})
    assert response.status_code == 200
    assert b"Albums That Didn't Match Your Filter" in response.data
    assert b"Outside Release Filter" in response.data or b"release_scope" in response.data
    assert b"Artist B" in response.data
    assert b"Artist C" in response.data
```

- [x] **Step 2: Update `scrobblescope/routes.py`**

Import and use `group_unmatched_albums`:

```python
from scrobblescope.unmatched import group_unmatched_albums

# In _render_unmatched_page():
    unmatched_data = dict(job_context.get("unmatched", {}))
    reasons, reason_counts, reason_metadata = group_unmatched_albums(unmatched_data)

    return render_template(
        "unmatched.html",
        username=username,
        year=year,
        filter_desc=filter_desc,
        unmatched_data=unmatched_data,
        reasons=reasons,
        reason_counts=reason_counts,
        reason_metadata=reason_metadata,
        total_count=len(unmatched_data),
        min_plays=min_plays,
        min_tracks=min_tracks,
        job_id=job_id,
    )
```

- [x] **Step 3: Run full verification suite for Commit 1**

```bash
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe" -q
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pre-commit.exe" run --all-files
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe" scripts/doc_state_sync.py --check
```
Expected: All tests pass, all hooks pass, doc_state_sync exits 0.

- [x] **Step 4: Commit Part 1**

```bash
git add scrobblescope/unmatched.py scrobblescope/orchestrator.py scrobblescope/routes.py tests/test_unmatched.py tests/test_routes.py tests/services/test_orchestrator_fetch_spotify.py tests/services/test_orchestrator_helpers.py
git commit -m "feat(unmatched): Add stable reason_code to the unmatched contract"
# Committed as b3e3e96
```

---

## Part 2: UI Overhaul (`feat(ui): rebuild unmatched page on tailwind`)

### Task 4: Rebuild `templates/unmatched.html`, `static/css/unmatched.css`, and `static/js/unmatched.js`

**Files:**
- Modify: `templates/unmatched.html`
- Modify: `static/css/unmatched.css`
- Modify: `static/js/unmatched.js`

**Interfaces:**
- Consumes: `reasons`, `reason_counts`, `reason_metadata`, `total_count`, `filter_desc`, `username`, `year` from `_render_unmatched_page`
- Produces: Tailwind v4 / daisyUI template compliant with `DESIGN.md` and Screen 5 specification

- [x] **Step 1: Rewrite `templates/unmatched.html`**

```html
{% extends "base.html" %}

{% block title %}Unmatched Albums | ScrobbleScope{% endblock %}

{# Migrated to Tailwind; opt out of legacy Bootstrap stack. #}
{% block legacy_css %}{% endblock %}

{% block stylesheets %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/tailwind.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/unmatched.css') }}">
{% endblock %}

{% block content %}
<main class="unmatched-page mx-auto px-4 pt-4 pb-12 md:pt-6 md:pb-16">
    <!-- Masthead: Editorial title + navigation actions -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6 pb-4 border-b border-[var(--ss-border-default)]">
        <div>
            <span class="font-mono text-xs text-[var(--ss-text-muted)] tracking-wider uppercase block mb-1">
                Audit & Discovery · {{ year }}
            </span>
            <h1 class="font-serif text-3xl md:text-5xl text-[var(--color-base-content)] leading-tight">
                Albums that didn't match for <span class="italic text-[var(--color-primary)]">{{ username }}</span>
            </h1>
            <p class="font-sans text-sm md:text-base text-[var(--ss-text-muted)] mt-1">
                {{ filter_desc|capitalize }} · Minimum {{ min_plays }} plays and {{ min_tracks }} unique tracks
            </p>
        </div>
        <div class="flex items-center gap-3 flex-shrink-0">
            <a href="{{ url_for('main.results') }}" class="btn btn-outline min-h-[44px] px-4 font-sans text-sm rounded-[var(--radius-field,8px)]">
                Back to Results
            </a>
            <a href="/" class="btn btn-primary min-h-[44px] px-5 font-sans text-sm rounded-[var(--radius-field,8px)]">
                New Search
            </a>
        </div>
    </div>

    <!-- Active Summary Pill Bar -->
    <div class="bg-[var(--ss-surface-card)] border border-[var(--ss-border-default)] rounded-[var(--radius-field,8px)] p-4 mb-8 flex flex-wrap items-center justify-between gap-4">
        <div class="flex flex-wrap items-center gap-2 text-xs font-mono">
            <span class="px-2 py-1 bg-[var(--ss-surface-sunken)] rounded text-[var(--ss-text-body)]">
                YEAR: {{ year }}
            </span>
            <span class="px-2 py-1 bg-[var(--ss-surface-sunken)] rounded text-[var(--ss-text-body)]">
                FILTER: {{ filter_desc }}
            </span>
            <span class="px-2 py-1 bg-[var(--ss-surface-sunken)] rounded text-[var(--ss-text-body)]">
                MIN: {{ min_plays }} plays / {{ min_tracks }} tracks
            </span>
        </div>
        <div class="text-sm font-sans text-[var(--ss-text-muted)]">
            Total unmatched: <strong class="text-[var(--color-base-content)]">{{ total_count }}</strong>
        </div>
    </div>

    <!-- Reason Groups Grid -->
    {% if total_count == 0 %}
    <div class="text-center py-12 bg-[var(--ss-surface-card)] border border-[var(--ss-border-default)] rounded-[var(--radius-card,14px)]">
        <p class="font-sans text-base text-[var(--ss-text-muted)]">No albums to review for this search.</p>
    </div>
    {% else %}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {% for reason_key, albums in reasons.items() %}
        {% set meta = reason_metadata.get(reason_key, {}) %}
        <section class="unmatched-group col-span-1 {% if reasons|length == 1 %}lg:col-span-3{% elif albums|length > 8 %}lg:col-span-2{% else %}lg:col-span-1{% endif %} bg-[var(--ss-surface-card)] border border-[var(--ss-border-default)] rounded-[var(--radius-card,14px)] p-5 md:p-6 flex flex-col justify-between" data-reason="{{ reason_key }}">
            <div>
                <!-- Card Header -->
                <div class="flex items-start justify-between gap-4 mb-4 pb-3 border-b border-[var(--ss-border-default)]">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="font-mono text-xs px-2 py-0.5 rounded bg-[var(--ss-accent-soft)] text-[var(--color-primary)] uppercase tracking-wider">
                                {{ meta.badge|default('Excluded') }}
                            </span>
                            <h2 class="font-sans font-bold text-lg md:text-xl text-[var(--color-base-content)]">
                                {{ meta.title|default(reason_key) }}
                            </h2>
                        </div>
                        <p class="font-sans text-sm text-[var(--ss-text-muted)]">
                            {{ meta.description|default('Albums excluded by filter criteria.') }}
                        </p>
                    </div>
                    <div class="text-right flex-shrink-0">
                        <span class="font-figure text-2xl md:text-3xl font-bold text-[var(--color-primary)]">
                            {{ reason_counts[reason_key] }}
                        </span>
                        <span class="block font-mono text-[0.625rem] uppercase text-[var(--ss-text-muted)]">albums</span>
                    </div>
                </div>

                <!-- Table of unmatched items -->
                <div class="overflow-x-auto">
                    <table class="w-full text-left font-sans text-sm">
                        <thead>
                            <tr class="border-b border-[var(--ss-border-default)] text-xs font-mono uppercase text-[var(--ss-text-muted)]">
                                <th class="py-2 px-3 w-12 text-center">#</th>
                                <th class="py-2 px-3">Album &amp; Artist</th>
                                <th class="py-2 px-3 text-right">Reason Detail</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-[var(--ss-border-default)]">
                            {% for item in albums %}
                            <tr class="hover:bg-[var(--ss-surface-sunken)] {% if loop.index > 10 %}unmatched-overflow hidden{% endif %}">
                                <td class="py-2 px-3 font-mono text-xs text-center text-[var(--ss-text-muted)]">{{ "%02d" % loop.index }}</td>
                                <td class="py-2 px-3">
                                            <div class="font-normal text-[var(--color-base-content)] leading-snug">{{ item.album }}</div>
                                    <div class="text-xs text-[var(--ss-text-muted)]">{{ item.artist }}</div>
                                </td>
                                <td class="py-2 px-3 font-mono text-xs text-right text-[var(--ss-text-muted)]">{{ item.reason }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <!-- Expander Button if more than 10 items -->
                {% if albums|length > 10 %}
                <div class="mt-3 text-center">
                    <button type="button"
                            class="unmatched-expander-btn btn btn-sm btn-ghost font-mono text-xs text-[var(--color-primary)] hover:bg-[var(--ss-accent-soft)]"
                            aria-expanded="false"
                            data-total-count="{{ albums|length }}">
                        Show all {{ albums|length }} albums
                    </button>
                </div>
                {% endif %}
            </div>

            <!-- Purple mono uppercase fix line at 9px held to one line (Screen 5 spec) -->
            <div class="mt-4 pt-3 border-t border-[var(--ss-border-default)] font-mono text-[0.5625rem] uppercase tracking-wider text-[var(--color-primary)] truncate"
                 title="{{ meta.fix_hint|default('Excluded from results based on criteria.') }}">
                {{ meta.fix_hint|default('Excluded from results based on criteria.') }}
            </div>
        </section>
        {% endfor %}
    </div>
    {% endif %}
</main>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/unmatched.js') }}"></script>
{% endblock %}
```

- [x] **Step 2: Rewrite `static/css/unmatched.css`**

Replace `static/css/unmatched.css` with token-based styles adhering to `DESIGN.md`:

```css
/* unmatched.css -- Unmatched albums report page styles */

.unmatched-page {
    max-width: 73.75rem;
    min-height: calc(100vh - 12rem);
}

.unmatched-group {
    background-color: var(--ss-surface-card);
    border: 1px solid var(--ss-border-default);
    box-shadow: none;
}

@media (any-pointer: coarse) {
    .unmatched-page .btn {
        min-height: 44px;
    }
}
```

- [x] **Step 3: Implement client-side expander in `static/js/unmatched.js`**

Replace `static/js/unmatched.js` with keyboard-accessible expander:

```javascript
// static/js/unmatched.js
// Client-side expander for unmatched album groups (>10 albums).

document.addEventListener('DOMContentLoaded', () => {
    const expanderButtons = document.querySelectorAll('.unmatched-expander-btn');
    expanderButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            const group = btn.closest('.unmatched-group');
            if (!group) return;
            const overflowRows = group.querySelectorAll('.unmatched-overflow');
            const isExpanded = btn.getAttribute('aria-expanded') === 'true';
            const total = btn.getAttribute('data-total-count') || '';

            overflowRows.forEach((row) => {
                row.classList.toggle('hidden', isExpanded);
            });

            btn.setAttribute('aria-expanded', String(!isExpanded));
            btn.textContent = isExpanded ? `Show all ${total} albums` : 'Show fewer';
        });
    });
});
```

- [x] **Step 4: Rebuild Tailwind CSS**

Run: `& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe" scripts/dev/tailwind_build.py`
Expected: Successfully compiled `static/css/tailwind.css`.

---

### Task 5: Shell test, frontend gate integration, and Commit 2 verification

**Files:**
- Modify: `tests/test_template_shell.py:92-100`
- Modify: `tests/services/test_orchestrator_fetch_spotify.py`
- Modify: `scripts/dev/frontend_gate.py:177,2687`

**Interfaces:**
- Consumes: Migrated `unmatched.html` template and static assets
- Produces: Green test suite, clean Playwright browser passes on Chromium and Firefox

- [x] **Step 1: Move `unmatched.html` to `MIGRATED` in `tests/test_template_shell.py`**

Line 92 of `tests/test_template_shell.py`:

```python
MIGRATED = {
    "error.html",
    "heatmap_empty.html",
    "index.html",
    "loading.html",
    "results.html",
    "results_empty.html",
    "unmatched.html",
    "unmatched_empty.html",
}
```

- [x] **Step 2: Run template shell tests**

Run: `& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe" tests/test_template_shell.py -q`
Expected: PASS (all template shell assertions pass with `unmatched.html` migrated).
Execution: 109 passed in 1.95s.

- [x] **Step 3: Update `scripts/dev/frontend_gate.py`**

In `scripts/dev/frontend_gate.py`, add `"/unmatched"` to `MIGRATED_PAGES` at line 177:

```python
MIGRATED_PAGES = ["/", "/results", "/heatmap", "/unmatched", ERROR_PAGE_PATH]
```

This immediately subjects `/unmatched` to:
- `check_stylesheet_isolation`: verifies `/unmatched` loads only `tailwind.css` and 0 Bootstrap stylesheets.
- `check_theme_tokens`: verifies `--color-primary` resolves and no forbidden surfaces appear.
- `check_fonts`: verifies Adobe Fonts kit integration.
- `check_body_font`: verifies body typography on desktop and mobile.
- `check_touch_targets`: verifies all interactive links and buttons have >=44px touch targets on coarse pointers.
- `check_unmatched_report`: creates a populated disposable job and verifies two
  stable reason groups, the 10-row disclosure boundary in both toggle states,
  Spotify and play-count enrichment, lazy artist-portrait hydration through
  the existing full-stack route, the figure type role, and absence of
  unsupported 500/600 computed font weights.

- [x] **Step 4: Run full verification gate & mutation tests (mutests)**

```bash
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe" -q
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pre-commit.exe" run --all-files
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe" scripts/doc_state_sync.py --fix
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe" scripts/dev/frontend_gate.py
```
Expected: All unit tests pass, pre-commit passes, doc sync passes, and the frontend gate passes all 26 checks across 46 runs in Chromium and Firefox.

**Fresh Verification Evidence:**

1. `pytest -q`: **986 passed**, 2 warnings across 41 test modules.
2. `python scripts/dev/frontend_gate.py`: **26 checks passed in 46 runs**
   across Chromium and the Firefox static-assets canary.
3. Focused WP-7 suite: **345 passed**, 2 warnings.
4. `node --check static/js/unmatched.js`: passed.
5. `tailwind_build.py --check`: passed; generated CSS matches its sources.
6. `pre-commit run --all-files`: all 10 hooks passed.
7. `doc_state_sync.py --check`: passed with the expected active root Batch 21
   definition warning.

**Mutation Testing (mutests) Conducted:**
- **Mutest 1 (Domain Grouping)**: Disabled `reason_code` check in `scrobblescope/unmatched.py` (forced fallback to prose).
  - *Result*: RED (2 failures: `tests/test_unmatched.py::test_group_unmatched_albums_groups_by_reason_code` failed with `AssertionError: 3 == 2`; `tests/test_routes.py::test_unmatched_view_success_renders_grouped_reasons` failed).
  - *Restoration*: Restored code -> GREEN (109 passed).
- **Mutest 2 (Template Framework Isolation)**: Removed `{% block legacy_css %}{% endblock %}` in `templates/unmatched.html`.
  - *Result*: RED (2 failures in `tests/test_template_shell.py`: `test_every_page_loads_exactly_one_framework_stylesheet` failed with `AssertionError: unmatched.html loads 2 framework stylesheets`; `test_each_page_loads_the_framework_its_markup_is_written_for` failed).
  - *Restoration*: Restored block -> GREEN (109 passed).
- **Mutest 3 (Mobile Touch Targets in Real Browser)**: Mutated `static/css/unmatched.css` button touch target to 20px.
  - *Result*: RED in `scripts/dev/frontend_gate.py` (`FAIL chromium: touch targets [mobile]: /unmatched [as loaded]: a.btn is 133x20, smaller side under 44px`).
  - *Restoration*: Restored 44px min-height -> GREEN (25 checks passed in 45 runs).
- **Mutest 4 (Bootstrap JS Bundle Removal)**: Injected `bootstrap.bundle.min.js` `<script>` tag into `templates/unmatched.html`.
  - *Result*: RED in `tests/test_template_shell.py::test_a_migrated_page_loads_no_bootstrap_javascript[unmatched.html]` (`AssertionError: unmatched.html still loads Bootstrap JS`).
  - *Restoration*: Removed script -> GREEN (8 passed).
- **Mutest 5 (Upstream Failure Detection on reason_code -- F-B21-56)**: Reverted `_detect_spotify_total_failure` in `scrobblescope/orchestrator.py` to prose-only check (`reason == "No Spotify match"`).
  - *Result*: RED in `tests/services/test_orchestrator_helpers.py::test_detect_spotify_total_failure_bases_detection_on_reason_code` (`AssertionError: assert False is True`).
  - *Restoration*: Restored `reason_code == REASON_NO_SPOTIFY_MATCH` with legacy fallback -> GREEN (21 passed, including negative non-match check `test_detect_spotify_total_failure_does_not_fire_for_other_reason_codes`).
- **Mutest 6 (Event Loop Slot Release on Exception -- F-B21-1)**: Simulated `asyncio.set_event_loop` failure during loop setup.
  - *Result*: RED before fix in `tests/services/test_orchestrator_fetch_and_process.py::test_background_task_releases_slot_when_event_loop_setup_raises` and `tests/test_heatmap.py::TestHeatmapTask::test_release_job_slot_called_when_event_loop_setup_raises` (`RuntimeError: loop setup failed` without calling `release_job_slot()`).
  - *Restoration*: Moved loop creation inside `try...finally` in `background_task` and `heatmap_task` -> GREEN (all tests passed, slot unconditionally released).
- **Mutest 7 (Defensive Nested finally on loop.close Exception)**: Simulated `loop.close()` failure inside finally block.
  - *Result*: Verified that with sequential `if loop: loop.close(); release_job_slot()`, a failure in `loop.close()` would skip `release_job_slot()`. Wrapped in nested `finally: try: if loop: loop.close() finally: release_job_slot()`.
  - *Restoration*: Tests `test_background_task_releases_slot_when_loop_close_raises` and `test_release_job_slot_called_when_loop_close_raises` confirm `release_job_slot()` is called even when `loop.close()` raises.

## Deviations discovered during execution

1. **F-B21-56 -- stable-code follow-through.** The first commit introduced
   `reason_code` but left `_detect_spotify_total_failure` coupled to the English
   reason. The local follow-up checks `REASON_NO_SPOTIFY_MATCH` and keeps prose
   only as a legacy-job fallback.
2. **F-B21-1 -- worker slot cleanup.** Review of the touched album worker found
   that event-loop setup and close failures could skip `release_job_slot()`.
   The same worker invariant exists in `heatmap_task`, so both implementations,
   their adversarial tests, and both sequence diagrams move together. This is
   the intentional exception to the original heatmap-isolation statement.
3. **Audit-row enrichment.** The prepared report retains cover artwork,
   Spotify IDs, and Last.fm play counts already available at both unmatched
   producer sites. When cached album artwork is absent, the browser reuses the
   existing `/api/artist_spotlight` route with viewport deferral and a
   per-artist request cache. No new endpoint or dependency is introduced.
   Producer tests and the populated-report browser check own the contract.
4. **Commit boundary.** F-B21-1 and F-B21-56 are backend changes found after
   the backend commit. They cannot ship inside the independently revertible UI
   commit. On 2026-09-10 the owner authorized staging and committing; the
   non-rewrite path uses a separate fix commit before the UI commit.
5. **PR #231 Linux test setup.** The first Quality Gate passed pre-commit and
   then failed because two cleanup tests patched the Windows-only
   `asyncio.ProactorEventLoop` attribute unconditionally on Ubuntu. The tests
   now create that patch target when the platform does not expose it and close
   their test coroutine before forcing `loop.close()` to fail. Production code
   and UI rendering are unchanged.


- [x] **Step 5: Commit the authorized finding fix, then the remaining WP-7 UI**

```bash
git add templates/unmatched.html static/css/unmatched.css static/css/tailwind.css static/js/unmatched.js scrobblescope/orchestrator.py scrobblescope/heatmap.py tests/services/test_orchestrator_helpers.py tests/services/test_orchestrator_fetch_spotify.py tests/services/test_orchestrator_fetch_and_process.py tests/test_heatmap.py tests/test_template_shell.py scripts/dev/frontend_gate.py docs/architecture/top-albums-sequence.md docs/architecture/heatmap-sequence.md docs/superpowers/plans/2026-09-10-batch21-wp7-unmatched-page-and-reason-code.md BATCH21_DEFINITION.md FINDINGS.md PLAYBOOK.md .claude/SESSION_CONTEXT.md
git commit -m "feat(ui): rebuild unmatched page on tailwind"
```

The non-rewrite deviation fix committed as `ba5f9fe`; the UI commit completes
this step.

- [x] **Step 6: Review and commit post-commit cover containment**

Owner review of UI commit `968eaa0` exposed album covers expanding to intrinsic
table dimensions. The Tailwind theme declares no spacing steps 10 or 11, so the
template's `w-10`/`h-10` and desktop step-11 utilities emitted no CSS. Follow
the proven `results.css` pattern with explicit width, height, min/max bounds,
square aspect ratio, and `object-fit: cover`; retain the design's 40px mobile /
44px desktop list artwork and 4px radius. The populated-report browser check is
the regression seam. The owner approved the remedy and authorized publication
to `origin/test` on 2026-09-10.

- [x] **Step 7: Repair PR #231 cross-platform cleanup tests**

GitHub Actions run `34542763317` reported `2 failed, 984 passed` after its
pre-commit step passed. Both failures occurred while patching
`asyncio.ProactorEventLoop`, which is available on Windows but absent on the
Ubuntu runner. Use `create=True` for that platform-specific patch target in
both cleanup tests and close the coroutine consumed by the mocked loop. The
focused tests must pass both normally and with the attribute removed from the
local process; then run the complete repository gates before publication.

---

## Plan Self-Review

1. **Spec Coverage:**
   - Stable `reason_code` (`release_scope`, `no_spotify_match`) in `orchestrator.py`: Covered by Task 2.
   - `routes.py` grouping by code while preserving prose detail: Covered by Task 1 (`scrobblescope/unmatched.py`) and Task 3 (`routes.py`).
   - Heatmap JavaScript isolation: preserved. The bounded `heatmap.py` cleanup
     change is recorded as the F-B21-1 deviation and covered adversarially.
   - Two reason cards with human copy, top offenders + expander: Covered by Task 4 (`templates/unmatched.html`, `static/js/unmatched.js`).
   - Leaderboard-styled rows, 9px mono fix line: Covered by Task 4 (`templates/unmatched.html`).
   - Removal of Bootstrap JS bundle and legacy CSS: Covered by Task 4 (`unmatched.html`), Task 5 (`tests/test_template_shell.py`, `scripts/dev/frontend_gate.py`).
   - Rollback boundaries maintained: Task 3 is the backend contract, deviation
     fix `ba5f9fe` is separate, and Task 5 is the UI commit.

2. **Placeholder Scan:**
   - No `TODO`, `TBD`, or vague instructions exist. All code snippets are concrete, copy-pasteable, and syntactically valid.

3. **Type Consistency:**
   - `group_unmatched_albums` produces `(sorted_groups, counts, metadata)` used consistently across Task 1, Task 3, and Task 4.
   - Reason constants `REASON_RELEASE_SCOPE` and `REASON_NO_SPOTIFY_MATCH` declared in Task 1 and consumed in Tasks 1, 2, 3.
