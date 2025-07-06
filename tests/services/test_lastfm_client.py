# tests/services/test_lastfm_client.py

import asyncio
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

# Import create_app for setting up app context if needed for client initialization
from app import create_app

# Import the LastFmClient from its new location
from app.services.lastfm_client import LastFmClient
from app.utils import (  # Needed for processing mock data
    normalize_name,
    normalize_track_name,
)


# Fixture to provide a LastFmClient instance with a proper app context
@pytest.fixture
def lastfm_client_instance():
    # Create a minimal Flask app to provide an app context
    app = create_app()
    app.config["LASTFM_API_KEY"] = "test_lastfm_key"  # Mock the API key for testing

    with app.app_context():
        client = LastFmClient()
        yield client


@pytest.mark.asyncio
async def test_check_user_exists_success(lastfm_client_instance):
    """
    GIVEN a LastFmClient instance
    WHEN check_user_exists is called with a username that exists
    THEN it should return True by mocking a successful API response.
    """
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"user": {"name": "testuser"}}
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await lastfm_client_instance.check_user_exists("testuser")
        assert result is True
        mock_get.assert_called_once()  # Verify the API call was made


@pytest.mark.asyncio
async def test_check_user_does_not_exist(lastfm_client_instance):
    """
    GIVEN a LastFmClient instance
    WHEN check_user_exists is called with a username that does NOT exist
    THEN it should return False by mocking a 404 API response.
    """
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await lastfm_client_instance.check_user_exists("nonexistent_user")
        assert result is False
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_recent_tracks_page_success(lastfm_client_instance):
    """
    GIVEN a LastFmClient instance
    WHEN fetch_recent_tracks_page_async is called for a valid page
    THEN it should return the parsed JSON data.
    """
    mock_json_data = {
        "recenttracks": {"track": [{"name": "Song1"}], "@attr": {"totalPages": "1"}}
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_json_data
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result = await lastfm_client_instance.fetch_recent_tracks_page_async(
                session, "testuser", 1672531200, 1704067199, 1
            )
            assert result == mock_json_data
            mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_recent_tracks_page_rate_limit(lastfm_client_instance):
    """
    GIVEN a LastFmClient instance
    WHEN fetch_recent_tracks_page_async encounters a 429 rate limit
    THEN it should retry and succeed on the second attempt.
    """
    mock_json_data = {"recenttracks": {"track": [{"name": "Song2"}]}}

    with patch("aiohttp.ClientSession.get") as mock_get, patch(
        "asyncio.sleep", new=AsyncMock()
    ) as mock_sleep:  # Mock sleep to prevent actual delay

        # First call returns 429, second call returns 200
        mock_response_429 = AsyncMock()
        mock_response_429.status = 429
        mock_response_429.headers = {
            "Retry-After": "0"
        }  # Set retry-after to 0 for immediate retry

        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.json.return_value = mock_json_data

        mock_get.return_value.__aenter__.side_effect = [
            mock_response_429,  # First call
            mock_response_200,  # Second call
        ]

        async with aiohttp.ClientSession() as session:
            result = await lastfm_client_instance.fetch_recent_tracks_page_async(
                session, "testuser", 1672531200, 1704067199, 1
            )
            assert result == mock_json_data
            assert mock_get.call_count == 2  # Expect two calls due to retry
            mock_sleep.assert_called_once_with(0)  # Assert sleep was called


@pytest.mark.asyncio
async def test_fetch_all_recent_tracks_async_multiple_pages(lastfm_client_instance):
    """
    GIVEN a LastFmClient instance
    WHEN fetch_all_recent_tracks_async is called for multiple pages
    THEN it should fetch all pages and combine results.
    """
    # Patch the internal fetch_recent_tracks_page_async method to control behavior
    with patch.object(
        lastfm_client_instance, "fetch_recent_tracks_page_async", new_callable=AsyncMock
    ) as mock_fetch_page:
        # Simulate 3 pages of data
        mock_fetch_page.side_effect = [
            {
                "recenttracks": {
                    "track": [{"name": "SongA"}],
                    "@attr": {"totalPages": "3"},
                }
            },
            {"recenttracks": {"track": [{"name": "SongB"}]}},
            {"recenttracks": {"track": [{"name": "SongC"}]}},
        ]

        # Call the method
        result = await lastfm_client_instance.fetch_all_recent_tracks_async(
            "testuser", 1672531200, 1704067199
        )

        # Assertions
        assert len(result) == 3
        assert result[0]["recenttracks"]["track"][0]["name"] == "SongA"
        assert result[1]["recenttracks"]["track"][0]["name"] == "SongB"
        assert result[2]["recenttracks"]["track"][0]["name"] == "SongC"
        # Initial call for total pages + 1 batch of 2 pages (BATCH=20, so it will do 1 initial + range(2,4))
        assert mock_fetch_page.call_count == 3


@pytest.mark.asyncio
async def test_fetch_top_albums_async_filtering(lastfm_client_instance):
    """
    GIVEN a LastFmClient instance
    WHEN fetch_top_albums_async is called
    THEN it should filter albums based on min_plays and min_tracks.
    """
    # Patch fetch_all_recent_tracks_async to control input data
    with patch.object(
        lastfm_client_instance, "fetch_all_recent_tracks_async", new_callable=AsyncMock
    ) as mock_fetch_all_tracks:
        # IMPORTANT: Use the exact structure that Last.fm API returns for artist/album
        mock_fetch_all_tracks.return_value = [
            {
                "recenttracks": {
                    "track": [
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track1",
                            "date": {"uts": "1672531200"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track1",
                            "date": {"uts": "1672531201"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track2",
                            "date": {"uts": "1672531202"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track3",
                            "date": {"uts": "1672531203"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track1",
                            "date": {"uts": "1672531204"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track2",
                            "date": {"uts": "1672531205"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track3",
                            "date": {"uts": "1672531206"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track1",
                            "date": {"uts": "1672531207"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track2",
                            "date": {"uts": "1672531208"},
                        },
                        {
                            "artist": {"#text": "Artist1"},
                            "album": {"#text": "Album1"},
                            "name": "Track3",
                            "date": {"uts": "1672531209"},
                        },  # Total 10 plays, 3 unique for Album1
                        {
                            "artist": {"#text": "Artist2"},
                            "album": {"#text": "Album2"},
                            "name": "TrackA",
                            "date": {"uts": "1672531210"},
                        },
                        {
                            "artist": {"#text": "Artist2"},
                            "album": {"#text": "Album2"},
                            "name": "TrackA",
                            "date": {"uts": "1672531211"},
                        },
                        {
                            "artist": {"#text": "Artist2"},
                            "album": {"#text": "Album2"},
                            "name": "TrackB",
                            "date": {"uts": "1672531212"},
                        },
                        {
                            "artist": {"#text": "Artist2"},
                            "album": {"#text": "Album2"},
                            "name": "TrackA",
                            "date": {"uts": "1672531213"},
                        },
                        {
                            "artist": {"#text": "Artist2"},
                            "album": {"#text": "Album2"},
                            "name": "TrackB",
                            "date": {"uts": "1672531214"},
                        },  # Total 5 plays, 2 unique for Album2
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531215"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531216"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531217"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531218"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531219"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531220"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531221"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531222"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531223"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531224"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531225"},
                        },
                        {
                            "artist": {"#text": "Artist3"},
                            "album": {"#text": "Album3"},
                            "name": "TrackX",
                            "date": {"uts": "1672531226"},
                        },  # Total 12 plays, 1 unique for Album3
                    ]
                }
            }
        ]

    # Test with default thresholds (min_plays=10, min_tracks=3)
    filtered_albums = await lastfm_client_instance.fetch_top_albums_async(
        "testuser", 2023
    )

    # Album1 should pass (10 plays, 3 unique tracks)
    # Album2 should fail (5 plays < 10)
    # Album3 should fail (1 unique track < 3)
    assert len(filtered_albums) == 1
    assert normalize_name("Artist1", "Album1") in filtered_albums
    assert filtered_albums[normalize_name("Artist1", "Album1")]["play_count"] == 10
    assert (
        len(filtered_albums[normalize_name("Artist1", "Album1")]["track_counts"]) == 3
    )

    # Test with custom thresholds
    filtered_albums_custom = await lastfm_client_instance.fetch_top_albums_async(
        "testuser", 2023, min_plays=5, min_tracks=2
    )
    # Album1, Album2 should pass. Album3 still fails (1 unique track < 2)
    assert len(filtered_albums_custom) == 2
    assert normalize_name("Artist1", "Album1") in filtered_albums_custom
    assert normalize_name("Artist2", "Album2") in filtered_albums_custom
    assert (
        filtered_albums_custom[normalize_name("Artist2", "Album2")]["play_count"] == 5
    )
    assert (
        len(filtered_albums_custom[normalize_name("Artist2", "Album2")]["track_counts"])
        == 2
    )
