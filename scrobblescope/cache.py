import asyncio
import json
import logging
import os

try:
    import asyncpg
except ImportError:
    asyncpg = None

from scrobblescope.config import METADATA_CACHE_TTL_DAYS, ORIGINAL_RELEASE_TTL_DAYS

# Capture DATABASE_URL once at import time.  load_dotenv() in app.py runs
# before any module in scrobblescope is imported, so the value is guaranteed
# to be present here if it exists in .env.  Reading os.environ later from a
# worker thread has proven unreliable on Windows (the value disappears
# between app startup and the first background-task invocation).
_DATABASE_URL: str | None = os.environ.get("DATABASE_URL")


async def _get_db_connection():
    """Open a single asyncpg connection from DATABASE_URL, or return None.

    Returns None if DATABASE_URL is unset, asyncpg is unavailable, or the
    connection attempt fails. The caller is responsible for closing the
    returned connection.

    Failure reasons are logged with explicit classification labels:
    - `asyncpg-missing`
    - `missing-env-var`
    - `db-down`

    To smooth over Fly Postgres wake-up races, connection attempts use a small
    exponential backoff before giving up. Each attempt is capped at
    DB_CONNECT_TIMEOUT_SECONDS (default 5s) so an unreachable host that
    never answers -- rather than actively refusing -- fails fast instead of
    hanging for asyncpg's own 60s default per attempt.
    """
    if asyncpg is None:
        logging.warning(
            "DB cache unavailable (asyncpg-missing): asyncpg is not installed."
        )
        return None
    dsn = _DATABASE_URL
    if not dsn:
        logging.info("DB cache disabled (missing-env-var): DATABASE_URL is not set.")
        return None
    max_attempts = max(1, int(os.environ.get("DB_CONNECT_MAX_ATTEMPTS", "3")))
    base_delay_seconds = float(os.environ.get("DB_CONNECT_BASE_DELAY_SECONDS", "0.25"))
    # asyncpg.connect has no caller-set timeout by default, so a host that
    # never answers (a paused container gets no SYN-ACK, unlike a refused
    # connection) hangs for asyncpg's own 60s default on every attempt --
    # observed as a 3-minute silent stall at DB_CONNECT_MAX_ATTEMPTS=3.
    connect_timeout_seconds = float(os.environ.get("DB_CONNECT_TIMEOUT_SECONDS", "5"))
    for attempt in range(1, max_attempts + 1):
        try:
            conn = await asyncpg.connect(dsn, timeout=connect_timeout_seconds)
            return conn
        except Exception as exc:
            if attempt >= max_attempts:
                logging.warning(
                    "DB cache unavailable (db-down): connection failed after %s "
                    "attempts (cache disabled): %s",
                    max_attempts,
                    exc,
                )
                return None
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logging.warning(
                "DB connection attempt %s/%s failed (db-down): %s. Retrying in %.2fs.",
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
               album_image_url, track_durations, provider, provider_album_id,
               provider_url
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
            "provider": r.get("provider"),
            "provider_album_id": r.get("provider_album_id"),
            "provider_url": r.get("provider_url"),
        }
    return result


async def _cleanup_stale_metadata(conn):
    """Delete spotify_cache rows older than METADATA_CACHE_TTL_DAYS.

    Called opportunistically after each batch lookup. Non-fatal: any error
    is logged as a warning and silently suppressed so the job continues.
    """
    try:
        result = await conn.execute(
            """
            DELETE FROM spotify_cache
            WHERE updated_at < NOW() - make_interval(days => $1)
            """,
            METADATA_CACHE_TTL_DAYS,
        )
        logging.info("Stale cache cleanup: %s", result)
    except Exception as exc:
        logging.warning("Stale cache cleanup failed (non-fatal): %s", exc)


async def _batch_persist_metadata(conn, rows):
    """Persist newly fetched album metadata in a single INSERT statement.

    Uses INSERT ... SELECT FROM unnest() with ON CONFLICT DO UPDATE (upsert).
    Each element in *rows* is a tuple of (artist_norm, album_norm, spotify_id,
    release_date, album_image_url, track_durations_dict), optionally followed
    by (provider, provider_album_id, provider_url). A row without the
    trailing three elements is treated as a Spotify row (``provider``
    defaults to ``"spotify"`` and ``provider_album_id`` to ``spotify_id``),
    matching every caller that predates the provider contract.
    """
    if not rows:
        return
    artists = [r[0] for r in rows]
    albums = [r[1] for r in rows]
    spotify_ids = [r[2] for r in rows]
    release_dates = [r[3] for r in rows]
    image_urls = [r[4] for r in rows]
    track_durations_json = [json.dumps(r[5]) if r[5] else "{}" for r in rows]
    providers = [r[6] if len(r) > 6 else "spotify" for r in rows]
    provider_album_ids = [r[7] if len(r) > 7 else r[2] for r in rows]
    provider_urls = [r[8] if len(r) > 8 else None for r in rows]
    await conn.execute(
        """
        INSERT INTO spotify_cache
            (artist_norm, album_norm, spotify_id, release_date,
             album_image_url, track_durations, provider, provider_album_id,
             provider_url)
        SELECT * FROM unnest(
            $1::text[], $2::text[], $3::text[], $4::text[],
            $5::text[], $6::jsonb[], $7::text[], $8::text[], $9::text[]
        )
        ON CONFLICT (artist_norm, album_norm) DO UPDATE SET
            spotify_id        = EXCLUDED.spotify_id,
            release_date      = EXCLUDED.release_date,
            album_image_url   = EXCLUDED.album_image_url,
            track_durations   = EXCLUDED.track_durations,
            provider          = EXCLUDED.provider,
            provider_album_id = EXCLUDED.provider_album_id,
            provider_url      = EXCLUDED.provider_url,
            updated_at        = NOW()
        """,
        artists,
        albums,
        spotify_ids,
        release_dates,
        image_urls,
        track_durations_json,
        providers,
        provider_album_ids,
        provider_urls,
    )


async def _batch_lookup_original_release(conn, keys):
    """Look up cached MusicBrainz original-release findings for a batch of
    (artist_norm, album_norm) keys.

    Returns a dict keyed by (artist_norm, album_norm) with
    {"mb_release_group": str | None, "original_release": str | None}. A row
    with a null ``mb_release_group`` records "checked, nothing found" --
    still a cache hit, so the caller does not re-query MusicBrainz for it.
    """
    if not keys:
        return {}
    artists = [k[0] for k in keys]
    albums = [k[1] for k in keys]
    rows = await conn.fetch(
        """
        SELECT artist_norm, album_norm, mb_release_group, original_release
        FROM original_release_cache
        WHERE (artist_norm, album_norm) IN (
            SELECT unnest($1::text[]), unnest($2::text[])
        )
        AND checked_at > NOW() - make_interval(days => $3)
        """,
        artists,
        albums,
        ORIGINAL_RELEASE_TTL_DAYS,
    )
    return {
        (r["artist_norm"], r["album_norm"]): {
            "mb_release_group": r["mb_release_group"],
            "original_release": r["original_release"],
        }
        for r in rows
    }


async def _batch_persist_original_release(conn, rows):
    """Persist MusicBrainz original-release findings in a single INSERT.

    Each element in *rows* is a tuple of (artist_norm, album_norm,
    mb_release_group, original_release). ``mb_release_group`` and
    ``original_release`` may both be None -- a deliberate "checked, nothing
    found" record, since original dates do not change and the TTL only
    guards against a bad match.
    """
    if not rows:
        return
    artists = [r[0] for r in rows]
    albums = [r[1] for r in rows]
    mb_release_groups = [r[2] for r in rows]
    original_releases = [r[3] for r in rows]
    await conn.execute(
        """
        INSERT INTO original_release_cache
            (artist_norm, album_norm, mb_release_group, original_release)
        SELECT * FROM unnest(
            $1::text[], $2::text[], $3::text[], $4::text[]
        )
        ON CONFLICT (artist_norm, album_norm) DO UPDATE SET
            mb_release_group = EXCLUDED.mb_release_group,
            original_release = EXCLUDED.original_release,
            checked_at        = NOW()
        """,
        artists,
        albums,
        mb_release_groups,
        original_releases,
    )
