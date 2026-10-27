"""Tests for app factory startup validation: the secret key (WP-4) and the
provider API keys (F-SWE-4)."""

import logging
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from app import _validate_api_keys, _validate_secret_key, create_app
from scrobblescope.api_logging import RedactingFormatter

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


def test_every_root_log_handler_redacts_the_api_key():
    """Both channels app.py installs must redact: the rotating file and stdout,
    the production log channel. pytest's own capture handlers are subclasses,
    so an exact type match picks out only the two app.py built."""
    from logging.handlers import RotatingFileHandler

    handlers = logging.getLogger().handlers
    file_handlers = [h for h in handlers if type(h) is RotatingFileHandler]
    stdout_handlers = [h for h in handlers if type(h) is logging.StreamHandler]

    assert file_handlers, "no RotatingFileHandler on the root logger"
    assert stdout_handlers, "no stdout StreamHandler on the root logger"
    for handler in file_handlers + stdout_handlers:
        assert isinstance(handler.formatter, RedactingFormatter), (
            f"{type(handler).__name__} has no RedactingFormatter"
        )


REPO_ROOT = Path(__file__).resolve().parents[1]


def _import_app_in_child(tmp_path, *, prelude="", epilogue="", extra_env=None):
    """Import ``app`` in a fresh interpreter and return the completed process.

    Module-level start-up work (stream setup, logging handlers) runs only at
    first import, so it can only be observed in a new process. The child runs
    in *tmp_path* so its ``logs/`` directory lands there, with DEBUG_MODE=1 so
    a missing SECRET_KEY or API key warns instead of refusing to start.
    """
    python_path = os.pathsep.join(
        [str(REPO_ROOT), *filter(None, [os.environ.get("PYTHONPATH")])]
    )
    env = {**os.environ, "PYTHONPATH": python_path, "DEBUG_MODE": "1"}
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, "-c", f"{prelude}\nimport app\n{epilogue}"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        timeout=120,
    )


def test_importing_the_app_runs_no_shell_command(tmp_path):
    """Importing the app spawns no shell: no `os.system`, no `subprocess.Popen`.

    `subprocess.run`, `subprocess.call` and `os.popen` all construct a Popen,
    so recording Popen construction covers them as well as `os.system`.
    """
    prelude = (
        "import os, subprocess\n"
        "system_calls = []\n"
        "popen_calls = []\n"
        "os.system = lambda command: system_calls.append(command) or 0\n"
        "_Popen = subprocess.Popen\n"
        "class RecordingPopen(_Popen):\n"
        "    def __init__(self, *args, **kwargs):\n"
        "        popen_calls.append(args)\n"
        "        super().__init__(*args, **kwargs)\n"
        "subprocess.Popen = RecordingPopen"
    )
    epilogue = "print('SYSTEM_CALLS', system_calls)\nprint('POPEN_CALLS', popen_calls)"
    result = _import_app_in_child(tmp_path, prelude=prelude, epilogue=epilogue)
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert b"SYSTEM_CALLS []" in result.stdout
    assert b"POPEN_CALLS []" in result.stdout


def test_a_log_line_reaches_stdout_whole_when_its_encoding_is_legacy(tmp_path):
    """Log lines with characters a legacy code page lacks reach stdout and stderr intact.

    stdout and stderr here are pipes under a cp1252 encoding, as for a
    redirected log or a process manager on a legacy locale.
    """
    probe = "probe \u5742\u672c\u9f8d\u4e00 \u2192 done"
    result = _import_app_in_child(
        tmp_path,
        extra_env={"PYTHONIOENCODING": "cp1252"},
        epilogue=(
            "import logging, sys\n"
            f"logging.warning({probe!r})\n"
            f"sys.stderr.write({probe!r} + '\\n')\n"
            "sys.stderr.flush()"
        ),
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert probe in result.stdout.decode("utf-8")
    assert probe in result.stderr.decode("utf-8")
    assert b"Logging error" not in result.stderr


@pytest.mark.parametrize(("minutes", "starts"), [("20", 1), (None, 0)])
def test_create_app_starts_the_idle_watch_only_when_the_env_var_is_set(minutes, starts):
    env = {"IDLE_EXIT_MINUTES": minutes} if minutes else {}
    with patch.dict(os.environ, env):
        if minutes is None:
            os.environ.pop("IDLE_EXIT_MINUTES", None)
        with (
            patch("scrobblescope.idle_exit.IdleWatch.start") as start,
            patch("scrobblescope.idle_exit.IdleWatch.touch") as touch,
        ):
            application = create_app()
            application.test_client().get("/")
    assert start.call_count == starts
    # A request through the returned app renews the watch only when it is attached.
    assert (touch.call_count > 0) == bool(starts)
