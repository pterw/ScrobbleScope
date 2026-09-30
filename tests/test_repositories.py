# tests/test_repositories.py
import json
import logging
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope.cache import (
    _batch_lookup_metadata,
    _batch_persist_metadata,
    _get_db_connection,
)

# --- DB helper tests ---


@pytest.mark.asyncio
async def test_get_db_connection_no_asyncpg(caplog):
    """
    GIVEN asyncpg is None (not installed)
    WHEN _get_db_connection is called
    THEN it should return None immediately.
    """
    with patch("scrobblescope.cache.asyncpg", None):
        with caplog.at_level(logging.INFO):
            result = await _get_db_connection()
    assert result is None
    assert "asyncpg-missing" in caplog.text


@pytest.mark.asyncio
async def test_get_db_connection_no_database_url(caplog):
    """
    GIVEN asyncpg is available but DATABASE_URL is not set
    WHEN _get_db_connection is called
    THEN it should return None.
    """
    with patch("scrobblescope.cache._DATABASE_URL", None):
        with caplog.at_level(logging.INFO):
            result = await _get_db_connection()
    assert result is None
    assert "missing-env-var" in caplog.text


@pytest.mark.asyncio
async def test_get_db_connection_connect_failure(caplog):
    """
    GIVEN DATABASE_URL is set but the connection fails
    WHEN _get_db_connection is called
    THEN it should return None and log a warning.
    """
    with patch("scrobblescope.cache._DATABASE_URL", "postgres://bad:bad@localhost/bad"):
        with patch.dict(
            "os.environ",
            {
                "DB_CONNECT_MAX_ATTEMPTS": "1",
                "DB_CONNECT_BASE_DELAY_SECONDS": "0",
            },
        ):
            with patch("scrobblescope.cache.asyncpg") as mock_asyncpg:
                mock_asyncpg.connect = AsyncMock(
                    side_effect=Exception("connection refused")
                )
                with caplog.at_level(logging.INFO):
                    result = await _get_db_connection()
    assert result is None
    assert "db-down" in caplog.text


@pytest.mark.asyncio
async def test_get_db_connection_retries_then_succeeds():
    """
    GIVEN DATABASE_URL is set and the first connection attempt fails
    WHEN a subsequent retry succeeds
    THEN _get_db_connection should return the connection object.
    """
    mock_conn = AsyncMock()
    with patch(
        "scrobblescope.cache._DATABASE_URL",
        "postgres://good:good@localhost/good",
    ):
        with patch.dict(
            "os.environ",
            {
                "DB_CONNECT_MAX_ATTEMPTS": "3",
                "DB_CONNECT_BASE_DELAY_SECONDS": "0",
            },
        ):
            with (
                patch("scrobblescope.cache.asyncpg") as mock_asyncpg,
                patch(
                    "scrobblescope.cache.asyncio.sleep", new_callable=AsyncMock
                ) as mock_sleep,
            ):
                mock_asyncpg.connect = AsyncMock(
                    side_effect=[Exception("temporary fail"), mock_conn]
                )
                result = await _get_db_connection()
    assert result is mock_conn
    assert mock_asyncpg.connect.await_count == 2
    mock_sleep.assert_awaited_once_with(0.0)


@pytest.mark.asyncio
async def test_get_db_connection_retry_exhaustion_returns_none():
    """
    GIVEN DATABASE_URL is set but all connection attempts fail
    WHEN retry budget is exhausted
    THEN _get_db_connection should return None.
    """
    with patch(
        "scrobblescope.cache._DATABASE_URL",
        "postgres://bad:bad@localhost/bad",
    ):
        with patch.dict(
            "os.environ",
            {
                "DB_CONNECT_MAX_ATTEMPTS": "3",
                "DB_CONNECT_BASE_DELAY_SECONDS": "0",
            },
        ):
            with (
                patch("scrobblescope.cache.asyncpg") as mock_asyncpg,
                patch(
                    "scrobblescope.cache.asyncio.sleep", new_callable=AsyncMock
                ) as mock_sleep,
            ):
                mock_asyncpg.connect = AsyncMock(
                    side_effect=Exception("connection refused")
                )
                result = await _get_db_connection()
    assert result is None
    assert mock_asyncpg.connect.await_count == 3
    assert mock_sleep.await_count == 2


@pytest.mark.asyncio
async def test_get_db_connection_passes_explicit_timeout_to_asyncpg():
    """
    GIVEN DATABASE_URL is set and DB_CONNECT_TIMEOUT_SECONDS is configured
    WHEN _get_db_connection calls asyncpg.connect
    THEN it passes that value as the timeout kwarg -- asyncpg.connect has no
        caller-set timeout otherwise, so an unreachable host (a paused
        container answers no SYN-ACK, rather than refusing) hangs for
        asyncpg's own 60s default per attempt instead of failing fast.
    """
    mock_conn = AsyncMock()
    with patch(
        "scrobblescope.cache._DATABASE_URL",
        "postgres://good:good@localhost/good",
    ):
        with patch.dict(
            "os.environ",
            {"DB_CONNECT_TIMEOUT_SECONDS": "2.5"},
        ):
            with patch("scrobblescope.cache.asyncpg") as mock_asyncpg:
                mock_asyncpg.connect = AsyncMock(return_value=mock_conn)
                result = await _get_db_connection()
    assert result is mock_conn
    mock_asyncpg.connect.assert_awaited_once_with(
        "postgres://good:good@localhost/good", timeout=2.5
    )


@pytest.mark.asyncio
async def test_get_db_connection_treats_timeout_as_an_ordinary_failure(caplog):
    """
    GIVEN every asyncpg.connect attempt raises asyncio.TimeoutError (what a
        capped, unreachable connection raises once the timeout kwarg fires)
    WHEN _get_db_connection exhausts its retry budget
    THEN it returns None and logs db-down, the same as any other connect
        failure -- a timeout is not a special case the caller must handle.
    """
    with patch(
        "scrobblescope.cache._DATABASE_URL",
        "postgres://bad:bad@localhost/bad",
    ):
        with patch.dict(
            "os.environ",
            {
                "DB_CONNECT_MAX_ATTEMPTS": "2",
                "DB_CONNECT_BASE_DELAY_SECONDS": "0",
                "DB_CONNECT_TIMEOUT_SECONDS": "1",
            },
        ):
            with (
                patch("scrobblescope.cache.asyncpg") as mock_asyncpg,
                patch("scrobblescope.cache.asyncio.sleep", new_callable=AsyncMock),
            ):
                mock_asyncpg.connect = AsyncMock(side_effect=TimeoutError())
                with caplog.at_level(logging.INFO):
                    result = await _get_db_connection()
    assert result is None
    assert mock_asyncpg.connect.await_count == 2
    assert "db-down" in caplog.text


@pytest.mark.asyncio
async def test_batch_lookup_metadata_empty_keys():
    """
    GIVEN an empty list of keys
    WHEN _batch_lookup_metadata is called
    THEN it should return an empty dict without making a DB call.
    """
    mock_conn = AsyncMock()
    result = await _batch_lookup_metadata(mock_conn, [])
    assert result == {}
    mock_conn.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_lookup_metadata_parses_track_durations():
    """
    GIVEN DB rows with track_durations as a JSON string
    WHEN _batch_lookup_metadata processes the results
    THEN it should parse them into Python dicts.
    """
    mock_row = {
        "artist_norm": "radiohead",
        "album_norm": "ok computer",
        "spotify_id": "abc123",
        "release_date": "1997-06-16",
        "album_image_url": "https://img.example.com/ok.jpg",
        "track_durations": '{"paranoid android": 383, "karma police": 264}',
    }
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[mock_row])

    result = await _batch_lookup_metadata(mock_conn, [("radiohead", "ok computer")])

    assert ("radiohead", "ok computer") in result
    td = result[("radiohead", "ok computer")]["track_durations"]
    assert isinstance(td, dict)
    assert td["paranoid android"] == 383
    assert td["karma police"] == 264


@pytest.mark.asyncio
async def test_batch_persist_metadata_empty_rows():
    """
    GIVEN an empty list of rows
    WHEN _batch_persist_metadata is called
    THEN it should return immediately without making a DB call.
    """
    mock_conn = AsyncMock()
    await _batch_persist_metadata(mock_conn, [])
    mock_conn.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_persist_metadata_upsert_call_shape():
    """
    GIVEN a list of metadata rows
    WHEN _batch_persist_metadata is called
    THEN it should execute a single INSERT ... unnest() statement
    with the correct array parameters.
    """
    mock_conn = AsyncMock()
    rows = [
        (
            "artist1",
            "album1",
            "sp1",
            "2025-01-01",
            "https://img/1.jpg",
            {"track a": 200},
        ),
        ("artist2", "album2", "sp2", "2024-06-15", None, {}),
    ]

    await _batch_persist_metadata(mock_conn, rows)

    mock_conn.execute.assert_awaited_once()
    call_args = mock_conn.execute.call_args
    sql = call_args[0][0]
    assert "INSERT INTO spotify_cache" in sql
    assert "unnest" in sql
    assert "ON CONFLICT" in sql
    # Verify array parameters
    assert call_args[0][1] == ["artist1", "artist2"]
    assert call_args[0][2] == ["album1", "album2"]
    assert call_args[0][3] == ["sp1", "sp2"]
    # track_durations should be JSON strings
    td_param = call_args[0][6]
    assert json.loads(td_param[0]) == {"track a": 200}
    assert json.loads(td_param[1]) == {}
