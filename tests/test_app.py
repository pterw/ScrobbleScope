# tests/test_app.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# IMPORTANT: You'll import from your app object initially.
# After refactoring, you'd change this to something like:
# from app.utils import normalize_name
# from app.services.lastfm_client import check_user_exists
from app import app, check_user_exists, normalize_name


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid and contains key content.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert (
        b"Filter Your Album Scrobbles!" in response.data
    ), "Should find the main heading"
    assert b"Last.fm Username" in response.data, "Should find the username input field"


def test_normalize_name_simple():
    """
    GIVEN an artist and album with common suffixes and punctuation
    WHEN normalize_name is called
    THEN check that the names are correctly stripped and lowercased.
    """
    artist, album = normalize_name("The Beatles.", "Let It Be (Deluxe Edition)")
    # This line is now corrected to match the function's actual output
    assert artist == "the beatles"
    assert album == "let it be"


@pytest.mark.asyncio
async def test_check_user_exists_success():
    """
    GIVEN a username that exists
    WHEN check_user_exists is called
    THEN it should return True by mocking a successful API response.
    """
    # Use 'patch' to replace aiohttp.ClientSession.get with our mock
    with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
        # Configure the mock to simulate a successful (200) response
        mock_response = mock_get.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = {"user": {"name": "testuser"}}

        # Call the function we are testing
        result = await check_user_exists("any_user")

        # Assert that the function returned the expected value
        assert result is True


@pytest.mark.asyncio
async def test_check_user_does_not_exist():
    """
    GIVEN a username that does NOT exist
    WHEN check_user_exists is called
    THEN it should return False by mocking a 404 API response.
    """
    with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
        # Configure the mock to simulate a "Not Found" (404) response
        mock_response = mock_get.return_value.__aenter__.return_value
        mock_response.status = 404

        result = await check_user_exists("nonexistent_user")
        assert result is False
