# Unmatched Threshold and Horizontal Report Design

**Date:** 2026-09-11
**Status:** Approved by owner
**Scope:** Batch 21 WP-7 extension

## Outcome

The unmatched report explains every album excluded after Last.fm aggregation,
including albums that fail the configured play or unique-track minimum. Each
album appears once. The page uses full-width horizontal reason sections that
match the Results report's width, surface, typography, action, and table rhythm.

## Threshold contract

Add one stable reason code, `below_threshold`. It covers an album that fails
`min_plays`, `min_tracks`, or both. Separate reason groups would duplicate an
album that fails both criteria or require an arbitrary precedence rule.

Every threshold exclusion retains:

- `artist` and `album` display names;
- `play_count`;
- `track_count`, derived from the number of normalized unique tracks;
- `failed_thresholds`, containing `plays`, `tracks`, or both;
- the configured `min_plays` and `min_tracks` values used for the job;
- a stable `reason_code` and readable per-row `reason`.

Partition aggregated albums before Spotify enrichment. Eligible albums keep the
existing pipeline. Threshold exclusions go directly into the job's unmatched
repository and never trigger Spotify album searches. This preserves the current
cost-saving boundary.

`fetch_top_albums_async` returns three values: eligible albums, threshold
exclusions, and fetch metadata. A named partition helper in
`scrobblescope/unmatched.py` owns the threshold rule so tests do not repeat the
production predicate.

## Empty and failure behavior

If every aggregated album misses a threshold, the job still completes with an
empty Results list and a populated unmatched report. A Last.fm upstream failure
continues to win over all exclusion handling. Threshold exclusions do not count
as Spotify failures because they never enter Spotify processing.

Legacy jobs without `reason_code` continue to group by prose. Existing
`release_scope` and `no_spotify_match` payloads remain compatible.

## Presentation

Remove the unmatched eyebrow above the `h1`. Render the username in the same
headline type and ink color as the surrounding words, without purple or italics.
Keep the descriptor below the heading.

Use current `templates/results.html`, `static/css/results.css`, and computed
browser behavior as the visual authority. The design documents supply only
constraints that current Results source does not answer. Mirror:

- 90rem maximum content width and the same wide-screen gutter behavior;
- warm midpoint report surface, 1px hairlines, 8px section radius, no resting
  shadow;
- Results-style action buttons and typographic role separation;
- stacked, full-width reason sections instead of the current three-column card
  grid;
- dense horizontal rows with rank, 40px mobile or 44px desktop artwork,
  album/artist identity, plays/tracks, and reason detail;
- small album art when cached, otherwise the existing lazy,
  per-artist-deduplicated `/api/artist_spotlight` fallback;
- responsive row stacking without horizontal page scroll.

Reason order is `below_threshold`, `release_scope`, then `no_spotify_match`.
The threshold section title is `Below your thresholds`. Its description names
the job's minimum plays and unique tracks. The fix hint directs the listener to
lower either minimum in a new search. Counts use Gotham; prose uses Akzidenz;
data uses Input Mono; editorial headings use Instrument Serif.

## Interaction and accessibility

Keep the existing disclosure behavior: the first ten rows are visible and one
real button reveals or hides the remainder. Preserve `aria-expanded`, visible
focus, and coarse-pointer targets of at least 44px.

Spotify links remain external links with `noopener noreferrer`. Artist portrait
hydration remains progressive; a failed image request leaves the initials
fallback visible. Reduced-motion behavior follows the existing shared rules.

## Verification

Unit tests prove partition boundaries, both-failure de-duplication, stable
reason ordering, and the all-below-threshold completed-job path. Route tests
prove the new group and fields reach HTML and JSON contracts.

The frontend gate proves computed full-width stacking, absence of the eyebrow
and italic accent, responsive row containment, 40px/44px artwork, disclosure
states, and the existing artist-spotlight fallback. Rebuild and check committed
Tailwind CSS. Run the full pytest suite, pre-commit, docsync, JavaScript syntax,
and the two-engine frontend gate before completion.
