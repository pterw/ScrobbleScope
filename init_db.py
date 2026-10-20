"""Schema initialization for ScrobbleScope Postgres cache.

Designed to run as a Fly.io release_command (after build, before traffic).
Idempotent — safe to run on every deploy.

The schema step (connect plus every statement) is retried with a capped
backoff when the connection fails in a transient way, because the database
may still be waking when the release command connects (see SCHEMA_ATTEMPTS).
A SQL error fails at once.

Exit codes:
    0 — success or DATABASE_URL unset (no-op for local dev)
    1 — connection or schema error (Fly rolls back the deploy)
"""

import asyncio
import os
import sys

# The Postgres app auto-starts on the first connection and can take a few
# seconds to accept connections (a release failed on 2026-10-01 because the
# proxy restarted mid-boot). Retry the whole schema step: every statement is
# idempotent. 6 attempts with sleeps of 1, 2, 4, 8, 8 s is about 23 s, well
# inside Fly's release timeout.
SCHEMA_ATTEMPTS = 6
SCHEMA_BACKOFF_SECONDS = (1, 2, 4, 8, 8)
CONNECT_TIMEOUT_SECONDS = 10


async def _apply_schema(asyncpg, dsn):
    """Connect and run every schema statement once."""
    conn = await asyncpg.connect(dsn, timeout=CONNECT_TIMEOUT_SECONDS)
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spotify_cache (
                artist_norm     TEXT NOT NULL,
                album_norm      TEXT NOT NULL,
                spotify_id      TEXT NOT NULL,
                release_date    TEXT,
                album_image_url TEXT,
                track_durations JSONB,
                created_at      TIMESTAMPTZ DEFAULT NOW(),
                updated_at      TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (artist_norm, album_norm)
            )
            """
        )
        # Batch 22: any provider (not only Spotify) can populate this
        # cache. CREATE TABLE never alters an existing table, so these
        # columns need an explicit migration; spotify_id predates the
        # provider column and stays for rows Spotify wrote, but a
        # Deezer-only row cannot satisfy its old NOT NULL.
        await conn.execute(
            """
            ALTER TABLE spotify_cache
                ADD COLUMN IF NOT EXISTS provider TEXT,
                ADD COLUMN IF NOT EXISTS provider_album_id TEXT,
                ADD COLUMN IF NOT EXISTS provider_url TEXT,
                ALTER COLUMN spotify_id DROP NOT NULL
            """
        )
        await conn.execute(
            """
            UPDATE spotify_cache
            SET provider = 'spotify', provider_album_id = spotify_id
            WHERE provider IS NULL AND spotify_id IS NOT NULL
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS original_release_cache (
                artist_norm       TEXT NOT NULL,
                album_norm        TEXT NOT NULL,
                mb_release_group  TEXT,
                original_release  TEXT,
                checked_at        TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (artist_norm, album_norm)
            )
            """
        )
    finally:
        await conn.close()


async def main():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set — skipping schema init (local dev mode)")
        return

    try:
        import asyncpg
    except ImportError:
        print("ERROR: asyncpg not installed", file=sys.stderr)
        sys.exit(1)

    transient = (
        OSError,
        asyncio.TimeoutError,
        asyncpg.exceptions.ConnectionDoesNotExistError,
        asyncpg.exceptions.InterfaceError,
        asyncpg.exceptions.CannotConnectNowError,
        asyncpg.exceptions.ConnectionFailureError,
    )

    try:
        for attempt in range(1, SCHEMA_ATTEMPTS + 1):
            try:
                await _apply_schema(asyncpg, dsn)
                break
            except transient as exc:
                if attempt == SCHEMA_ATTEMPTS:
                    raise
                # Type only: the message can carry the DSN (Rule 6).
                print(
                    f"Schema init attempt {attempt}/{SCHEMA_ATTEMPTS} failed "
                    f"({type(exc).__name__}); retrying",
                    file=sys.stderr,
                )
                await asyncio.sleep(SCHEMA_BACKOFF_SECONDS[attempt - 1])
        print("Schema initialized successfully")
    # CLI boundary: report any failure as one line and a nonzero exit.
    except Exception as exc:  # noqa: BLE001
        # Type only, never the text: it can carry the DSN (Rule 6). A
        # PostgresError adds its SQLSTATE, a fixed five-character code
        # with no DSN or user data, so a SQL failure stays diagnosable.
        detail = type(exc).__name__
        if isinstance(exc, asyncpg.exceptions.PostgresError) and exc.sqlstate:
            detail += f", SQLSTATE {exc.sqlstate}"
        print(f"ERROR: Schema init failed ({detail})", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
