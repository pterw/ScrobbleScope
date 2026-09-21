"""Parity and behaviour tests for the runtime slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_runtime, frontend_gate
from scripts.dev._frontend_gate_runtime import (
    SETUP_COMMAND,
    FrontendGateError,
    _launch_browser,
    _load_playwright,
    serve_app,
)
from tests.scripts.dev.gate_parity import defined_names

MOVED = (
    "SETUP_COMMAND",
    "install_cdn_routes",
    "_SERVE_APP_LOCK",
    "FrontendGateError",
    "_load_playwright",
    "_launch_browser",
    "serve_app",
)
REEXPORTED = (
    "SETUP_COMMAND",
    "install_cdn_routes",
    "FrontendGateError",
    "_load_playwright",
    "_launch_browser",
    "serve_app",
)


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_runtime)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_runtime, name)


def test_the_environment_bootstrap_stays_in_the_facade() -> None:
    # Trap 4: the bootstrap must run before any sibling imports scrobblescope.
    assert "GATE_SECRET_KEY" in defined_names(frontend_gate)
    assert "REPO_ROOT" in defined_names(frontend_gate)


def test_a_missing_playwright_package_names_the_setup_command() -> None:
    """The gate never installs tooling implicitly; it tells the operator how."""
    with (
        patch.dict("sys.modules", {"playwright.sync_api": None}),
        pytest.raises(FrontendGateError) as error,
    ):
        _load_playwright()

    assert SETUP_COMMAND in str(error.value)


@pytest.mark.parametrize("browser_name", ("chromium", "firefox"))
def test_a_missing_browser_binary_names_the_setup_command(browser_name) -> None:
    """A pinned package without its matching browser build fails the same way."""
    playwright = MagicMock()
    getattr(playwright, browser_name).launch.side_effect = RuntimeError(
        "Executable doesn't exist at ...ms-playwright\\chromium-1234"
    )

    with pytest.raises(FrontendGateError) as error:
        _launch_browser(playwright, browser_name)

    assert SETUP_COMMAND in str(error.value)
    assert browser_name in str(error.value)


def test_the_server_shuts_down_when_a_check_raises() -> None:
    """A failing check must not leave a listening socket behind."""
    server = MagicMock()
    server.server_port = 5123

    with (
        patch("scripts.dev._frontend_gate_runtime.make_server", return_value=server),
        patch("scripts.dev._frontend_gate_runtime.create_app"),
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
        patch(
            "scripts.dev._frontend_gate_runtime.make_server", return_value=server
        ) as factory,
        patch("scripts.dev._frontend_gate_runtime.create_app"),
    ):
        with serve_app() as base_url:
            pass

    assert base_url == "http://127.0.0.1:5123"
    assert factory.call_args.args[:2] == ("127.0.0.1", 0)
    server.shutdown.assert_called_once()


def test_server_setup_failure_restores_jobs_and_page_inventories() -> None:
    """A bind failure must not leak fixture jobs or temporary routes."""
    migrated_before = list(frontend_gate.MIGRATED_PAGES)
    all_before = list(frontend_gate.ALL_PAGES)
    job_ids_before = dict(frontend_gate.GATE_JOB_IDS)

    with (
        patch("scripts.dev._frontend_gate_runtime.create_app"),
        patch(
            "scripts.dev._frontend_gate_runtime.create_job",
            side_effect=("album-job", "heatmap-job"),
        ),
        patch("scripts.dev._frontend_gate_runtime.set_job_progress"),
        patch(
            "scripts.dev._frontend_gate_runtime.make_server",
            side_effect=OSError("bind failed"),
        ),
        patch("scripts.dev._frontend_gate_runtime.delete_job") as delete_job,
        pytest.raises(OSError, match="bind failed"),
    ):
        with serve_app():
            pass

    assert frontend_gate.MIGRATED_PAGES == migrated_before
    assert frontend_gate.ALL_PAGES == all_before
    assert frontend_gate.GATE_JOB_IDS == job_ids_before
    assert [call.args[0] for call in delete_job.call_args_list] == [
        "album-job",
        "heatmap-job",
    ]


def test_install_cdn_routes_aborts_only_the_overlay_origin() -> None:
    """Only the developer overlay's origin is routed; everything else is untouched."""
    page = MagicMock()
    _frontend_gate_runtime.install_cdn_routes(page)
    assert page.route.call_count == 1
    pattern, handler = page.route.call_args.args
    assert pattern == "http://localhost:8400/**"
    route = MagicMock()
    handler(route)
    route.abort.assert_called_once_with()


def test_install_cdn_routes_respects_live_fonts_flag() -> None:
    """--live-fonts restores real-CDN navigation for local calibration."""
    page = MagicMock()
    _frontend_gate_runtime.install_cdn_routes(page, live_fonts=True)
    page.route.assert_not_called()
