import logging
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope.cache import (
    SCHEMA_OUT_OF_DATE_REMEDIATION,
    AlbumCache,
    batch_lookup_metadata,
    batch_lookup_original_release,
    batch_persist_metadata,
    batch_persist_original_release,
    open_album_cache,
    schema_is_out_of_date,
)
from scrobblescope.enrichment import AlbumMetadata
from tests.album_metadata import deezer_metadata, spotify_metadata
from tests.fake_postgres import fake_postgres


@pytest.mark.asyncio
async def test_batch_lookup_metadata_returns_albums_with_their_provider_columns():
    """A row carrying the provider columns comes back as that provider's album."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(
        return_value=[
            {
                "artist_norm": "grey orton",
                "album_norm": "rumours",
                "spotify_id": None,
                "release_date": "1977-02-04",
                "album_image_url": "https://cdn.example/cover.jpg",
                "track_durations": {},
                "provider": "deezer",
                "provider_album_id": "6237061",
                "provider_url": "https://www.deezer.com/album/6237061",
                "provider_artist": "Grey Orton",
                "provider_title": "Rumours",
            }
        ]
    )

    result = await batch_lookup_metadata(mock_conn, [("grey orton", "rumours")])

    fetch_sql = mock_conn.fetch.call_args[0][0]
    assert "provider" in fetch_sql
    assert "provider_album_id" in fetch_sql
    assert "provider_url" in fetch_sql
    assert "provider_artist" in fetch_sql
    assert "provider_title" in fetch_sql
    assert result == {
        ("grey orton", "rumours"): AlbumMetadata(
            provider="deezer",
            album_id="6237061",
            url="https://www.deezer.com/album/6237061",
            release_date="1977-02-04",
            image_url="https://cdn.example/cover.jpg",
            track_durations={},
            provider_artist="Grey Orton",
            provider_title="Rumours",
        )
    }


@pytest.mark.asyncio
async def test_batch_lookup_metadata_reads_a_pre_provider_row_as_a_spotify_album():
    """A row written before the provider columns (none in the mock) must not
    raise: it is a Spotify album with Spotify's classic link."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(
        return_value=[
            {
                "artist_norm": "radiohead",
                "album_norm": "ok computer",
                "spotify_id": "abc123",
                "release_date": "1997-06-16",
                "album_image_url": None,
                "track_durations": {},
            }
        ]
    )

    result = await batch_lookup_metadata(mock_conn, [("radiohead", "ok computer")])

    album = result[("radiohead", "ok computer")]
    assert (album.provider, album.album_id) == ("spotify", "abc123")
    assert album.url == "https://open.spotify.com/album/abc123"


@pytest.mark.asyncio
async def test_a_row_naming_no_provider_album_is_a_cache_miss():
    """A row with neither a provider nor an album id cannot be shown; leaving it
    out makes it a miss, so the next fetch overwrites it."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(
        return_value=[
            {
                "artist_norm": "a",
                "album_norm": "b",
                "spotify_id": None,
                "release_date": "2000",
                "album_image_url": None,
                "track_durations": {},
                "provider": None,
                "provider_album_id": None,
                "provider_url": None,
            }
        ]
    )

    assert await batch_lookup_metadata(mock_conn, [("a", "b")]) == {}


@pytest.mark.asyncio
async def test_batch_persist_metadata_writes_a_deezer_album_without_a_spotify_id():
    """A Deezer album persists its own id and link in the provider columns and
    leaves the legacy spotify_id column NULL."""
    mock_conn = AsyncMock()
    albums = {("grey orton", "rumours"): deezer_metadata("6237061", "1977-02-04")}

    await batch_persist_metadata(mock_conn, albums)

    mock_conn.execute.assert_awaited_once()
    call_args = mock_conn.execute.call_args[0]
    sql = call_args[0]
    assert "provider" in sql
    assert "provider_album_id" in sql
    assert "provider_url" in sql
    assert call_args[3] == [None]  # spotify_id
    assert call_args[7] == ["deezer"]
    assert call_args[8] == ["6237061"]
    assert call_args[9] == ["https://www.deezer.com/album/6237061"]


@pytest.mark.asyncio
async def test_batch_persist_metadata_writes_a_spotify_id_to_both_columns():
    """A Spotify album's id goes to spotify_id and provider_album_id, and its
    link is stored rather than left NULL."""
    mock_conn = AsyncMock()
    albums = {
        ("artist1", "album1"): spotify_metadata(
            "sp1", provider_artist="Artist1", provider_title="Album1"
        )
    }

    await batch_persist_metadata(mock_conn, albums)

    call_args = mock_conn.execute.call_args[0]
    assert "provider_artist" in call_args[0]
    assert "provider_title" in call_args[0]
    # A re-searched row must overwrite its old names, so both columns have to
    # be in the upsert's update list.
    assert "provider_artist   = EXCLUDED.provider_artist" in call_args[0]
    assert "provider_title    = EXCLUDED.provider_title" in call_args[0]
    assert call_args[10] == ["Artist1"]
    assert call_args[11] == ["Album1"]
    assert call_args[3] == ["sp1"]
    assert call_args[7] == ["spotify"]
    assert call_args[8] == ["sp1"]
    assert call_args[9] == ["https://open.spotify.com/album/sp1"]


@pytest.mark.asyncio
async def test_batch_lookup_original_release_empty_keys_makes_no_call():
    mock_conn = AsyncMock()
    result = await batch_lookup_original_release(mock_conn, [])
    assert result == {}
    mock_conn.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_lookup_original_release_returns_cache_miss_record():
    """A row with a null mb_release_group is a cache hit meaning 'checked,
    nothing found', distinct from no row at all (an uncached key)."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(
        return_value=[
            {
                "artist_norm": "some artist",
                "album_norm": "obscure ep",
                "mb_release_group": None,
                "original_release": None,
            }
        ]
    )

    result = await batch_lookup_original_release(
        mock_conn, [("some artist", "obscure ep")]
    )

    assert ("some artist", "obscure ep") in result
    assert result[("some artist", "obscure ep")]["mb_release_group"] is None


@pytest.mark.asyncio
async def test_batch_persist_original_release_empty_rows_makes_no_call():
    mock_conn = AsyncMock()
    await batch_persist_original_release(mock_conn, [])
    mock_conn.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_persist_original_release_upsert_call_shape():
    mock_conn = AsyncMock()
    rows = [
        ("fleetwood mac", "rumours", "mb-rg-1", "1977-02-04"),
        ("some artist", "obscure ep", None, None),
    ]

    await batch_persist_original_release(mock_conn, rows)

    mock_conn.execute.assert_awaited_once()
    call_args = mock_conn.execute.call_args[0]
    sql = call_args[0]
    assert "INSERT INTO original_release_cache" in sql
    assert "unnest" in sql
    assert "ON CONFLICT" in sql
    assert call_args[1] == ["fleetwood mac", "some artist"]
    assert call_args[2] == ["rumours", "obscure ep"]
    assert call_args[3] == ["mb-rg-1", None]
    assert call_args[4] == ["1977-02-04", None]


# --- The stale-schema diagnostic ------------------------------------------


class _PgError(Exception):
    """Stands in for an asyncpg error, which carries its SQLSTATE."""

    def __init__(self, sqlstate, message="boom"):
        super().__init__(message)
        self.sqlstate = sqlstate


def test_undefined_column_reads_as_a_stale_schema():
    """42703 is what a cache read hits when a migration has not been run.

    Measured against the owner's live database on 2026-09-20: it held the
    pre-Batch-22 schema, so every metadata read raised UndefinedColumnError
    and every job silently ran cache-less against 3,628 usable rows.
    """
    assert schema_is_out_of_date(_PgError("42703", 'column "provider" does not exist'))


def test_undefined_table_reads_as_a_stale_schema():
    """42P01 is the same fault one table earlier: original_release_cache."""
    assert schema_is_out_of_date(
        _PgError("42P01", 'relation "original_release_cache" does not exist')
    )


def test_a_transient_failure_is_not_a_stale_schema():
    """A dropped connection heals itself; a missing column never does.

    Reporting the two the same way is what let a permanent fault look like a
    passing hiccup for as long as it did.
    """
    assert not schema_is_out_of_date(_PgError("08006", "connection failure"))
    assert not schema_is_out_of_date(OSError("connection refused"))
    assert not schema_is_out_of_date(None)


def test_the_remediation_names_the_command_that_fixes_it():
    """The reader will not be the person who wrote the check."""
    assert "init_db.py" in SCHEMA_OUT_OF_DATE_REMEDIATION


KEY = ("radiohead", "ok computer")
MARKER = "secret-marker-do-not-log"


@pytest.mark.asyncio
async def test_a_cache_with_no_database_does_nothing_and_fails_nothing():
    """
    GIVEN no DATABASE_URL
    WHEN every operation runs
    THEN each returns its empty answer, nothing connects, and no failure is
    flagged: a missing cache is not an error.
    """
    with fake_postgres(url=None) as db:
        async with open_album_cache() as album_cache:
            assert album_cache.enabled is False
            assert await album_cache.lookup([KEY]) == {}
            await album_cache.persist({KEY: spotify_metadata()})
            assert await album_cache.lookup_original_releases([KEY]) == {}

    assert (album_cache.lookup_failed, album_cache.persist_failed) == (False, False)
    assert db.connect_attempts == 0
    assert db.statements == []


@pytest.mark.asyncio
@pytest.mark.parametrize("block_raises", [False, True])
async def test_the_connection_closes_once_however_the_block_ends(block_raises):
    """The block's own failure (a provider outage, say) still closes the
    connection, and a normal exit closes it once."""
    with fake_postgres() as db:
        try:
            async with open_album_cache():
                if block_raises:
                    raise RuntimeError("a provider failed")
        except RuntimeError:
            assert block_raises

    assert (db.connect_attempts, db.closes) == (1, 1)


@pytest.mark.asyncio
async def test_a_failing_close_is_logged_by_class_and_never_raised(caplog):
    """
    GIVEN a connection whose close() raises
    WHEN the block ends
    THEN nothing is raised (the job's work is done and its results are built),
    and the log names the exception class, not its text.
    """
    with fake_postgres() as db:

        async def broken_close():
            raise RuntimeError(MARKER)

        db.close = broken_close
        with caplog.at_level(logging.WARNING):
            async with open_album_cache():
                pass

    assert "Closing the cache DB connection failed" in caplog.text
    assert "RuntimeError" in caplog.text
    assert MARKER not in caplog.text


@pytest.mark.asyncio
async def test_a_failed_read_is_a_miss_and_a_failed_write_is_not_an_error():
    """
    GIVEN the metadata read and the metadata write both fail
    WHEN the cache is used
    THEN the read answers {}, the write returns, and each failure is flagged
    for the caller to report.
    """
    with fake_postgres() as db:
        db.fail("SELECT", "spotify_cache", OSError("down"))
        db.fail("INSERT", "spotify_cache", OSError("down"))
        async with open_album_cache() as album_cache:
            assert await album_cache.lookup([KEY]) == {}
            await album_cache.persist({KEY: spotify_metadata()})

    assert album_cache.lookup_failed is True
    assert album_cache.persist_failed is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "album",
    [
        spotify_metadata(
            "sp1", "1997-06-16", "https://img.example.com/ok.jpg", {"a": 1}
        ),
        deezer_metadata("6237061", "1977-02-04"),
        spotify_metadata("sp2", "2001-01-01", None, {}),
    ],
    ids=["spotify", "deezer", "spotify_without_cover_or_durations"],
)
async def test_what_persist_writes_lookup_reads_back(album):
    """Every provider's album survives the cache unchanged, and a healthy cache
    flags no failure."""
    with fake_postgres():
        async with open_album_cache() as album_cache:
            await album_cache.persist({KEY: album})
            assert await album_cache.lookup([KEY]) == {KEY: album}

    assert (album_cache.lookup_failed, album_cache.persist_failed) == (False, False)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("columns", "returned"),
    [
        (
            {"provider": "spotify", "provider_artist": "Captain Beefheart"}
            | {"provider_title": "Safe As Milk"},
            False,
        ),
        (
            {"provider": "spotify", "provider_artist": "Xiu Xiu"}
            | {"provider_title": "A Promise"},
            True,
        ),
        ({"provider": "spotify"}, True),
        ({"provider": "deezer"}, True),
    ],
    ids=["names_of_another_album", "names_fit_the_key", "unstamped", "deezer"],
)
async def test_a_spotify_row_naming_another_album_is_a_miss(columns, returned, caplog):
    """A cached Spotify row whose provider names do not fit its key is dropped,
    so the album is searched again; fitting, unstamped and Deezer rows stay."""
    key = ("xiu xiu", "a promise")
    with fake_postgres() as db:
        db.seed_metadata(
            *key,
            release_date="2004",
            spotify_id="id1",
            provider_album_id="id1",
            **columns,
        )
        async with open_album_cache() as album_cache:
            with caplog.at_level(logging.INFO):
                hits = await album_cache.lookup([key])

    assert (key in hits) is returned
    assert ("Dropped 1 cached" in caplog.text) is (not returned)


@pytest.mark.asyncio
async def test_a_stored_row_naming_no_provider_album_is_a_miss_not_an_album():
    """A row with no provider and no album id is left out of a lookup."""
    with fake_postgres() as db:
        db.seed_metadata(*KEY, release_date="1997", provider=None, spotify_id=None)
        async with open_album_cache() as album_cache:
            assert await album_cache.lookup([KEY]) == {}


@pytest.mark.asyncio
async def test_original_release_lookup_without_a_connection_skips_the_query():
    """No DB connection means no correction lookup and an empty result."""
    with patch(
        "scrobblescope.cache.batch_lookup_original_release", new_callable=AsyncMock
    ) as mock_lookup:
        result = await AlbumCache(None).lookup_original_releases([("artist", "album")])

    assert result == {}
    mock_lookup.assert_not_awaited()


@pytest.mark.asyncio
async def test_original_release_lookup_failure_is_non_fatal(caplog):
    """A correction-cache failure is logged and cannot block album results."""
    with (
        caplog.at_level(logging.WARNING),
        patch(
            "scrobblescope.cache.batch_lookup_original_release",
            new_callable=AsyncMock,
            side_effect=RuntimeError("database unavailable"),
        ),
    ):
        result = await AlbumCache(AsyncMock()).lookup_original_releases(
            [("artist", "album")]
        )

    assert result == {}
    assert "Original-release cache lookup failed (non-fatal): RuntimeError" in (
        caplog.text
    )
    assert "database unavailable" not in caplog.text
