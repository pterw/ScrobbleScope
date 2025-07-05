# tests/test_app.py
from unittest.mock import AsyncMock, patch

import pytest

# Imports from your application
from app import check_user_exists, create_app, normalize_name


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app()
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
    WHEN check_user_exists is called
    THEN it should return True by mocking a successful API response.
    """
    # Patch 'aiohttp.ClientSession.get'. Its return value must be an
    # object that supports the `async with` protocol.
    with patch("aiohttp.ClientSession.get") as mock_get:
        # Create a mock for the response object itself.
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"user": {"name": "testuser"}}

        # This is the key: Configure the return value of the mock's __aenter__
        # method. This correctly simulates the object `async with` will use.
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await check_user_exists("any_user")
        assert result is True


@pytest.mark.asyncio
async def test_check_user_does_not_exist():
    """
    GIVEN a username that does NOT exist
    WHEN check_user_exists is called
    THEN it should return False by mocking a 404 API response.
    """
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await check_user_exists("nonexistent_user")
        assert result is False
