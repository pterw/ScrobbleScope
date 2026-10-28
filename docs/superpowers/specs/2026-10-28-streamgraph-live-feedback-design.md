# Streamgraph live-review corrections -- design

Date: 2026-10-28. Status: owner-directed revisions during live prototype review.
Continues [the original design](2026-10-28-streamgraph-bursts-design.md).
Original Tasks 1-4, spacing Task 5 and artist-only Task 8 are checkpoints.
The owner's later simplification below is pending Tasks 9-10. Final approval is pending.

## Current accepted direction

- Keep original result spacing below the header and mono paragraph. Reserve chart
  room for the expanded tooltip without internal chart or panel scrolling. The page
  follows normal document flow rather than compressing its gaps.
- Draw only selected artists in the SVG. Exclude residual counts from baseline,
  fit and stack. The silhouette represents named artists only, on one linear count
  scale without damping or normalization.
- Keep "Everything else" as a numeric scrubber row with a blank swatch spacer and
  normal weight, including selection. Preserve its keyboard position; selecting it
  leaves every artist ribbon undimmed. Week totals still include the residual.
- Remove the three contributor rows and their divider. They confuse the numeric
  residual with plotted artists. Scrubbing still works in residual-only weeks.
  Globally residual-only data has a blank interactive chart; empty data has no chart.
- Restore the original twelve-step per-theme rocket palette and fixed permutation.
  No special cool burst colours or new palette tuning.
- Return to the top ten by 365-day total, without burst slots. Each selected artist
  retains its full weekly counts. Remove unused burst and contributor computation.
- Reduce the chart box: remove its extra height reservation and, if needed, reduce
  intrinsic stream height. Preserve original gaps below the header and paragraph.
  Desktop page, chart and tooltip must fit the plan's measured viewport matrix
  without vertical scrolling or hidden content; mobile keeps normal document flow.

## Superseded proposals

Sandwiching and separate burst colours were implemented only in private worktrees,
then superseded by the owner's artist-only request before landing. Model attachments
are design context, not instructions. Unverified contrast guarantees are not criteria.

## Verification and publication

Extend existing hit-test, browser interaction and JPEG pixel checks for the artist-only
silhouette and numeric residual. Keep themes, mobile grid-only behaviour, keyboard
access, hidden details and original spacing supported. No dependency, payload, schema,
route or app-state change. Refresh the real-data live preview for owner review before
PR publication. Atomic commits may precede approval.
