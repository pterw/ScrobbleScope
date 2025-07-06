# tests/services/test_spotify_client.py

import asyncio
import time
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

# Import create_app for setting up app context if needed for client initialization
from app import create_app

# Import the SpotifyClient from its new location
from app.services.spotify_client import SpotifyClient
from app.utils import (  # Needed for mocking external dependencies
    normalize_name,
    normalize_track_name,
)


# Fixture to provide a SpotifyClient instance with a mocked app context
@pytest.fixture
def spotify_client_instance():
    # Create a minimal Flask app to provide an app context
    app = create_app()
    app.config["SPOTIFY_CLIENT_ID"] = "test_spotify_id"
    app.config["SPOTIFY_CLIENT_SECRET"] = "test_spotify_secret"

    with app.app_context():
        client = SpotifyClient()
        yield client


# Reset the global spotify_token_cache before each test involving it
@pytest.fixture(autouse=True)
def reset_spotify_token_cache():
    from app.services.spotify_client import spotify_token_cache

    spotify_token_cache["token"] = None
    spotify_token_cache["expires_at"] = 0


@pytest.mark.asyncio
async def test_fetch_spotify_access_token_new_token(spotify_client_instance):
    """
    GIVEN a SpotifyClient instance and no cached token
    WHEN fetch_spotify_access_token is called
    THEN it should fetch a new token and cache it.
    """
    mock_token_data = {"access_token": "new_test_token", "expires_in": 3600}

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_token_data
        mock_post.return_value.__aenter__.return_value = mock_response

        token = await spotify_client_instance.fetch_spotify_access_token()
        assert token == "new_test_token"
        mock_post.assert_called_once()
        # Verify cache was updated
        from app.services.spotify_client import spotify_token_cache

        assert spotify_token_cache["token"] == "new_test_token"
        assert spotify_token_cache["expires_at"] > time.time()


@pytest.mark.asyncio
async def test_fetch_spotify_access_token_cached_token(spotify_client_instance):
    """
    GIVEN a SpotifyClient instance with a valid cached token
    WHEN fetch_spotify_access_token is called
    THEN it should return the cached token without making an API call.
    """
    from app.services.spotify_client import spotify_token_cache

    spotify_token_cache["token"] = "cached_test_token"
    spotify_token_cache["expires_at"] = time.time() + 1000  # Expires in the future

    with patch("aiohttp.ClientSession.post") as mock_post:
        token = await spotify_client_instance.fetch_spotify_access_token()
        assert token == "cached_test_token"
        mock_post.assert_not_called()  # No API call should be made


@pytest.mark.asyncio
async def test_fetch_spotify_album_release_date_success(spotify_client_instance):
    """
    GIVEN a SpotifyClient instance
    WHEN fetch_spotify_album_release_date is called with valid artist/album
    THEN it should return the correct release date, image, and id.
    """
    mock_spotify_data = {
        "albums": {
            "items": [
                {
                    "release_date": "2000-01-01",
                    "images": [{"url": "http://example.com/cover.jpg"}],
                    "id": "album_id_123",
                }
            ]
        }
    }
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_spotify_data
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result = await spotify_client_instance.fetch_spotify_album_release_date(
                session, "Test Artist", "Test Album", "dummy_token"
            )
            assert result["release_date"] == "2000-01-01"
            assert result["album_image"] == "http://example.com/cover.jpg"
            assert result["id"] == "album_id_123"
            mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_spotify_album_release_date_no_match_then_relaxed(
    spotify_client_instance,
):
    """
    GIVEN a SpotifyClient instance
    WHEN fetch_spotify_album_release_date finds no initial match but succeeds on relaxed query
    THEN it should return data from the relaxed query.
    """
    mock_empty_data = {"albums": {"items": []}}
    mock_relaxed_data = {
        "albums": {
            "items": [
                {
                    "release_date": "2005-05-05",
                    "images": [{"url": "http://example.com/relaxed_cover.png"}],
                    "id": "relaxed_id_456",
                }
            ]
        }
    }
    with patch("aiohttp.ClientSession.get") as mock_get:
        # First call for precise query, second for relaxed
        mock_response_empty = AsyncMock(
            status=200, json=AsyncMock(return_value=mock_empty_data)
        )
        mock_response_relaxed = AsyncMock(
            status=200, json=AsyncMock(return_value=mock_relaxed_data)
        )
        mock_get.return_value.__aenter__.side_effect = [
            mock_response_empty,
            mock_response_relaxed,
        ]

        async with aiohttp.ClientSession() as session:
            result = await spotify_client_instance.fetch_spotify_album_release_date(
                session, "Test Artist", "Very Specific Album", "dummy_token"
            )
            assert result["release_date"] == "2005-05-05"
            assert result["album_image"] == "http://example.com/relaxed_cover.png"
            assert result["id"] == "relaxed_id_456"
            assert mock_get.call_count == 2  # Two calls expected


@pytest.mark.asyncio
async def test_fetch_spotify_album_release_date_no_match_at_all(
    spotify_client_instance,
):
    """
    GIVEN a SpotifyClient instance
    WHEN fetch_spotify_album_release_date finds no match even with relaxed query
    THEN it should return an empty dictionary.
    """
    mock_empty_data = {"albums": {"items": []}}
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response_empty = AsyncMock(
            status=200, json=AsyncMock(return_value=mock_empty_data)
        )
        mock_get.return_value.__aenter__.return_value = mock_response_empty
        mock_get.return_value.__aenter__.side_effect = [
            mock_response_empty,
            mock_response_empty,
        ]  # Both fail

        async with aiohttp.ClientSession() as session:
            result = await spotify_client_instance.fetch_spotify_album_release_date(
                session, "Nonexistent Artist", "Nonexistent Album", "dummy_token"
            )
            assert result == {}
            assert mock_get.call_count == 2  # Two calls expected (original + relaxed)


@pytest.mark.asyncio
async def test_fetch_spotify_track_durations_success(spotify_client_instance):
    """
    GIVEN a SpotifyClient instance
    WHEN fetch_spotify_track_durations is called for a valid album
    THEN it should return a dictionary of normalized track names to durations.
    """
    mock_track_data = {
        "items": [
            {"name": "Song 1 (Remix)", "duration_ms": 180000},  # 3 mins
            {"name": "Song 2", "duration_ms": 240000},  # 4 mins
        ]
    }
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_track_data
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result = await spotify_client_instance.fetch_spotify_track_durations(
                session, "album_id_123", "dummy_token"
            )
            assert normalize_track_name("Song 1 (Remix)") in result
            assert result[normalize_track_name("Song 1 (Remix)")] == 180
            assert normalize_track_name("Song 2") in result
            assert result[normalize_track_name("Song 2")] == 240
            assert len(result) == 2
            mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_spotify_track_durations_empty(spotify_client_instance):
    """
    GIVEN a SpotifyClient instance
    WHEN fetch_spotify_track_durations is called for an album with no tracks
    THEN it should return an empty dictionary.
    """
    mock_empty_track_data = {"items": []}
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_empty_track_data
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result = await spotify_client_instance.fetch_spotify_track_durations(
                session, "album_id_empty", "dummy_token"
            )
            assert result == {}
            mock_get.assert_called_once()
