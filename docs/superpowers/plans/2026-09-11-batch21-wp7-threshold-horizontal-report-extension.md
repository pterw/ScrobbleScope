# Batch 21 WP-7 Threshold and Horizontal Report Extension Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retain albums that miss either eligibility threshold under one stable reason code and rebuild the unmatched report as full-width horizontal sections that mirror the current Results implementation.

**Architecture:** Partition aggregated Last.fm albums before Spotify enrichment. Return eligible and threshold-excluded mappings separately, persist exclusions through the existing job repository, and keep Spotify cost unchanged. The unmatched template directly reuses Results stylesheet classes and scale variables where their semantics match; `unmatched.css` owns only page-specific row and category behavior.

**Tech Stack:** Python 3.13, Flask, Jinja2, Tailwind CSS v4, daisyUI v5, vanilla JavaScript, Playwright, pytest.

## Global Constraints

- Current `templates/results.html`, `static/css/results.css`, and their computed browser output are the visual authority; dated design documents are secondary.
- Use one stable `below_threshold` reason. An album that fails both minimums appears once.
- Preserve exact play and unique-track counts and the failed-threshold list.
- Threshold exclusions never enter Spotify search or batch enrichment.
- Keep the existing `/api/artist_spotlight` lazy fallback for rows without cached album art.
- Remove the unmatched eyebrow above `h1`; render its username without purple or italics.
- Use full-width stacked reason sections, Results width/scale/surface/action/table conventions, 1px hairlines, and no resting shadow.
- Spacing and type use `rem`; fine borders, outlines, and radii use `px`.
- Coarse-pointer controls remain at least 44px on their smaller side.
- No new dependency and no weight 500 or 600.
- Use the qualified primary-checkout Python, pytest, and pre-commit paths.
- Update the active definition, original WP-7 plan, PLAYBOOK, and SESSION_CONTEXT with each commit.

---

### Task 1: Partition and store threshold exclusions

**Files:**
- Modify: `scrobblescope/unmatched.py`
- Modify: `scrobblescope/orchestrator.py`
- Modify: `tests/test_unmatched.py`
- Modify: `tests/services/test_lastfm_logic.py`
- Modify: `tests/services/test_orchestrator_fetch_and_process.py`
- Modify: `tests/test_routes.py`

**Interfaces:**
- Produces: `REASON_BELOW_THRESHOLD = "below_threshold"`
- Produces: `partition_albums_by_threshold(albums, min_plays, min_tracks) -> tuple[dict, dict]`
- Changes: `fetch_top_albums_async(...) -> tuple[dict, dict, dict]`, returning eligible albums, threshold exclusions, and fetch metadata.
- Persists: one unmatched payload per excluded album through `add_job_unmatched`.

- [ ] **Step 1: Write failing partition tests**

Add tests that exercise play-only, track-only, both-failure, and exact-boundary albums:

```python
def test_partition_albums_by_threshold_keeps_each_exclusion_once():
    albums = {
        ("artist", "both low"): {
            "original_artist": "Artist",
            "original_album": "Both Low",
            "play_count": 7,
            "track_counts": {"one": 4, "two": 3},
        },
        ("artist", "eligible"): {
            "original_artist": "Artist",
            "original_album": "Eligible",
            "play_count": 10,
            "track_counts": {"one": 4, "two": 3, "three": 3},
        },
    }

    eligible, excluded = partition_albums_by_threshold(albums, 10, 3)

    assert list(eligible) == [("artist", "eligible")]
    assert list(excluded) == [("artist", "both low")]
    item = excluded[("artist", "both low")]
    assert item["reason_code"] == REASON_BELOW_THRESHOLD
    assert item["failed_thresholds"] == ["plays", "tracks"]
    assert item["play_count"] == 7
    assert item["track_count"] == 2
```

- [ ] **Step 2: Run the partition tests and confirm RED**

Run the named tests with qualified pytest. Expected: import failure for
`REASON_BELOW_THRESHOLD` or `partition_albums_by_threshold`.

- [ ] **Step 3: Implement the pure partition contract**

Add the constant and category metadata, then implement one pass over the
aggregated mapping. Copy only display and threshold facts into exclusions;
leave `track_counts` on eligible albums for the existing Spotify pipeline.

```python
failed_thresholds = []
if play_count < min_plays:
    failed_thresholds.append("plays")
if track_count < min_tracks:
    failed_thresholds.append("tracks")
```

Use the stable category order:

```python
order = [REASON_BELOW_THRESHOLD, REASON_RELEASE_SCOPE, REASON_NO_SPOTIFY_MATCH]
```

- [ ] **Step 4: Make the fetch boundary explicit**

Replace the filtering comprehension in `fetch_top_albums_async` with the
partition helper and return:

```python
return eligible_albums, threshold_exclusions, fetch_metadata
```

Add `albums_below_threshold` to the existing stats mapping. Update every test
unpacking this function; do not add a compatibility branch that accepts both
tuple shapes.

- [ ] **Step 5: Persist exclusions after Last.fm success**

In `_fetch_job_albums`, unpack all three values. Check upstream status first.
Then call `add_job_unmatched(job_id, f"{artist_key}|{album_key}", item)` once
for every threshold exclusion before handling the eligible-empty case. This
ensures an all-below-threshold job completes with empty Results and a populated
unmatched report.

- [ ] **Step 6: Prove the pipeline behavior**

Add tests that assert:

- Last.fm errors do not persist threshold exclusions;
- an all-below-threshold fetch writes one completed empty result and one
  unmatched item;
- the unmatched item carries actual counts and never enters Spotify processing;
- the Results unmatched count includes the threshold exclusion.

Run `tests/test_unmatched.py`, `tests/services/test_lastfm_logic.py`, the named
orchestrator tests, and the affected route tests. Expected: PASS.

- [ ] **Step 7: Update batch state and commit Task 1**

Record the backend extension in the active WP-7 Section 4 entry, run docsync
fix, full pytest, all pre-commit hooks, docsync check, and diff check. Stage
only the named backend, test, and document files.

Commit:

```text
feat(unmatched): Retain below-threshold albums
```

---

### Task 2: Mirror Results with horizontal unmatched sections

**Files:**
- Modify: `templates/unmatched.html`
- Modify: `static/css/unmatched.css`
- Modify: `static/js/unmatched.js`
- Modify: `static/css/tailwind.css`
- Modify: `scripts/dev/frontend_gate.py`
- Modify: `tests/test_routes.py`
- Modify: `tests/test_template_shell.py`

**Interfaces:**
- Consumes: `below_threshold`, its structured counts, existing reason metadata, and Results' current CSS variables/classes.
- Preserves: `.unmatched-expander-btn`, `.unmatched-overflow`, `[data-artist-image]`, and `/api/artist_spotlight` hydration.
- Produces: stacked `.unmatched-group` sections and `.unmatched-thresholds` row values.

- [ ] **Step 1: Add RED route and browser assertions**

Require the populated page to have no element before `h1` inside the headline
block, no italic or primary-color username class, and reason order
`below_threshold`, `release_scope`, `no_spotify_match`. Extend the frontend
fixture with one threshold item failing both limits and assert it renders once
with `7 plays / 2 tracks`.

Require every reason section to occupy the report content width at desktop,
artwork to compute to 44px desktop and 40px mobile, and the page to have no
horizontal overflow at the narrow profile.

- [ ] **Step 2: Rewrite the masthead from current Results source**

Use the same flex breakpoint, bottom alignment, margin rhythm, headline sizes,
and toolbar grid as `templates/results.html`. Remove the eyebrow entirely.
Keep the descriptor below `h1`. The unmatched username is a normal span using
the surrounding serif and ink color.

- [ ] **Step 3: Reuse Results composition classes**

Load `results.css` before `unmatched.css`. Give the main element both
`results-page` and `unmatched-page`. Use `results-action`,
`results-toolbar-action`, `results-filter-bar`, `results-table-wrapper`, and
`results-table` only where their current semantics match.

In `unmatched.js`, apply the same current Results scaling calculation to the
shared `--results-scale` and `--results-base-rem` variables on the unmatched
main element. Do not change `results.js` in this task.

- [ ] **Step 4: Replace the card grid with stacked horizontal sections**

Render one full-width section per reason. Remove category badges and the
three-column span logic. Each section header contains title/description on the
left and the Gotham album count on the right.

Use four table columns: rank, album and artist, plays/tracks, and reason detail.
The threshold metric uses `play_count` and `track_count`; existing categories
show play count plus their existing detail. Keep the 10-row expander and lazy
portrait markup.

- [ ] **Step 5: Author only unmatched-specific CSS**

Keep Results' width, surface, action, and table rules authoritative. Add only
stack spacing, four-column budgets, threshold metric styling, the 40px/44px
art override, and narrow-screen row containment. Use Results' midpoint surface
and 8px radius; remove the old 14px card radius and all resting shadows.

- [ ] **Step 6: Rebuild and verify the frontend**

Run the qualified Tailwind build, `node --check static/js/unmatched.js`, the
route/template tests, the focused unmatched browser check in Chromium, and the
complete frontend gate across Chromium and Firefox. Inspect computed width,
scale, surface, headline, artwork, row overflow, and both expander states.

- [ ] **Step 7: Update batch state and commit Task 2**

Record the UI extension and fresh evidence in PLAYBOOK, run docsync fix, full
pytest, all hooks, docsync check, Tailwind drift check, and diff check. Stage
the named UI, generated CSS, gate, tests, and document files only.

Commit:

```text
fix(ui): Align unmatched report with Results
```

---

## Plan Self-Review

1. **Spec coverage:** Task 1 covers retention, de-duplication, structured facts,
   Last.fm failure precedence, and Spotify cost isolation. Task 2 covers the
   Results-source hierarchy, horizontal layout, neutral username, artwork
   fallback, accessibility, and rendered verification.
2. **Placeholder scan:** no TODO, TBD, deferred implementation instruction, or
   undefined helper remains.
3. **Type consistency:** `partition_albums_by_threshold` returns two mappings;
   `fetch_top_albums_async` returns those two mappings plus metadata; the job
   repository receives the exclusion payload unchanged; the template reads the
   exact `play_count`, `track_count`, and `failed_thresholds` names.
