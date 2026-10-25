"""An in-memory PostgreSQL for the album metadata cache.

``scrobblescope.cache`` sends a handful of statements: a batch read of
``spotify_cache``, an upsert into it, a stale-row delete, and a read and an
upsert of ``original_release_cache``. This fake answers exactly those against
two dicts, so a test that drives the real cache module sees what the SQL's
arguments would store, not a mock's call list.

``statements`` records ``(verb, table)`` for EVERY statement the code sends, in
order, before anything else happens to it (``table`` is ``None`` when the
statement names neither cache table, e.g. ``SELECT 1``), which is how a test
proves a job's database traffic did not grow. A statement the fake does not
answer, or one sent on a closed connection (asyncpg raises ``InterfaceError``),
raises, and is also listed in ``refused``. The cache module swallows every
database error, so the raise alone is invisible: ``fake_postgres`` asserts
``refused`` is empty when its block ends, and a sequence assertion sees the
extra ``statements`` entry. Not modelled: TTLs (the days argument,
``updated_at``), column types and unique-key rules.

``connect_attempts`` counts calls to ``asyncpg.connect`` and ``closes`` counts
``close()`` calls.
"""

import json
from contextlib import contextmanager
from unittest.mock import patch

from asyncpg.exceptions import InterfaceError

#: The nine data columns of ``spotify_cache`` after the two key columns, in
#: the order ``cache.py``'s upsert passes its arrays.
METADATA_FIELDS = (
    "spotify_id",
    "release_date",
    "album_image_url",
    "track_durations",
    "provider",
    "provider_album_id",
    "provider_url",
    "provider_artist",
    "provider_title",
)

_ORIGINAL_FIELDS = ("mb_release_group", "original_release")


class _Row(dict):
    """What asyncpg returns: read by column name, with ``.get``."""


class FakePostgres:
    """One database, doubling as the connection the cache module is handed."""

    def __init__(self):
        self.metadata = {}
        self.original_releases = {}
        self.statements = []
        self.refused = []
        self.connect_attempts = 0
        self.closes = 0
        self.closed = False
        self._failures = {}

    def seed_metadata(self, artist_norm, album_norm, **columns):
        """Store a ``spotify_cache`` row; unnamed columns are NULL.

        ``track_durations`` may be given as a dict, which is stored as the JSON
        string asyncpg returns for a JSONB column with no codec registered.
        """
        row = dict.fromkeys(METADATA_FIELDS)
        unknown = set(columns) - set(row)
        assert not unknown, f"not a spotify_cache column: {sorted(unknown)}"
        row.update(columns)
        if isinstance(row["track_durations"], dict):
            row["track_durations"] = json.dumps(row["track_durations"])
        self.metadata[(artist_norm, album_norm)] = row

    def seed_original_release(
        self, artist_norm, album_norm, mb_release_group, original_release
    ):
        """Store an ``original_release_cache`` row."""
        self.original_releases[(artist_norm, album_norm)] = {
            "mb_release_group": mb_release_group,
            "original_release": original_release,
        }

    def fail(self, verb, table, error):
        """Make every statement of this kind raise *error*."""
        self._failures[(verb, table)] = error

    def _begin(self, sql):
        """Record a statement, raise its planted failure, return (verb, table)."""
        verb = sql.split(None, 1)[0].upper()
        if "original_release_cache" in sql:
            table = "original_release_cache"
        elif "spotify_cache" in sql:
            table = "spotify_cache"
        else:
            table = None
        self.statements.append((verb, table))
        if self.closed:
            self.refused.append(f"{verb} on a closed connection")
            raise InterfaceError("connection is closed")
        if table is None:
            self.refused.append(f"{verb} names no cache table: {sql[:80]!r}")
            raise AssertionError(f"FakePostgres: unknown table in {sql[:80]!r}")
        error = self._failures.get((verb, table))
        if error is not None:
            raise error
        return verb, table

    async def fetch(self, sql, *args):
        """Answer the two batch reads; the TTL argument is accepted and ignored."""
        verb, table = self._begin(sql)
        if verb != "SELECT":
            raise AssertionError(f"FakePostgres.fetch got {verb} on {table}")
        artists, albums, _days = args
        wanted = set(zip(artists, albums, strict=True))
        rows = self.metadata if table == "spotify_cache" else self.original_releases
        return [
            _Row(artist_norm=artist, album_norm=album, **row)
            for (artist, album), row in rows.items()
            if (artist, album) in wanted
        ]

    async def execute(self, sql, *args):
        """Apply the two upserts and accept the stale-row delete."""
        verb, table = self._begin(sql)
        if (verb, table) == ("INSERT", "spotify_cache"):
            artists, albums, *columns = args
            assert len(columns) == len(METADATA_FIELDS), (
                f"FakePostgres: spotify_cache upsert passed {len(columns)} "
                f"column arrays, expected {len(METADATA_FIELDS)}"
            )
            for index, key in enumerate(zip(artists, albums, strict=True)):
                self.metadata[key] = {
                    name: values[index]
                    for name, values in zip(METADATA_FIELDS, columns, strict=True)
                }
        elif (verb, table) == ("INSERT", "original_release_cache"):
            artists, albums, *columns = args
            assert len(columns) == len(_ORIGINAL_FIELDS)
            for index, key in enumerate(zip(artists, albums, strict=True)):
                self.original_releases[key] = {
                    name: values[index]
                    for name, values in zip(_ORIGINAL_FIELDS, columns, strict=True)
                }
        elif (verb, table) == ("DELETE", "spotify_cache"):
            pass
        else:
            raise AssertionError(f"FakePostgres.execute got {verb} on {table}")
        return f"{verb} OK"

    async def close(self):
        """Count a close; the cache module must close exactly once per job."""
        self.closes += 1
        self.closed = True


@contextmanager
def fake_postgres(
    db=None, *, connect_error=None, url="postgresql://fake.invalid/cache"
):
    """Point ``scrobblescope.cache`` at *db* (a new ``FakePostgres`` by default).

    ``connect_error`` makes every ``asyncpg.connect`` raise it, which is a
    database that is asleep or unreachable. ``url=None`` is a deployment with
    no ``DATABASE_URL``.
    """
    db = db or FakePostgres()

    class _Driver:
        @staticmethod
        async def connect(dsn, timeout=None):
            db.connect_attempts += 1
            if connect_error is not None:
                raise connect_error
            db.closed = False
            return db

    with (
        patch("scrobblescope.cache.asyncpg", _Driver),
        patch("scrobblescope.cache._DATABASE_URL", url),
    ):
        yield db
    assert not db.refused, f"FakePostgres refused statements: {db.refused}"
