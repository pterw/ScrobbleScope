"""Schema initialization for ScrobbleScope Postgres cache.

Designed to run as a Fly.io release_command (after build, before traffic).
Idempotent — safe to run on every deploy.

Exit codes:
    0 — success or DATABASE_URL unset (no-op for local dev)
    1 — connection or schema error (Fly rolls back the deploy)
"""

import asyncio
import os
import sys


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

    try:
        conn = await asyncpg.connect(dsn)
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
            print("Schema initialized successfully")
        finally:
            await conn.close()
    except Exception as exc:
        print(f"ERROR: Schema init failed — {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
