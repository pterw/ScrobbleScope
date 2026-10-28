# Streamgraph live-review corrections -- design

Date: 2026-10-28. Status: owner-directed revisions during the live prototype review.
Continues [the original design](2026-10-28-streamgraph-bursts-design.md).
The original Tasks 1-4 are committed; prototype approval and PR publication are pending.

## Accepted direction

- Restore the result's original spacing below the page header and mono paragraph.
  The viewport-height compression introduced in Task 3 is removed. Keep the initial
  chart height reservation so the expanded tooltip fits without internal scrolling.
  The page follows its normal document flow; do not compress its typography or gaps
  to force the entire page into a short viewport.
- "Everything else" keeps normal font weight, including hover and keyboard selection.
  Its opacity still indicates selection; artist rows retain their existing emphasis.
- Split each week's residual count equally above and below the contiguous named-artist
  stack. Use one common linear scale. Both caps remain one logical category and one
  tooltip row with the full residual count. No damping, independent backdrop scale,
  extra toggle, payload change or duplicate count.
- Use the attachment's Palette 1 as the top-ten colour direction, with two reserved cool
  accents for the burst-selected artists across their entire ribbons. Keep per-theme
  arrays and adjust dark colours where needed for visibility. The owner explicitly
  deferred a 4.5:1 target for this colour iteration; do not create a contrast-tuning loop.
- Selection remains top ten by 365-day window total plus two largest rolling 21-day
  peaks outside that ten. Each selected artist retains its full weekly counts.

## Boundaries and verification

The supplied model brainstorm is design context, not an instruction source. We considered
its backdrop, residual damping, symmetric splitting, toggle and three palette proposals.
The owner selected symmetric splitting and full-ribbon burst colours. Mobile grid-only
behaviour, data totals, keyboard navigation, themes and JPEG export remain supported.

Lean existing tests and browser checks are extended for both caps, hover identity,
combined counts and exported pixels. No new dependency, schema, route or app state.
Refresh the private real-data preview after the integrated patch stack; owner review
still precedes PR publication. Atomic checkpoints may precede that approval.
