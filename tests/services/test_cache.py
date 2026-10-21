from unittest.mock import AsyncMock

import pytest

from scrobblescope.cache import (
    SCHEMA_OUT_OF_DATE_REMEDIATION,
    batch_lookup_metadata,
    batch_lookup_original_release,
    batch_persist_metadata,
    batch_persist_original_release,
    schema_is_out_of_date,
)
from scrobblescope.enrichment import AlbumMetadata
from tests.album_metadata import deezer_metadata, spotify_metadata


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
            }
        ]
    )

    result = await batch_lookup_metadata(mock_conn, [("grey orton", "rumours")])

    fetch_sql = mock_conn.fetch.call_args[0][0]
    assert "provider" in fetch_sql
    assert "provider_album_id" in fetch_sql
    assert "provider_url" in fetch_sql
    assert result == {
        ("grey orton", "rumours"): AlbumMetadata(
            provider="deezer",
            album_id="6237061",
            url="https://www.deezer.com/album/6237061",
            release_date="1977-02-04",
            image_url="https://cdn.example/cover.jpg",
            track_durations={},
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
    albums = {("artist1", "album1"): spotify_metadata("sp1")}

    await batch_persist_metadata(mock_conn, albums)

    call_args = mock_conn.execute.call_args[0]
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
