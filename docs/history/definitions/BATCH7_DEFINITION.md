# Batch 7: Persistent metadata layer (performance and cost)

Status: **Complete**
Archived from `PLAYBOOK.md` Section 4 on 2026-02-22.

---

Purpose:
- Reduce repeated Spotify lookups across cold starts and users.

Recommended architecture:
- Durable store first (Postgres preferred on Fly).
- Optional Redis as a hot cache in front.

Data model (minimum):
- `artist_norm`
- `album_norm`
- `spotify_id`
- `release_date`
- `album_image_url`
- `track_durations_json`
- `updated_at`

Lookup flow:
1. Check durable metadata store by normalized key.
2. Hit -> return immediately.
3. Miss -> call Spotify -> persist -> return.

Concerns:
- Validate Spotify API terms for metadata persistence.
- Add TTL or refresh policy to avoid stale data.

Acceptance:
- Repeat queries show reduced Spotify calls and latency.
- Cold-start behavior improved over time.
