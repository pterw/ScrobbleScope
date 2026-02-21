import os

import pytest

# Provide a safe SECRET_KEY for tests so the startup guard in create_app()
# does not raise. Must be set before app.py is imported.
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-min-16chars!!")

from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    with application.test_client() as client:
        yield client


@pytest.fixture
def csrf_app_client():
    """Test client with CSRF protection active (WTF_CSRF_ENABLED not disabled).

    Use this fixture for tests that verify CSRF enforcement behaviour.
    The default ``client`` fixture disables CSRF for convenience; this one
    does not, so token validation runs as it would in production.
    """
    application = create_app()
    application.config["TESTING"] = True
    with application.test_client() as csrf_client:
        yield csrf_client
