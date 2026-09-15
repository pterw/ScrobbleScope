from unittest.mock import AsyncMock

import pytest

from scrobblescope.cache import (
    _batch_lookup_metadata,
    _batch_lookup_original_release,
    _batch_persist_metadata,
    _batch_persist_original_release,
)


@pytest.mark.asyncio
async def test_batch_lookup_metadata_selects_and_returns_provider_columns():
    """A row carrying the new provider columns round-trips through the dict."""
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

    result = await _batch_lookup_metadata(mock_conn, [("grey orton", "rumours")])

    fetch_sql = mock_conn.fetch.call_args[0][0]
    assert "provider" in fetch_sql
    assert "provider_album_id" in fetch_sql
    assert "provider_url" in fetch_sql

    row = result[("grey orton", "rumours")]
    assert row["provider"] == "deezer"
    assert row["provider_album_id"] == "6237061"
    assert row["provider_url"] == "https://www.deezer.com/album/6237061"


@pytest.mark.asyncio
async def test_batch_lookup_metadata_defaults_provider_fields_when_absent():
    """A pre-migration row (no provider columns in the mock) must not raise."""
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

    result = await _batch_lookup_metadata(mock_conn, [("radiohead", "ok computer")])

    row = result[("radiohead", "ok computer")]
    assert row["provider"] is None
    assert row["provider_album_id"] is None
    assert row["provider_url"] is None


@pytest.mark.asyncio
async def test_batch_persist_metadata_writes_provider_columns_when_given():
    """A 9-element row (post-provider-contract caller) persists all three
    new columns as its own arrays, not the legacy defaults."""
    mock_conn = AsyncMock()
    rows = [
        (
            "grey orton",
            "rumours",
            None,
            "1977-02-04",
            "https://cdn.example/cover.jpg",
            {},
            "deezer",
            "6237061",
            "https://www.deezer.com/album/6237061",
        )
    ]

    await _batch_persist_metadata(mock_conn, rows)

    mock_conn.execute.assert_awaited_once()
    call_args = mock_conn.execute.call_args[0]
    sql = call_args[0]
    assert "provider" in sql
    assert "provider_album_id" in sql
    assert "provider_url" in sql
    assert call_args[7] == ["deezer"]
    assert call_args[8] == ["6237061"]
    assert call_args[9] == ["https://www.deezer.com/album/6237061"]


@pytest.mark.asyncio
async def test_batch_persist_metadata_defaults_provider_for_legacy_six_tuple():
    """A pre-Task-3 caller still passes 6-element rows; persisting them must
    tag the row as a Spotify write rather than leaving provider NULL."""
    mock_conn = AsyncMock()
    rows = [("artist1", "album1", "sp1", "2025-01-01", "https://img/1.jpg", {})]

    await _batch_persist_metadata(mock_conn, rows)

    call_args = mock_conn.execute.call_args[0]
    assert call_args[7] == ["spotify"]
    assert call_args[8] == ["sp1"]  # provider_album_id defaults to spotify_id
    assert call_args[9] == [None]


@pytest.mark.asyncio
async def test_batch_lookup_original_release_empty_keys_makes_no_call():
    mock_conn = AsyncMock()
    result = await _batch_lookup_original_release(mock_conn, [])
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

    result = await _batch_lookup_original_release(
        mock_conn, [("some artist", "obscure ep")]
    )

    assert ("some artist", "obscure ep") in result
    assert result[("some artist", "obscure ep")]["mb_release_group"] is None


@pytest.mark.asyncio
async def test_batch_persist_original_release_empty_rows_makes_no_call():
    mock_conn = AsyncMock()
    await _batch_persist_original_release(mock_conn, [])
    mock_conn.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_persist_original_release_upsert_call_shape():
    mock_conn = AsyncMock()
    rows = [
        ("fleetwood mac", "rumours", "mb-rg-1", "1977-02-04"),
        ("some artist", "obscure ep", None, None),
    ]

    await _batch_persist_original_release(mock_conn, rows)

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
