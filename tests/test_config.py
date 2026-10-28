"""Tests for scrobblescope.config: environment values read at import."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scrobblescope import config

REPO_ROOT = Path(__file__).resolve().parents[1]
NAME = "LASTFM_PRECHECK_TIMEOUT_SECONDS"


def test_positive_seconds_uses_the_default_when_unset(monkeypatch):
    """An unset variable takes the default."""
    monkeypatch.delenv(NAME, raising=False)
    assert config._positive_seconds(NAME, "5") == 5.0


def test_positive_seconds_uses_the_default_the_caller_passes(monkeypatch):
    """The default is the caller's argument, not a constant inside the function."""
    monkeypatch.delenv(NAME, raising=False)
    assert config._positive_seconds(NAME, "7") == 7.0


def test_positive_seconds_treats_a_blank_value_as_unset(monkeypatch):
    """`NAME=` in a .env file means "not set", as for MUSICBRAINZ_CONTACT."""
    monkeypatch.setenv(NAME, "  ")
    assert config._positive_seconds(NAME, "5") == 5.0


def test_positive_seconds_reads_a_fractional_override(monkeypatch):
    """An override is read as a float, so sub-second budgets work."""
    monkeypatch.setenv(NAME, "2.5")
    assert config._positive_seconds(NAME, "5") == 2.5


@pytest.mark.parametrize("raw", ["0", "-1", "nan", "inf", "-inf", "five"])
def test_positive_seconds_refuses_a_value_that_cannot_bound_a_wait(monkeypatch, raw):
    """Zero, negative, non-finite and non-numeric values all refuse, naming the variable."""
    monkeypatch.setenv(NAME, raw)
    with pytest.raises(ValueError) as excinfo:
        config._positive_seconds(NAME, "5")
    assert NAME in str(excinfo.value)
    assert repr(raw) in str(excinfo.value)


def _import_config_in_child(value):
    """Import scrobblescope.config in a fresh interpreter with NAME=value."""
    env = {**os.environ, NAME: value}
    return subprocess.run(
        [
            sys.executable,
            "-c",
            f"from scrobblescope import config; print(config.{NAME})",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_the_precheck_timeout_is_read_through_the_validator():
    """The module constant itself refuses a bad value at import and reads a good one."""
    refused = _import_config_in_child("0")
    assert refused.returncode != 0
    assert NAME in refused.stderr
    assert "ValueError" in refused.stderr

    accepted = _import_config_in_child("0.25")
    assert accepted.returncode == 0, accepted.stderr
    assert accepted.stdout.strip() == "0.25"


MB_INTERVAL = "MUSICBRAINZ_MIN_INTERVAL_SECONDS"
MB_OLD_RATE = "MUSICBRAINZ_REQUESTS_PER_SECOND"


@pytest.mark.parametrize(
    "env, expected_interval, expected_warnings",
    [
        ({}, "1.2", 0),
        ({MB_INTERVAL: "2.0"}, "2.0", 0),
        ({MB_OLD_RATE: "5"}, "1.2", 1),
    ],
)
def test_musicbrainz_spacing_is_the_interval_setting_and_the_old_rate_is_ignored(
    env, expected_interval, expected_warnings
):
    """The interval setting (default 1.2s) sets the spacing; the old rate setting
    changes nothing and logs one warning naming the new variable."""
    base = {k: v for k, v in os.environ.items() if k not in (MB_INTERVAL, MB_OLD_RATE)}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from scrobblescope import config, utils; "
            f"print(config.{MB_INTERVAL}); "
            "print(utils._MUSICBRAINZ_THROTTLE._min_interval)",
        ],
        cwd=REPO_ROOT,
        env={**base, **env},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    # The throttle's real spacing follows the setting, not just the config value.
    assert result.stdout.split() == [expected_interval, expected_interval]
    assert result.stderr.count(MB_OLD_RATE) == expected_warnings
    assert result.stderr.count(MB_INTERVAL) == expected_warnings
