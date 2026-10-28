# Streamgraph live-review corrections -- design

Date: 2026-10-28. Status: owner-directed revisions during live prototype review.
Continues [the original design](2026-10-28-streamgraph-bursts-design.md).
Original Tasks 1-4 and spacing Task 5 are committed. Prototype approval is pending.

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
- Preserve the three hidden-artist rows below the conditional divider. Scrubbing
  works in residual-only weeks. Globally residual-only data has a blank interactive
  chart; an entirely empty payload has no chart.
- Restore the original twelve-step per-theme rocket palette and fixed permutation.
  No special cool burst colours or new palette tuning.
- Selection remains top ten by 365-day total plus two largest rolling 21-day peaks
  outside that ten. Each selected artist retains its full weekly counts.

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
