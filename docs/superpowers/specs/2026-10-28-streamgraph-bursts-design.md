# Streamgraph burst layers, hidden-artist tooltip and rocket palette -- design

> Historical direction superseded by the owner's 2026-10-28 context-halo plan.
> Earlier decisions below are retained as project history.

Date: 2026-10-28. Status: approved by the owner in brainstorming (all three parts "Looks right"); to be
committed as `docs/superpowers/specs/2026-10-28-streamgraph-bursts-design.md` on its own branch off `main`,
a separate PR after #279. Continues the handoff's deferred "Everything else band" item (ruling U35).

## Problem

The heatmap's listening streamgraph shows the 10 artists with the most plays in the last 365 days and
pools every other artist into "Everything else". An artist heard heavily for a few weeks and little
otherwise never reaches the top 10, so the weeks they dominated read as a large grey band. Owner's case:
Cameron Winter, 206 plays in the window (rank 17), most of them between 11 and 17 October 2026, is
invisible inside "Everything else" for that week. The current palette (Tailwind steps) also leaves the
ends of the warm ramp unused. This motivating example does not guarantee a burst slot for that artist;
the measured ranking below determines selection.

## Decisions (owner, 2026-10-28, verbatim where quoted)

- The window stays the last 365 days ending today, never a calendar year ("it distorts data -- especially
  if it were the beginning of a year"). This is already how `heatmap.py` builds the window.
- 12 layers: "We could realistically do 12 artists" -- 10 by window total plus 2 burst slots.
- Burst slots are fixed for the whole chart: "Fixed: 2 biggest bursts". Both are always filled when there
  are hidden artists ("Always fill both").
- Bursts are measured on a rolling 21-day window of daily plays, so listening that runs from a Wednesday
  into the next week's Tuesday is one burst (the owner's boundary concern).
- Tooltip: no indentation; "a horizontal rule ... below the top artists, and then keep the three below
  it. That horizontal divider should only show when the extra artists appear."
- Palette: rocket, sampled more widely than now, assigned out of order "so it doesn't blend".

## Part 1 -- selection (server, `scrobblescope/plays.py`)

- `aggregate_weekly_artist_counts` keeps its window, week grid, artist key (`normalize_name(artist,
  "")[0]`) and top-10 ranking (window total descending, tie on key) unchanged.
- From the artists outside the top 10, the 2 with the largest maximum play count over any 21 consecutive
  days in the window become burst layers (tie: larger window total, then key). Fewer candidates mean
  fewer burst layers; a user with 11 artists gets 11 layers and an empty "Everything else".
- Computing the peak walks each artist's sorted play dates once with a sliding window (one sorted walk
  per artist), never artists x days. Selection and the hidden list below come from the same single pass
  over the plays, in the same function.
- A burst layer carries the full weekly counts across the 365-day window like any layer. Counts are
  not clipped to its selected 21-day peak; it is zero and takes no vertical space only in weeks with
  no plays. The payload carries no `burst` flag (nothing reads it; a layer past the top 10 is a burst
  layer). The key and tooltip render burst layers exactly like the others.
- New payload field: for each week, the 3 largest artists still inside "Everything else" after the 12
  layers are removed, as name and count, largest first (tie on key); fewer when fewer exist. Empty-key
  plays stay in the "Everything else" total and are never listed by name.
- Payload shape stays backward compatible for the existing fields (`weeks`, `artists`, `other`).
- The job store's read view (`scrobblescope/jobs.py`, `_context_view`) copies the new field through to
  the browser (a copy callers may mutate); a payload stored without it stays without it.

## Part 2 -- tooltip (`static/js/heatmap.js`)

- Rows as now: one per layer with plays that week (up to 12), then "Everything else" with its count.
  Keyboard positions follow those visible rows, including after pointer activity or a week change.
- When the week's hidden-artist list is non-empty: a horizontal rule, then up to three rows, one per
  hidden artist, name and count, in the same alignment as the rows above (no indentation, no new
  horizontal space; an empty swatch-width spacer stands where the layer rows have a colour swatch, so
  names and counts line up). No rule and no rows when the list is empty.
- The rule uses the existing `--stream-muted` token, chosen by the owner on 2026-10-28 for its higher
  contrast against the panel (see the plan's Task 3). No new token is added.
- The panel's existing size cap, ellipsis and side choice apply to the new rows. The current page-flow
  and internal-scroll contract is owned by the [live-review design](2026-10-28-streamgraph-live-feedback-design.md).

## Part 3 -- palette (`static/js/heatmap.js`)

- 12 colours sampled at even steps from seaborn's rocket colormap (`seaborn/cm.py`, `_rocket_lut`, at the
  pinned tag v0.13.2), per theme: the dark theme over 28%-90% of the ramp, the light theme over 15%-78%
  (owner, 2026-10-28). The extremes are excluded because rocket's darkest step matches the dark theme's
  background and its lightest the light theme's. Defined once, as two 12-colour arrays in `heatmap.js`
  (the palette's one owner), not as CSS tokens.
- Colours are assigned by a fixed permutation of the 12 steps so bands that touch in the stack are at
  least 3 steps apart, whichever of the two burst layers is larger. The current residual geometry and
  numeric-row contract is owned by the [live-review design](2026-10-28-streamgraph-live-feedback-design.md).
- Contrast: the stream-fill exemption (rulings U20, S13/S14) stands; both themes are checked against the
  stream frame (light min 1.89, max 12.66; dark min 1.59, max 10.83) and the numbers are shown to the
  owner.

## Verification

- The real flounder14 payload (window ending 2026-10-28) is rendered with the new selection, tooltip
  and palette, with Firefox screenshots in both themes, including the weeks covering 11-17 October.
  Owner sign-off precedes PR publication; the owner authorized atomic checkpoint commits before
  prototype approval on 2026-10-28. The prototype renders the real task patches.
- The prototype independently recomputes the top ten by window total and the two largest rolling
  21-day peaks among the remaining artists, with the specified tie rules, and compares the selected
  names with the job-store readback. The owner reaffirmed this top-ten-plus-two rule on 2026-10-28;
  no named artist is guaranteed a slot.
- Unit tests (lean suite, one per behaviour, parametrized): a burst crossing a Monday is found; the top 10
  are unchanged; a sparse fixture retains zero counts in weeks with no plays, while each selected
  artist keeps its full weekly history; fewer than 12 artists; the 3 hidden artists per week and their
  order; empty-key plays never named; the job store passes the hidden list through as a copy.
- Browser gate: the tooltip's rule and hidden rows appear only for a week with hidden artists (which also
  proves the field survives the job store); the existing streamgraph checks still pass.

## Out of scope

Rotating burst slots; a separate burst view; changing the heatmap grid's colours; mobile streamgraph work
(U18); the pause-button placement fix (its own PR).
