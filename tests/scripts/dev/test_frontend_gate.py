"""Tests for the repository-owned frontend gate runtime.

Every test here is unit level and starts no browser. The browser behaviour is
covered by running the gate itself, which is what the Quality Gate does.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev.frontend_gate import (
    SETUP_COMMAND,
    FrontendGateError,
    _launch_chromium,
    _load_playwright,
    run_checks,
    serve_app,
)


def test_a_missing_playwright_package_names_the_setup_command() -> None:
    """The gate never installs tooling implicitly; it tells the operator how."""
    with (
        patch.dict("sys.modules", {"playwright.sync_api": None}),
        pytest.raises(FrontendGateError) as error,
    ):
        _load_playwright()

    assert SETUP_COMMAND in str(error.value)


def test_a_missing_browser_binary_names_the_setup_command() -> None:
    """A pinned package without its matching browser build fails the same way."""
    playwright = MagicMock()
    playwright.chromium.launch.side_effect = RuntimeError(
        "Executable doesn't exist at ...ms-playwright\\chromium-1234"
    )

    with pytest.raises(FrontendGateError) as error:
        _launch_chromium(playwright)

    assert SETUP_COMMAND in str(error.value)


def test_the_server_shuts_down_when_a_check_raises() -> None:
    """A failing check must not leave a listening socket behind."""
    server = MagicMock()
    server.server_port = 5123

    with (
        patch("scripts.dev.frontend_gate.make_server", return_value=server),
        patch("scripts.dev.frontend_gate.create_app"),
        pytest.raises(RuntimeError, match="check exploded"),
    ):
        with serve_app():
            raise RuntimeError("check exploded")

    server.shutdown.assert_called_once()


def test_the_server_reports_the_port_the_os_actually_assigned() -> None:
    """Port 0 asks the OS to choose, so the gate must read the real port back."""
    server = MagicMock()
    server.server_port = 5123

    with (
        patch("scripts.dev.frontend_gate.make_server", return_value=server) as factory,
        patch("scripts.dev.frontend_gate.create_app"),
    ):
        with serve_app() as base_url:
            pass

    assert base_url == "http://127.0.0.1:5123"
    assert factory.call_args.args[:2] == ("127.0.0.1", 0)
    server.shutdown.assert_called_once()


def test_headed_reaches_the_browser_launch() -> None:
    """--headed is the option you reach for when a reported failure looks wrong.

    Nothing asserted the flag reached launch, so it silently did nothing.
    """
    playwright = MagicMock()

    _launch_chromium(playwright, headless=False)

    assert playwright.chromium.launch.call_args.kwargs == {"headless": False}


def test_launch_is_headless_by_default() -> None:
    """CI has no display, so the default must stay headless."""
    playwright = MagicMock()

    _launch_chromium(playwright)

    assert playwright.chromium.launch.call_args.kwargs == {"headless": True}


def test_a_raising_check_is_reported_and_the_run_continues() -> None:
    """One broken check must not hide every check after it."""

    def _explodes(_page, _base_url):
        raise TypeError("bad selector")

    def _reports(_page, _base_url):
        return ["a real finding"]

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (("exploding", _explodes), ("later", _reports)),
    ):
        failures = run_checks(page=None, base_url="http://127.0.0.1:0")

    assert failures == [
        "exploding: raised TypeError: bad selector",
        "later: a real finding",
    ]
