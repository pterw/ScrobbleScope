# tests/test_app.py

from unittest.mock import AsyncMock, patch

import pytest

# Import the create_app factory from your new app package
from app import create_app
from app.services.lastfm_client import (  # Needed for mocking in test_check_user_exists
    LastFmClient,
)
from app.tasks import background_task  # Import the background task for testing

# Import functions/classes from their new modular locations
from app.utils import normalize_name, normalize_track_name  # Added normalize_track_name


@pytest.fixture
def client():
    """Create a test client for the Flask application using the app factory."""
    app = create_app()
    app.config["TESTING"] = True
    # The SECRET_KEY is set via environment variables in your CI workflow,
    # but for local testing, ensure it's set or use a default.
    app.config["SECRET_KEY"] = "test_secret_key"

    # Mock API keys for testing purposes, if they are directly accessed in tests
    # (though typically they are accessed via app.config, which is handled by create_app)
    app.config["LASTFM_API_KEY"] = "test_lastfm_key"
    app.config["SPOTIFY_CLIENT_ID"] = "test_spotify_id"
    app.config["SPOTIFY_CLIENT_SECRET"] = "test_spotify_secret"

    with app.test_client() as client:
        # Before each test, clear the global state in app.state
        # This is important for isolated test runs when dealing with global state
        with app.app_context():
            from app.state import UNMATCHED, completed_results, current_progress

            current_progress.update(
                {"progress": 0, "message": "Initializing...", "error": False}
            )
            UNMATCHED.clear()
            completed_results.clear()
        yield client


def test_home_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid and contains key content.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Filter Your Album Scrobbles!" in response.data


def test_normalize_name_simple():
    """
    GIVEN an artist and album with common suffixes and punctuation
    WHEN normalize_name is called
    THEN check that the names are correctly stripped and lowercased.
    """
    artist, album = normalize_name("The Beatles.", "Let It Be (Deluxe Edition)")
    assert artist == "the beatles"
    assert album == "let it be"


@pytest.mark.asyncio
async def test_check_user_exists_success():
    """
    GIVEN a username that exists
    WHEN check_user_exists is called via LastFmClient
    THEN it should return True by mocking a successful API response.
    """
    # Create an instance of LastFmClient
    # This requires an app context for app.config access
    from flask import Flask

    temp_app = Flask(__name__)
    temp_app.config["LASTFM_API_KEY"] = "dummy_key"
    with temp_app.app_context():
        lastfm_client = LastFmClient()

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"user": {"name": "testuser"}}
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await lastfm_client.check_user_exists("testuser")
            assert result is True


@pytest.mark.asyncio
async def test_check_user_does_not_exist():
    """
    GIVEN a username that does NOT exist
    WHEN check_user_exists is called via LastFmClient
    THEN it should return False by mocking a 404 API response.
    """
    # Create an instance of LastFmClient within an app context
    from flask import Flask

    temp_app = Flask(__name__)
    temp_app.config["LASTFM_API_KEY"] = "dummy_key"
    with temp_app.app_context():
        lastfm_client = LastFmClient()

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await lastfm_client.check_user_exists("nonexistent_user")
            assert result is False


# The following tests are adapted to call the synchronous background_task
# and pass the app_instance from the client fixture.
@pytest.mark.asyncio
async def test_background_task_success(client):  # Use client fixture to get app context
    """
    Test background_task full flow with mocks for clients, ensuring
    progress updates and results caching are correct on success.
    """
    username = "testuser"
    year = 2023
    sort_mode = "playcount"
    release_scope = "same"
    min_plays = 10
    min_tracks = 3

    mock_filtered_albums = {
        normalize_name("ArtistA", "AlbumX"): {
            "play_count": 15,
            "track_counts": {
                normalize_track_name("Track1"): 15
            },  # Use normalized track name
            "original_artist": "ArtistA",
            "original_album": "AlbumX",
        }
    }
    mock_processed_results = [
        {
            "artist": "ArtistA",
            "album": "AlbumX",
            "play_count": 15,
            "play_time_seconds": 900,
        }
    ]

    # Patch the classes themselves so that when background_task instantiates them,
    # it gets our mock objects.
    with patch(
        "app.services.lastfm_client.LastFmClient", autospec=True
    ) as MockLastFmClient, patch(
        "app.services.spotify_client.SpotifyClient", autospec=True
    ) as MockSpotifyClient, patch(
        "app.tasks.process_albums", new_callable=AsyncMock
    ) as mock_process_albums, patch(
        "asyncio.sleep", new=AsyncMock()
    ) as mock_sleep:  # Mock sleep calls

        # Configure the return values of the *mock instances* that will be created
        mock_lastfm_instance = MockLastFmClient.return_value
        mock_lastfm_instance.check_user_exists.return_value = True
        mock_lastfm_instance.fetch_top_albums_async.return_value = mock_filtered_albums

        mock_spotify_instance = (
            MockSpotifyClient.return_value
        )  # Get the mock instance for SpotifyClient
        mock_process_albums.return_value = mock_processed_results

        # Run background task (now a synchronous function)
        background_task(  # Removed 'await' here
            client.application,  # Pass the Flask app instance from the client
            username,
            year,
            sort_mode,
            release_scope,
            None,
            None,
            min_plays,
            min_tracks,
        )

        # Assertions on progress updates
        with client.application.app_context():  # Ensure app context for state access in assertions
            from app.state import completed_results, current_progress

            assert current_progress["progress"] == 100
            assert (
                "Done!" in current_progress["message"]
            )  # This test is checking for success message
            assert current_progress["error"] is False

            # Verify client methods were called through the mocked instances
            mock_lastfm_instance.check_user_exists.assert_called_once_with(username)
            mock_lastfm_instance.fetch_top_albums_async.assert_called_once_with(
                username, year, min_plays=min_plays, min_tracks=min_tracks
            )
            # Ensure process_albums received the mocked SpotifyClient instance
            mock_process_albums.assert_called_once_with(
                mock_filtered_albums,
                year,
                sort_mode,
                release_scope,
                None,
                None,
                mock_spotify_instance,
            )

            # Verify results were cached
            cache_key = (
                username,
                year,
                sort_mode,
                release_scope,
                None,
                None,
                min_plays,
                min_tracks,
            )
            assert cache_key in completed_results
            assert completed_results[cache_key] == mock_processed_results


@pytest.mark.asyncio
async def test_background_task_user_not_found(client):  # Use client fixture
    """
    Test background_task handles user not found scenario gracefully.
    """
    username = "nonexistent_user"
    year = 2023
    sort_mode = "playcount"
    release_scope = "same"

    with patch(
        "app.services.lastfm_client.LastFmClient", autospec=True
    ) as MockLastFmClient, patch(
        "app.tasks.process_albums", new_callable=AsyncMock
    ) as mock_process_albums, patch(
        "asyncio.sleep", new=AsyncMock()
    ):  # Mock sleep calls

        # Configure the return value of the mock instance
        MockLastFmClient.return_value.check_user_exists.return_value = (
            False  # Simulate user not found
        )

        background_task(
            client.application, username, year, sort_mode, release_scope
        )  # Removed 'await'

        with client.application.app_context():
            from app.state import current_progress

            assert current_progress["progress"] == 100
            assert (
                f"Error: User '{username}' not found on Last.fm"
                in current_progress["message"]
            )
            assert current_progress["error"] is True

        MockLastFmClient.return_value.check_user_exists.assert_called_once_with(
            username
        )
        MockLastFmClient.return_value.fetch_top_albums_async.assert_not_called()
        mock_process_albums.assert_not_called()


@pytest.mark.asyncio
async def test_background_task_no_albums_found(client):  # Use client fixture
    """
    Test background_task handles scenario where no albums match initial criteria.
    """
    username = "testuser"
    year = 2023
    sort_mode = "playcount"
    release_scope = "same"

    with patch(
        "app.services.lastfm_client.LastFmClient", autospec=True
    ) as MockLastFmClient, patch(
        "app.services.spotify_client.SpotifyClient", autospec=True
    ) as MockSpotifyClient, patch(
        "app.tasks.process_albums", new_callable=AsyncMock
    ) as mock_process_albums, patch(
        "asyncio.sleep", new=AsyncMock()
    ):  # Mock sleep calls

        # Configure the return value of the mock instance
        MockLastFmClient.return_value.check_user_exists.return_value = True
        MockLastFmClient.return_value.fetch_top_albums_async.return_value = (
            {}
        )  # Simulate no albums found

        background_task(
            client.application, username, year, sort_mode, release_scope
        )  # Removed 'await'

        with client.application.app_context():
            from app.state import current_progress

            assert current_progress["progress"] == 100
            assert (
                "No albums found for the specified criteria."
                in current_progress["message"]
            )
            assert current_progress["error"] is False

        MockLastFmClient.return_value.check_user_exists.assert_called_once_with(
            username
        )
        MockLastFmClient.return_value.fetch_top_albums_async.assert_called_once()
        mock_process_albums.assert_not_called()
