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


class TestSecurityHeaders:
    def test_global_security_headers_are_applied(self, client):
        response = client.get("/test-404-nonexistent-route")

        # Test headers are applied to the 404 response
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert (
            response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        )
