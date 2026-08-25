"""Tests for the repository-owned frontend gate runtime.

Every test here is unit level and starts no browser. The browser behaviour is
covered by running the gate itself, which is what the Quality Gate does.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts.dev import frontend_gate
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
        (
            ("exploding", _explodes, (frontend_gate.DESKTOP,)),
            ("later", _reports, (frontend_gate.DESKTOP,)),
        ),
    ):
        failures = run_checks(page=Mock(), base_url="http://127.0.0.1:0")

    assert failures == [
        "exploding [desktop]: raised TypeError: bad selector",
        "later [desktop]: a real finding",
    ]


def test_a_check_runs_once_per_viewport_it_claims() -> None:
    """A mobile-only check must not also run at desktop, and the reverse.

    Every check in this gate ran at 1280x720 and nothing else until WP-3, so
    the viewport a failure came from is new information and the table that
    assigns it is worth holding.
    """
    seen = []

    def _record(_page, _base_url):
        return ["found something"]

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (
            ("both", _record, (frontend_gate.DESKTOP, frontend_gate.MOBILE)),
            ("mobile only", _record, (frontend_gate.MOBILE,)),
        ),
    ):
        page = Mock()
        page.set_viewport_size.side_effect = lambda size: seen.append(size)
        failures = run_checks(page=page, base_url="http://127.0.0.1:0")

    assert seen == [
        frontend_gate.VIEWPORTS[frontend_gate.DESKTOP],
        frontend_gate.VIEWPORTS[frontend_gate.MOBILE],
    ]
    assert failures == [
        "both [desktop]: found something",
        "both [mobile]: found something",
        "mobile only [mobile]: found something",
    ]


def test_a_viewport_that_cannot_be_set_is_reported_not_raised() -> None:
    """The same rule as a broken check: report it, keep going.

    Outside the try, a browser that refuses a resize ends the run in a
    traceback, which reads as "the gate crashed" rather than "one viewport
    could not be reached".
    """

    def _reports(_page, _base_url):
        return ["a real finding"]

    page = Mock()
    page.set_viewport_size.side_effect = [RuntimeError("no resize"), None]

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (("later", _reports, (frontend_gate.DESKTOP, frontend_gate.MOBILE)),),
    ):
        failures = run_checks(page=page, base_url="http://127.0.0.1:0")

    assert failures == [
        "the desktop viewport could not be set: RuntimeError: no resize",
        "later [mobile]: a real finding",
    ]
