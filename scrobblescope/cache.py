import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

try:
    import asyncpg
except ImportError:
    asyncpg = None

from scrobblescope.config import METADATA_CACHE_TTL_DAYS, ORIGINAL_RELEASE_TTL_DAYS
from scrobblescope.enrichment import MATCH_WRONG, AlbumMetadata
from scrobblescope.utils import log_failure

# Capture DATABASE_URL once at import time.  load_dotenv() in app.py runs
# before any module in scrobblescope is imported, so the value is guaranteed
# to be present here if it exists in .env.  Reading os.environ later from a
# worker thread has proven unreliable on Windows (the value disappears
# between app startup and the first background-task invocation).
_DATABASE_URL: str | None = os.environ.get("DATABASE_URL")

#: PostgreSQL SQLSTATEs that mean the database is missing something this code
#: expects: 42703 undefined_column, 42P01 undefined_table. Matched on the code
#: rather than the asyncpg exception class because asyncpg is an optional
#: import here, and a SQLSTATE is the stable half of the contract anyway.
_STALE_SCHEMA_SQLSTATES = frozenset({"42703", "42P01"})

#: What to do about it. A missing column is not a transient failure: it never
#: heals, and every read until it is fixed misses a cache that is sitting
#: right there. Found on 2026-09-20, when the owner's database still held the
#: pre-Batch-22 schema and 3,628 usable rows went unread on every job.
SCHEMA_OUT_OF_DATE_REMEDIATION = (
    "The cache schema is out of date -- run `python init_db.py` with "
    "DATABASE_URL set. It is idempotent and safe to re-run."
)


def schema_is_out_of_date(exc):
    """Return True when *exc* says the database lacks something the code needs.

    Distinguishing this from a dropped connection is the whole point: one is
    a hiccup that heals itself and the other is a migration nobody has run,
    and reporting them in the same words is what let a permanently inert
    cache look like a passing glitch.
    """
    return getattr(exc, "sqlstate", None) in _STALE_SCHEMA_SQLSTATES


async def get_db_connection():
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
        # The cache is optional: any connect failure disables it for this job.
        except Exception:  # noqa: BLE001
            if attempt >= max_attempts:
                log_failure(
                    f"DB cache unavailable (db-down): connection failed after "
                    f"{max_attempts} attempts (cache disabled)",
                    logging.WARNING,
                )
                return None
            delay = base_delay_seconds * (2 ** (attempt - 1))
            log_failure(
                f"DB connection attempt {attempt}/{max_attempts} failed (db-down), "
                f"retrying in {delay:.2f}s",
                logging.WARNING,
            )
            await asyncio.sleep(delay)


async def batch_lookup_metadata(conn, keys):
    """Look up cached album metadata for a batch of (artist_norm, album_norm) keys.

    Executes a single SELECT using unnest() for efficient batch lookup.
    Only rows updated within the configured TTL are returned.
    Returns a dict keyed by (artist_norm, album_norm) with ``AlbumMetadata``
    values. ``AlbumMetadata.from_row`` owns how a stored row is read, rows
    older than the provider columns included; a row that names no provider
    album is left out, so it is a miss and the next fetch overwrites it.
    """
    if not keys:
        return {}
    artists = [k[0] for k in keys]
    albums = [k[1] for k in keys]
    rows = await conn.fetch(
        """
        SELECT artist_norm, album_norm, spotify_id, release_date,
               album_image_url, track_durations, provider, provider_album_id,
               provider_url, provider_artist, provider_title
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
        metadata = AlbumMetadata.from_row(r)
        if metadata is not None:
            result[(r["artist_norm"], r["album_norm"])] = metadata
    return result


async def cleanup_stale_metadata(conn):
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
    # Opportunistic housekeeping; a failure must never reach the job.
    except Exception:  # noqa: BLE001
        log_failure("Stale cache cleanup failed (non-fatal)", logging.WARNING)


async def batch_persist_metadata(conn, albums):
    """Persist newly fetched album metadata in a single INSERT statement.

    *albums* maps (artist_norm, album_norm) to the ``AlbumMetadata`` a provider
    returned. This is the only statement that writes ``spotify_cache``, and
    ``AlbumMetadata`` has no field a listening fact could travel in, so the
    shared table's contract (BATCH23 "Data handling": no listening facts, no
    link to a listener) is held by the type. Uses INSERT ... SELECT FROM
    unnest() with ON CONFLICT DO UPDATE (upsert). The legacy ``spotify_id``
    column takes the album id for a Spotify album and NULL for any other
    provider; ``provider_album_id`` always takes the id the provider issued.
    """
    if not albums:
        return
    keys = list(albums)
    metadata = [albums[key] for key in keys]
    artists = [key[0] for key in keys]
    album_norms = [key[1] for key in keys]
    spotify_ids = [m.spotify_id for m in metadata]
    release_dates = [m.release_date for m in metadata]
    image_urls = [m.image_url for m in metadata]
    track_durations_json = [
        json.dumps(m.track_durations) if m.track_durations else "{}" for m in metadata
    ]
    providers = [m.provider for m in metadata]
    provider_album_ids = [m.album_id for m in metadata]
    provider_urls = [m.url for m in metadata]
    provider_artists = [m.provider_artist for m in metadata]
    provider_titles = [m.provider_title for m in metadata]
    await conn.execute(
        """
        INSERT INTO spotify_cache
            (artist_norm, album_norm, spotify_id, release_date,
             album_image_url, track_durations, provider, provider_album_id,
             provider_url, provider_artist, provider_title)
        SELECT * FROM unnest(
            $1::text[], $2::text[], $3::text[], $4::text[],
            $5::text[], $6::jsonb[], $7::text[], $8::text[], $9::text[],
            $10::text[], $11::text[]
        )
        ON CONFLICT (artist_norm, album_norm) DO UPDATE SET
            spotify_id        = EXCLUDED.spotify_id,
            release_date      = EXCLUDED.release_date,
            album_image_url   = EXCLUDED.album_image_url,
            track_durations   = EXCLUDED.track_durations,
            provider          = EXCLUDED.provider,
            provider_album_id = EXCLUDED.provider_album_id,
            provider_url      = EXCLUDED.provider_url,
            provider_artist   = EXCLUDED.provider_artist,
            provider_title    = EXCLUDED.provider_title,
            updated_at        = NOW()
        """,
        artists,
        album_norms,
        spotify_ids,
        release_dates,
        image_urls,
        track_durations_json,
        providers,
        provider_album_ids,
        provider_urls,
        provider_artists,
        provider_titles,
    )


async def batch_lookup_original_release(conn, keys):
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


async def batch_persist_original_release(conn, rows):
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


class AlbumCache:
    """One job's use of the shared album cache, and what its failures mean.

    The cache is optional at runtime (BATCH23 / the hosting cost ceiling): a
    missing, sleeping or failing database never fails a job. This class is the
    one place that says so. Every operation answers with an empty value instead
    of raising, and records which operation failed in ``lookup_failed`` and
    ``persist_failed`` so the caller can tell the job (job messages stay with
    the caller). It issues the same statements the pipeline always did, on the
    one connection ``open_album_cache`` opened: it never reconnects and never
    retries a statement.

    Build one with ``open_album_cache``; the constructor takes the connection
    (or None for a disabled cache) so tests can hand it a fake.
    """

    def __init__(self, conn):
        self._conn = conn
        self.lookup_failed = False
        self.persist_failed = False

    @property
    def enabled(self):
        """True while a database connection is open."""
        return self._conn is not None

    async def lookup(self, keys):
        """Return cached ``AlbumMetadata`` for *keys*, then clear stale rows.

        A Spotify row whose provider names do not fit its key is left out (a
        miss); an unstamped or non-Spotify row is returned.

        Returns {} when the cache is disabled or the read fails (every album is
        then a miss and the providers answer). A schema that is out of date
        gets its own remediation text: until it is fixed every read misses.
        The stale-row cleanup runs after the read whether or not it succeeded.
        """
        if self._conn is None:
            return {}
        try:
            hits = await batch_lookup_metadata(self._conn, keys)
        # Fail open: a failed cache read makes every album a miss, not a failed job.
        except Exception as exc:  # noqa: BLE001
            self.lookup_failed = True
            if schema_is_out_of_date(exc):
                log_failure(
                    "DB lookup failed, proceeding without cache "
                    f"({SCHEMA_OUT_OF_DATE_REMEDIATION})",
                    logging.WARNING,
                )
            else:
                log_failure(
                    "DB lookup failed, proceeding without cache", logging.WARNING
                )
            hits = {}
        # A row whose provider names do not fit its key is another album's: a
        # miss, searched again and overwritten by the upsert.
        fitting = {k: v for k, v in hits.items() if v.match_for(k) != MATCH_WRONG}
        if len(fitting) < len(hits):
            logging.info(
                f"Dropped {len(hits) - len(fitting)} cached albums "
                "whose provider names do not fit the key"
            )
        hits = fitting
        # Opportunistic stale-row cleanup -- non-fatal, errors swallowed inside.
        await cleanup_stale_metadata(self._conn)
        return hits

    async def persist(self, albums):
        """Write *albums* (``{key: AlbumMetadata}``) in one upsert.

        A no-op when the cache is disabled or *albums* is empty. A failure is
        logged, flagged in ``persist_failed`` and not raised: it costs the next
        job a lookup, not this one.
        """
        if self._conn is None or not albums:
            return
        try:
            await batch_persist_metadata(self._conn, albums)
        # Fail open: a failed persist costs the next job a lookup, not this one.
        except Exception:  # noqa: BLE001
            self.persist_failed = True
            log_failure("DB persist failed (non-fatal)", logging.WARNING)

    async def lookup_original_releases(self, keys):
        """Return cached MusicBrainz findings for *keys*, or {} without raising.

        A missing correction only skips the display upgrade; it must never
        block a job the way a metadata-fetch failure would.
        """
        if self._conn is None:
            return {}
        try:
            return await batch_lookup_original_release(self._conn, keys)
        # Fail open: a missing correction only skips the display upgrade.
        except Exception:  # noqa: BLE001
            log_failure(
                "Original-release cache lookup failed (non-fatal)", logging.WARNING
            )
            return {}

    async def close(self):
        """Close the connection at most once; a failed close is logged only.

        The cache is optional, so closing it must not take down a job whose
        results are already built.
        """
        conn, self._conn = self._conn, None
        if conn is None:
            return
        try:
            await conn.close()
        # A failed close must not mask the job's own outcome.
        except Exception:  # noqa: BLE001
            log_failure("Closing the cache DB connection failed", logging.WARNING)


@asynccontextmanager
async def open_album_cache():
    """Open the shared album cache for one job and close it when the block ends.

    Connects through ``get_db_connection`` (``DATABASE_URL``, the retry
    backoff and the connect timeout are its, unchanged) and yields an
    ``AlbumCache``, disabled when no connection could be had. The connection is
    closed when the block ends, whether it ends normally or with an exception.
    """
    album_cache = AlbumCache(await get_db_connection())
    try:
        yield album_cache
    finally:
        await album_cache.close()
