# Results Artist Spotlight Rotation Design

**Date:** 2026-09-06
**Status:** Approved by owner
**Scope:** Results side rail only

## Contract

Aggregate the filtered album results by artist and rank artists by total
scrobbles. Take the top ten, then choose five unique artists with a deterministic
job-ID seed. A reload of the same completed job therefore keeps the same sample
and order. If fewer than five artists are available, use every artist.

Each candidate carries its display name, aggregate scrobbles, charted album
count, aggregate listening time, and the first available album image as a
server-rendered fallback.

## Request and rotation flow

Do not add work to album enrichment or the Heatmap pipeline. Render Results
first, then issue one existing `/api/artist_spotlight` request for each of the
five candidates concurrently. Merge a successful artist portrait and Spotify
profile URL into that candidate; retain its fallback data on failure.

Rotate the card every seven seconds. The five records live in the page, so
rotation makes no further requests. Pause changes while the document is hidden.
When `prefers-reduced-motion: reduce` matches, hydrate the first record but do
not start automatic rotation.

## Race rules

- A response may update only the candidate slot whose artist name it captured.
- A hydrated slot may repaint only when that slot is still active.
- Each image load carries a revision; an older load cannot hide or replace the
  current image.

## Presentation

Use the existing Results spotlight structure, Tailwind utilities, and fade.
Add no CSS rules. Show the rotation position as `01 / 05`. Hide the Spotify
link until an artist-profile URL is available; never label an album URL as an
artist destination.

## Verification

Route coverage proves aggregate top-ten eligibility, five unique selections,
and reload stability. The real browser gate proves five post-render hydration
requests and a card-index change in Chromium and Firefox. A sensitivity run
with the production interval disabled must fail the rotation assertion.
