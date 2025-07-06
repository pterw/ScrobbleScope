# tests/tasks/test_tasks.py

import asyncio
import logging
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import functions and classes from the new modular structure
from app import create_app  # To get app instance from app_context fixture

# Import LastFmClient and SpotifyClient for type hinting in mocks, though patched
from app.services.lastfm_client import LastFmClient
from app.services.spotify_client import SpotifyClient
from app.state import (
    UNMATCHED,
    completed_results,
    current_progress,
    progress_lock,
    unmatched_lock,
)
from app.tasks import background_task, process_albums, run_async_in_thread

# Corrected import for normalize_track_name and other utils
from app.utils import (
    format_seconds,
    get_filter_description,
    normalize_name,
    normalize_track_name,
)


# Fixture to reset global state before each test
@pytest.fixture(autouse=True)
def reset_global_state():
    with progress_lock:
        current_progress.update(
            {"progress": 0, "message": "Initializing...", "error": False}
        )
    with unmatched_lock:
        UNMATCHED.clear()
    completed_results.clear()


# Fixture for app instance, needed for clients that access current_app.config
@pytest.fixture
def app_instance():
    # Create the Flask app instance once per test function where this fixture is used
    app = create_app()
    app.config["LASTFM_API_KEY"] = "dummy_lastfm_key"
    app.config["SPOTIFY_CLIENT_ID"] = "dummy_spotify_id"
    app.config["SPOTIFY_CLIENT_SECRET"] = "dummy_spotify_secret"

    # Push and yield from within the app context for the entire test
    with app.app_context():
        yield app


@pytest.mark.asyncio
async def test_run_async_in_thread_success(app_instance):  # Use app_instance fixture
    """
    Test that run_async_in_thread executes a coroutine successfully
    and returns its result.
    """

    async def sample_coroutine():
        await asyncio.sleep(0.01)  # Simulate async work
        return "Task Completed"

    result = run_async_in_thread(app_instance, sample_coroutine)  # Pass app_instance
    assert result == "Task Completed"
    with progress_lock:
        assert not current_progress["error"]


@pytest.mark.asyncio
async def test_run_async_in_thread_error_handling(
    app_instance,
):  # Use app_instance fixture
    """
    Test that run_async_in_thread catches exceptions from coroutines
    and updates global progress state.
    """

    async def failing_coroutine():
        await asyncio.sleep(0.01)
        raise ValueError("Simulated error in async task")

    with pytest.raises(ValueError, match="Simulated error in async task"):
        run_async_in_thread(app_instance, failing_coroutine)  # Pass app_instance

    with progress_lock:
        assert current_progress["error"] is True
        assert "Error: Simulated error in async task" in current_progress["message"]


@pytest.mark.asyncio
async def test_process_albums_success(app_instance):  # Use app_instance fixture
    """
    Test process_albums with successful Spotify API mocks,
    ensuring correct filtering and sorting.
    """
    mock_filtered_albums = {
        normalize_name("ArtistA", "AlbumX"): {
            "play_count": 15,
            "track_counts": {
                normalize_track_name("Track1"): 5,
                normalize_track_name("Track2"): 5,
                normalize_track_name("Track3"): 5,
            },
            "original_artist": "ArtistA",
            "original_album": "AlbumX",
        },
        normalize_name("ArtistB", "AlbumY"): {
            "play_count": 10,
            "track_counts": {
                normalize_track_name("TrackA"): 3,
                normalize_track_name("TrackB"): 7,
            },
            "original_artist": "ArtistB",
            "original_album": "AlbumY",
        },
    }
    mock_year = 2023
    mock_sort_mode = "playtime"
    mock_release_scope = "same"
    mock_decade = None
    mock_release_year = None

    with patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_access_token",
        new_callable=AsyncMock,
    ) as mock_token, patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_album_release_date",
        new_callable=AsyncMock,
    ) as mock_release_date, patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_track_durations",
        new_callable=AsyncMock,
    ) as mock_durations:

        mock_token.return_value = "dummy_spotify_token"

        mock_release_date.side_effect = [
            {
                "release_date": "2023-03-15",
                "album_image": "http://coverX.jpg",
                "id": "album_id_X",
            },
            {
                "release_date": "2023-01-01",
                "album_image": "http://coverY.jpg",
                "id": "album_id_Y",
            },
        ]
        mock_durations.side_effect = [
            {
                normalize_track_name("Track1"): 60,
                normalize_track_name("Track2"): 90,
                normalize_track_name("Track3"): 120,
            },  # AlbumX durations
            {
                normalize_track_name("TrackA"): 100,
                normalize_track_name("TrackB"): 150,
            },  # AlbumY durations
        ]

        # Use the actual SpotifyClient but with mocked methods
        with app_instance.app_context():  # Ensure app context for SpotifyClient instantiation
            spotify_client_real_instance = SpotifyClient()
            spotify_client_real_instance.fetch_spotify_access_token = mock_token
            spotify_client_real_instance.fetch_spotify_album_release_date = (
                mock_release_date
            )
            spotify_client_real_instance.fetch_spotify_track_durations = mock_durations

            results = await process_albums(
                mock_filtered_albums,
                mock_year,
                mock_sort_mode,
                mock_release_scope,
                mock_decade,
                mock_release_year,
                spotify_client_real_instance,
            )

        assert len(results) == 2

        album_x_result = next((a for a in results if a["album"] == "AlbumX"), None)
        album_y_result = next((a for a in results if a["album"] == "AlbumY"), None)

        assert album_x_result is not None
        assert album_x_result["play_time_seconds"] == 1350
        assert album_x_result["release_date"] == "2023-03-15"
        assert album_x_result["album_image"] == "http://coverX.jpg"

        assert album_y_result is not None
        assert album_y_result["play_time_seconds"] == 1350
        assert album_y_result["release_date"] == "2023-01-01"
        assert album_y_result["album_image"] == "http://coverY.jpg"

        mock_token.assert_called_once()  # Corrected assertion syntax
        assert mock_release_date.call_count == 2  # Corrected assertion syntax
        assert mock_durations.call_count == 2  # Corrected assertion syntax


@pytest.mark.asyncio
async def test_process_albums_filter_unmatched_release_year(
    app_instance,
):  # Use app_instance fixture
    """
    Test process_albums correctly identifies and logs albums
    that do not match the specified release year criteria.
    """
    mock_filtered_albums = {
        normalize_name("ArtistC", "AlbumZ"): {
            "play_count": 20,
            "track_counts": {
                normalize_track_name("Track1"): 10,
                normalize_track_name("Track2"): 10,
            },
            "original_artist": "ArtistC",
            "original_album": "AlbumZ",
        }
    }
    mock_year = 2023
    mock_sort_mode = "playcount"
    mock_release_scope = "same"  # Expect release year to be 2023
    mock_decade = None
    mock_release_year = None

    with patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_access_token",
        new_callable=AsyncMock,
    ) as mock_token, patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_album_release_date",
        new_callable=AsyncMock,
    ) as mock_release_date, patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_track_durations",
        new_callable=AsyncMock,
    ) as mock_durations:

        mock_token.return_value = "dummy_spotify_token"
        mock_release_date.return_value = {
            "release_date": "2022-07-01",
            "album_image": "http://coverZ.jpg",
            "id": "album_id_Z",
        }
        mock_durations.return_value = {}

        with app_instance.app_context():  # Ensure app context for SpotifyClient instantiation
            spotify_client_real_instance = SpotifyClient()
            spotify_client_real_instance.fetch_spotify_access_token = mock_token
            spotify_client_real_instance.fetch_spotify_album_release_date = (
                mock_release_date
            )
            spotify_client_real_instance.fetch_spotify_track_durations = mock_durations

            results = await process_albums(
                mock_filtered_albums,
                mock_year,
                mock_sort_mode,
                mock_release_scope,
                mock_decade,
                mock_release_year,
                spotify_client_real_instance,
            )

        assert len(results) == 0
        with unmatched_lock:
            # Correct assertion: UNMATCHED keys are strings like "artistc|albumz"
            unmatched_key_str = "|".join(normalize_name("ArtistC", "AlbumZ"))
            assert unmatched_key_str in UNMATCHED
            assert (
                UNMATCHED[unmatched_key_str]["reason"]
                == "Released in 2022 instead of 2023"
            )

        mock_token.assert_called_once()  # Corrected assertion syntax
        mock_release_date.assert_called_once()  # Corrected assertion syntax
        mock_durations.assert_not_called()


@pytest.mark.asyncio
async def test_process_albums_no_spotify_match(
    app_instance,
):  # Use app_instance fixture
    """
    Test process_albums correctly handles albums with no Spotify match,
    and updates UNMATCHED.
    """
    mock_filtered_albums = {
        normalize_name("ArtistD", "AlbumMissing"): {
            "play_count": 50,
            "track_counts": {
                normalize_track_name("TrackA"): 25,
                normalize_track_name("TrackB"): 25,
            },
            "original_artist": "ArtistD",
            "original_album": "AlbumMissing",
        }
    }
    mock_year = 2023
    mock_sort_mode = "playcount"
    mock_release_scope = "same"
    mock_decade = None
    mock_release_year = None

    with patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_access_token",
        new_callable=AsyncMock,
    ) as mock_token, patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_album_release_date",
        new_callable=AsyncMock,
    ) as mock_release_date, patch(
        "app.services.spotify_client.SpotifyClient.fetch_spotify_track_durations",
        new_callable=AsyncMock,
    ) as mock_durations:

        mock_token.return_value = "dummy_spotify_token"
        mock_release_date.return_value = {}
        mock_durations.return_value = {}

        with app_instance.app_context():  # Ensure app context for SpotifyClient instantiation
            spotify_client_real_instance = SpotifyClient()
            spotify_client_real_instance.fetch_spotify_access_token = mock_token
            spotify_client_real_instance.fetch_spotify_album_release_date = (
                mock_release_date
            )
            spotify_client_real_instance.fetch_spotify_track_durations = mock_durations

            results = await process_albums(
                mock_filtered_albums,
                mock_year,
                mock_sort_mode,
                mock_release_scope,
                mock_decade,
                mock_release_year,
                spotify_client_real_instance,
            )

        assert len(results) == 0
        with unmatched_lock:
            # Correct assertion: UNMATCHED keys are strings like "artistd|albummissing"
            unmatched_key_str = "|".join(normalize_name("ArtistD", "AlbumMissing"))
            assert unmatched_key_str in UNMATCHED
            assert UNMATCHED[unmatched_key_str]["reason"] == "No match found on Spotify"

        mock_token.assert_called_once()  # Corrected assertion syntax
        mock_release_date.assert_called_once()  # Corrected assertion syntax
        mock_durations.assert_not_called()


# Test background_task
@pytest.mark.asyncio
async def test_background_task_success(
    app_instance,
):  # Use app_instance fixture to get app context
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
    # it gets our mock objects. Removed autospec=True for more flexible mocking.
    with patch("app.services.lastfm_client.LastFmClient") as MockLastFmClient, patch(
        "app.services.spotify_client.SpotifyClient"
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
            app_instance.application,  # Pass the Flask app instance from the client
            username,
            year,
            sort_mode,
            release_scope,
            None,
            None,
            min_plays,
            min_tracks,
        )

        # Assertions must be INSIDE this 'with' block where mocks are in scope
        with app_instance.application.app_context():  # Ensure app context for state access in assertions
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
@pytest.mark.asyncio
async def test_background_task_user_not_found(client):  # Use client fixture
    """
    Test background_task handles user not found scenario gracefully.
    """
    username = "nonexistent_user"
    year = 2023
    sort_mode = "playcount"
    release_scope = "same"

    # Removed autospec=True for more flexible mocking.
    with patch("app.services.lastfm_client.LastFmClient") as MockLastFmClient, patch(
        "app.tasks.process_albums", new_callable=AsyncMock
    ) as mock_process_albums, patch(
        "asyncio.sleep", new=AsyncMock()
    ):  # Mock sleep calls

        # Configure the return value of the mock instance
        mock_lastfm_instance = MockLastFmClient.return_value
        mock_lastfm_instance.check_user_exists.return_value = (
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

            mock_lastfm_instance.check_user_exists.assert_called_once_with(username)
            mock_lastfm_instance.fetch_top_albums_async.assert_not_called()
            mock_process_albums.assert_not_called()


@pytest.mark.asyncio
async def test_background_task_no_albums_found(app_instance):  # Use client fixture
    """
    Test background_task handles scenario where no albums match initial criteria.
    """
    username = "testuser"
    year = 2023
    sort_mode = "playcount"
    release_scope = "same"

    # Removed autospec=True for more flexible mocking.
    with patch("app.services.lastfm_client.LastFmClient") as MockLastFmClient, patch(
        "app.services.spotify_client.SpotifyClient"
    ) as MockSpotifyClient, patch(
        "app.tasks.process_albums", new_callable=AsyncMock
    ) as mock_process_albums, patch(
        "asyncio.sleep", new=AsyncMock()
    ):  # Mock sleep calls

        # Configure the return value of the mock instance
        mock_lastfm_instance = MockLastFmClient.return_value
        mock_lastfm_instance.check_user_exists.return_value = True
        mock_lastfm_instance.fetch_top_albums_async.return_value = (
            {}
        )  # Simulate no albums found

        background_task(
            app_instance.application, username, year, sort_mode, release_scope
        )  # Removed 'await'

        with app_instance.application.app_context():
            from app.state import current_progress

            assert current_progress["progress"] == 100
            assert (
                "No albums found for the specified criteria."
                in current_progress["message"]
            )
            assert current_progress["error"] is False

            mock_lastfm_instance.check_user_exists.assert_called_once_with(username)
            mock_lastfm_instance.fetch_top_albums_async.assert_called_once()
            mock_process_albums.assert_not_called()
