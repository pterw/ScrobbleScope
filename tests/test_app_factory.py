"""Tests for app factory startup secret-key validation (WP-4)."""

import logging

import pytest

from app import _validate_secret_key

_STRONG_KEY = "a" * 64


class TestValidateSecretKey:
    def test_raises_in_production_when_key_is_missing(self):
        with pytest.raises(RuntimeError, match="Refusing to start"):
            _validate_secret_key("", is_dev_mode=False)

    def test_raises_in_production_when_key_is_dev(self):
        with pytest.raises(RuntimeError, match="Refusing to start"):
            _validate_secret_key("dev", is_dev_mode=False)

    def test_raises_in_production_when_key_is_changeme(self):
        with pytest.raises(RuntimeError, match="Refusing to start"):
            _validate_secret_key("changeme_in_production", is_dev_mode=False)

    def test_raises_in_production_when_key_is_too_short(self):
        with pytest.raises(RuntimeError, match="Refusing to start"):
            _validate_secret_key("tooshort", is_dev_mode=False)

    def test_warns_in_dev_mode_when_key_is_weak(self, caplog):
        with caplog.at_level(logging.WARNING):
            _validate_secret_key("dev", is_dev_mode=True)
        assert "insecure" in caplog.text.lower()

    def test_succeeds_with_strong_key_in_production(self):
        _validate_secret_key(_STRONG_KEY, is_dev_mode=False)

def test_security_headers(monkeypatch):
    """GIVEN the Flask application factory
    WHEN a request is made to an endpoint
    THEN the response should contain the required security headers.
    """
    monkeypatch.setenv("SECRET_KEY", _STRONG_KEY)

    from app import create_app
    app = create_app()
    app.testing = True

    with app.test_client() as client:
        # Requesting a non-existent route just to get a response
        # that passes through after_request hooks
        response = client.get('/non_existent_route_for_headers_test')

        headers = response.headers
        assert headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
