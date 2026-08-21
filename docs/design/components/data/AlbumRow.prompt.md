The results list. Stack rows directly — no wrapping table, no zebra striping.

```jsx
<AlbumRow rank={1} title="Cascade" artist="Floating Points" value="247" meta="2025-03-14" href="https://open.spotify.com/album/…" coverIndex={1} />
```

Notes
- The value column is right-aligned mono so digits line up down the list; that alignment is the whole reason the leaderboard reads faster than the old table.
- Titles link to Spotify when `spotify_id` exists and are plain text otherwise — never render a dead link.
- Placeholder covers are muted two-tone washes, deliberately not the purple accent.
