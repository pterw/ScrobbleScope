"""Tests for app factory startup validation: the secret key (WP-4) and the
provider API keys (F-SWE-4)."""

import logging
from unittest.mock import patch

import pytest

from app import _validate_api_keys, _validate_secret_key, create_app

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


class TestValidateApiKeys:
    """``gunicorn app:app`` imports the module rather than running it, so the
    ``__main__`` check never fired in production (F-SWE-4). These pin the
    check to the factory instead, with the secret key's dev-mode leniency."""

    def test_raises_in_production_when_a_key_is_missing(self):
        with patch("scrobblescope.config.SPOTIFY_CLIENT_SECRET", None):
            with pytest.raises(RuntimeError, match="Refusing to start"):
                _validate_api_keys(is_dev_mode=False)

    def test_warns_in_dev_mode_when_a_key_is_missing(self, caplog):
        with (
            patch("scrobblescope.config.LASTFM_API_KEY", ""),
            caplog.at_level(logging.WARNING),
        ):
            _validate_api_keys(is_dev_mode=True)
        assert "missing api keys" in caplog.text.lower()

    def test_succeeds_in_production_when_every_key_is_set(self):
        with (
            patch("scrobblescope.config.LASTFM_API_KEY", "k"),
            patch("scrobblescope.config.SPOTIFY_CLIENT_ID", "i"),
            patch("scrobblescope.config.SPOTIFY_CLIENT_SECRET", "s"),
        ):
            _validate_api_keys(is_dev_mode=False)

    def test_create_app_refuses_to_start_in_production_without_keys(self):
        """The regression itself: the factory, which is what gunicorn reaches,
        must run the check -- not only the ``__main__`` block."""
        with (
            patch("app.debug_mode", False),
            patch("scrobblescope.config.LASTFM_API_KEY", None),
        ):
            with pytest.raises(RuntimeError, match="Refusing to start"):
                create_app()
