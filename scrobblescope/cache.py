import asyncio
import json
import logging
import os

try:
    import asyncpg
except ImportError:
    asyncpg = None

from scrobblescope.config import METADATA_CACHE_TTL_DAYS


async def _get_db_connection():
    """Open a single asyncpg connection from DATABASE_URL, or return None.

    Returns None (with a debug log) if DATABASE_URL is unset, asyncpg is
    unavailable, or the connection attempt fails.  The caller is responsible
    for closing the returned connection.

    To smooth over Fly Postgres wake-up races, connection attempts use a small
    exponential backoff before giving up.
    """
    if asyncpg is None:
        return None
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        return None
    max_attempts = max(1, int(os.environ.get("DB_CONNECT_MAX_ATTEMPTS", "3")))
    base_delay_seconds = float(os.environ.get("DB_CONNECT_BASE_DELAY_SECONDS", "0.25"))
    for attempt in range(1, max_attempts + 1):
        try:
            conn = await asyncpg.connect(dsn)
            return conn
        except Exception as exc:
            if attempt >= max_attempts:
                logging.warning(
                    "DB connection failed after %s attempts (cache disabled): %s",
                    max_attempts,
                    exc,
                )
                return None
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logging.warning(
                "DB connection attempt %s/%s failed: %s. Retrying in %.2fs.",
                attempt,
                max_attempts,
                exc,
                delay,
            )
            await asyncio.sleep(delay)


async def _batch_lookup_metadata(conn, keys):
    """Look up cached Spotify metadata for a batch of (artist_norm, album_norm) keys.

    Executes a single SELECT using unnest() for efficient batch lookup.
    Only rows updated within the configured TTL are returned.
    Returns a dict keyed by (artist_norm, album_norm) with plain-dict values.
    """
    if not keys:
        return {}
    artists = [k[0] for k in keys]
    albums = [k[1] for k in keys]
    rows = await conn.fetch(
        """
        SELECT artist_norm, album_norm, spotify_id, release_date,
               album_image_url, track_durations
        FROM spotify_cache
        WHERE (artist_norm, album_norm) IN (
            SELECT unnest($1::text[]), unnest($2::text[])
        )
        AND updated_at > NOW() - make_interval(days => $3)
        """,
        artists,
        albums,
        METADATA_CACHE_TTL_DAYS,
    )
    result = {}
    for r in rows:
        td = r["track_durations"]
        if isinstance(td, str):
            td = json.loads(td)
        result[(r["artist_norm"], r["album_norm"])] = {
            "spotify_id": r["spotify_id"],
            "release_date": r["release_date"],
            "album_image_url": r["album_image_url"],
            "track_durations": td if td else {},
        }
    return result


async def _batch_persist_metadata(conn, rows):
    """Persist newly fetched Spotify metadata in a single INSERT statement.

    Uses INSERT ... SELECT FROM unnest() with ON CONFLICT DO UPDATE (upsert).
    Each element in *rows* is a tuple of (artist_norm, album_norm, spotify_id,
    release_date, album_image_url, track_durations_dict).
    """
    if not rows:
        return
    artists = [r[0] for r in rows]
    albums = [r[1] for r in rows]
    spotify_ids = [r[2] for r in rows]
    release_dates = [r[3] for r in rows]
    image_urls = [r[4] for r in rows]
    track_durations_json = [json.dumps(r[5]) if r[5] else "{}" for r in rows]
    await conn.execute(
        """
        INSERT INTO spotify_cache
            (artist_norm, album_norm, spotify_id, release_date,
             album_image_url, track_durations)
        SELECT * FROM unnest(
            $1::text[], $2::text[], $3::text[], $4::text[],
            $5::text[], $6::jsonb[]
        )
        ON CONFLICT (artist_norm, album_norm) DO UPDATE SET
            spotify_id      = EXCLUDED.spotify_id,
            release_date    = EXCLUDED.release_date,
            album_image_url = EXCLUDED.album_image_url,
            track_durations = EXCLUDED.track_durations,
            updated_at      = NOW()
        """,
        artists,
        albums,
        spotify_ids,
        release_dates,
        image_urls,
        track_durations_json,
    )
