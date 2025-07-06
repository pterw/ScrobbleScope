# tests/test_app.py
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app import create_app
from app.services.lastfm_service import check_user_exists
from app.utils import normalize_name


@pytest.fixture
def client():
    """Create a test client for the Flask application."""

    app = create_app(testing=True)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """Ensure the index page renders correctly."""

    response = client.get("/")
    assert response.status_code == 200
    assert b"Filter Your Album Scrobbles!" in response.data


def test_normalize_name_simple():
    """normalize_name should strip punctuation and metadata words."""

    artist, album = normalize_name("The Beatles.", "Let It Be (Deluxe Edition)")
    assert artist == "the beatles"
    assert album == "let it be"


@pytest.mark.asyncio
async def test_check_user_exists_success():
    """check_user_exists returns True on 200 responses."""
    async_session = Mock()
    mock_response = AsyncMock(status=200)
    cm = AsyncMock()
    cm.__aenter__.return_value = mock_response
    async_session.get.return_value = cm

    with patch("app.services.lastfm_service.get_session", return_value=async_session):
        result = await check_user_exists("any_user")
    assert result is True


@pytest.mark.asyncio
async def test_check_user_does_not_exist():
    """check_user_exists returns False on 404 responses."""
    async_session = Mock()
    mock_response = AsyncMock(status=404)
    cm = AsyncMock()
    cm.__aenter__.return_value = mock_response
    async_session.get.return_value = cm

    with patch("app.services.lastfm_service.get_session", return_value=async_session):
        result = await check_user_exists("missing_user")
    assert result is False
