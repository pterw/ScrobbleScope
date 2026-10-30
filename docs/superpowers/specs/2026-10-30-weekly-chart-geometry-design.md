# Weekly chart geometry design

## Decision and authority

The owner selected the weekly chart geometry proposal on 2026-10-30 and
approved the in-file design below. This is a side task before Batch 23 WP-1,
not a new batch work package. The implementation plan is
[the weekly chart geometry plan](../plans/2026-10-30-weekly-chart-geometry.md).

The owner explicitly approved a bounded exception to
[global-rules.md, Rule 3](../../agents/global-rules.md#3-the-rule-of-three-duplication-buffer):
the two established compositions are the production renderer and its test.
The exception permits this chart-specific encapsulation. It does not permit
a generic chart framework or sharing provider-specific logic.

The owner also approved a clean worktree from `origin/main`, with WT003
advisory for the side-task branch, and requested one independent review
after the definition of done rather than review after each atomic commit.
No other validation gate is waived.

## Problem

`drawStream` in `static/js/heatmap.js` orders the artists, builds their
baseline, fits and stacks their counts, derives safe smoothing segments,
and projects the artist and halo paths. A test reconstructs this sequence
with different coordinates and no endpoint extension. The calculation the
test exercises can therefore differ from what the renderer draws.

Pointer selection also knows the stack's coordinate system and rank map.
Keeping that representation private lets drawing and selection use one
calculation without teaching either caller the internal protocol.

## Interface

Keep the pure module inside the existing `heatmap.js` closure, adjacent to
the mathematical helpers. A separate asset would add script ordering,
global naming and fixture-loading obligations without a present consumer
that needs them.

```js
streamGeometry(validPayload) // null, or:
{
  xs,                         // week centres in SVG viewBox coordinates
  haloPath,                   // existing SVG path serialization
  artists: [{ rank, path }],   // existing bottom-to-top drawing order
  hitAt(x, y)                 // -> { week, hoverId }
}
```

`hitAt` takes SVG viewBox coordinates with downward-positive y. It closes
over the numeric stack, centre-line conversion and artist rank map. These
values are implementation details, not returned fields. Returned arrays
are treated as read-only; construction does not mutate the payload.

The existing payload validator remains the caller's prerequisite. There is
no second normalization, exception or recovery policy. A chart with no
positive fitted extent returns `null`; positive residual-only data still
has a halo and no artist paths.

DOM creation, theme colours, labels, event binding, panel content,
week-specific keyboard rows and SVG export cloning keep their current
owners. `drawStream` paints the returned paths. The pointer handler only
converts browser coordinates to viewBox coordinates before calling
`hitAt`. The existing geometry helpers may remain internal seams for
independent mathematical tests.

## Compatibility

The [approved context-halo plan](../plans/2026-10-28-streamgraph-context-halo.md)
owns the chart behavior. This refactor preserves its ordering, common fit,
halo calculation, visibility control, calendar alignment and saved image.
Do not copy or amend those product decisions here.

For a given valid payload, the artist path order, ranks and serialized
path strings, including endpoint extension, remain identical. Hit selection
keeps nearest-week rounding and clamping, sampled-week bands rather than
curve containment, upper-band ownership at shared edges, zero-band
exclusion and `null` outside named artists. The residual halo does not
become a pointer-selectable artist.

No new dependency, backend change, template loading contract, new chart
framework or user-visible design change belongs to this task.

## Verification and definition of done

1. Before moving production calculation, extend existing coverage for
   rendered adversarial spikes and the exact horizontal midpoint. Verify
   those checks against the current implementation.
2. Replace the reconstructed composition test with the production geometry
   interface. Its independent enclosure and clipping assertions remain.
   The test parser must accept production endpoint-extension commands.
3. Cover the new interface's ordering, hit selection, nonmutation and
   no-play/residual-only behavior. Keep independent mathematical oracles;
   remove an old hook only when its behavior has equivalent coverage.
4. Compare actual path strings and representative pointer results before
   and after the refactor with deterministic seeded results. Do not add a
   permanent second implementation as an oracle.
5. Run the full tracked suite, the complete frontend gate across its device
   profiles, all hooks and final docsync. Inspect Chromium and Firefox.
6. Complete one independent whole-branch standards/spec review after the
   preceding items. Resolve material findings and verify fixes.
7. Open a PR against `main` using the repository PR template, with truthful
   task state and validation evidence at the pushed head. Do not merge it.

## Alternatives considered

- A separate classic script or ES module adds asset-loading work and
  changes the disk-loaded test fixture. There is no second production asset
  that needs this calculation, so keep the current closure.
- Returning raw bands with a separate hit helper exposes the fitted stack
  and its coordinate conversion. Closing over that state gives the current
  caller a smaller interface.
- A configurable rendering framework would solve hypothetical variation.
  This calculation has pure in-process dependencies and needs no adapter.
