import pytest

from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    with application.test_client() as client:
        yield client
