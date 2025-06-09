# tests/test_app.py
import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get("/")
    assert response.status_code == 200
    assert (
        b"Filter Your Album Scrobbles!" in response.data
    ), "Should find the main heading on the home page"
