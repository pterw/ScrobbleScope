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
    check_pipeline_state_machines,
    check_shell_scales_with_text,
    check_theme_persistence,
    check_theme_survives_blocked_storage,
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


def test_server_setup_failure_restores_jobs_and_page_inventories() -> None:
    """A bind failure must not leak fixture jobs or temporary routes."""
    migrated_before = list(frontend_gate.MIGRATED_PAGES)
    all_before = list(frontend_gate.ALL_PAGES)
    job_ids_before = dict(frontend_gate.GATE_JOB_IDS)

    with (
        patch("scripts.dev.frontend_gate.create_app"),
        patch(
            "scripts.dev.frontend_gate.create_job",
            side_effect=("album-job", "heatmap-job"),
        ),
        patch("scripts.dev.frontend_gate.set_job_progress"),
        patch(
            "scripts.dev.frontend_gate.make_server",
            side_effect=OSError("bind failed"),
        ),
        patch("scripts.dev.frontend_gate.delete_job") as delete_job,
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


def test_blocked_storage_probe_closes_context_when_page_creation_fails() -> None:
    """A failed probe page must not leave its isolated context open."""
    context = MagicMock()
    context.new_page.side_effect = RuntimeError("page unavailable")
    browser = MagicMock()
    browser.new_context.return_value = context
    page = MagicMock()
    page.context.browser = browser

    with pytest.raises(RuntimeError, match="page unavailable"):
        check_theme_survives_blocked_storage(page, "http://127.0.0.1:0")

    context.close.assert_called_once()


def test_pipeline_state_machine_uses_a_disposable_page() -> None:
    """Its page-level timer patch must not reach later checks."""
    page = MagicMock()
    probe = page.context.new_page.return_value

    with (
        patch.dict(
            "scripts.dev.frontend_gate.GATE_JOB_IDS",
            {"album": "album-job", "heatmap": "heatmap-job"},
            clear=True,
        ),
        patch("scripts.dev.frontend_gate.reset_job_state"),
        patch("scripts.dev.frontend_gate.set_job_progress"),
        patch(
            "scripts.dev.frontend_gate._exercise_pipeline_state_machines",
            side_effect=RuntimeError("pipeline failed"),
        ) as exercise,
    ):
        with pytest.raises(RuntimeError, match="pipeline failed"):
            check_pipeline_state_machines(page, "http://127.0.0.1:0")

    exercise.assert_called_once_with(probe, "http://127.0.0.1:0")
    probe.close.assert_called_once()


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


def test_text_scaling_check_restores_the_page_root() -> None:
    """A diagnostic does not leak its enlarged root into later checks."""

    class ScalingPage:
        """Small page seam that exposes only the root style the check changes."""

        root_font_size = "17px"

        def goto(self, _url, *, wait_until):
            assert wait_until == "load"

        def evaluate(self, script, arg=None):
            if "style.fontSize = '20px'" in script:
                self.root_font_size = "20px"
                return {"height": 85.0, "expected": 85.0}
            if "style.fontSize = fontSize" in script:
                self.root_font_size = arg
                return None
            if "document.documentElement.style.fontSize" in script:
                return self.root_font_size
            raise AssertionError(f"unexpected browser expression: {script}")

    page = ScalingPage()

    assert check_shell_scales_with_text(page, "http://127.0.0.1:0") == []
    assert page.root_font_size == "17px"


def test_theme_persistence_check_restores_the_saved_preference() -> None:
    """The persistence diagnostic must not choose a theme for later checks."""
    state = {"saved": "true", "theme": "dark"}
    page = MagicMock()

    def load_saved_theme(*_args, **_kwargs):
        state["theme"] = "dark" if state["saved"] == "true" else "light"

    def evaluate(script, arg=None):
        if "localStorage.getItem('darkMode')" in script:
            return state["saved"]
        if "document.documentElement.dataset.theme" in script:
            return state["theme"]
        if "localStorage.removeItem('darkMode')" in script:
            state["saved"] = arg
            return None
        raise AssertionError(f"unexpected browser expression: {script}")

    def toggle_theme(*_args, **_kwargs):
        state["saved"] = "false" if state["saved"] == "true" else "true"
        load_saved_theme()

    page.goto.side_effect = load_saved_theme
    page.reload.side_effect = load_saved_theme
    page.evaluate.side_effect = evaluate
    page.locator.return_value.count.return_value = 1
    page.locator.return_value.first.click.side_effect = toggle_theme

    with patch("scripts.dev.frontend_gate.MIGRATED_PAGES", ("/",)):
        assert check_theme_persistence(page, "http://127.0.0.1:0") == []

    assert state == {"saved": "true", "theme": "dark"}


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
        failures = run_checks(
            new_page=lambda spec: Mock(), base_url="http://127.0.0.1:0"
        )

    assert failures == [
        "exploding [desktop]: raised TypeError: bad selector",
        "later [desktop]: a real finding",
    ]


def test_a_check_runs_once_per_profile_it_claims() -> None:
    """A profile-scoped check must run on its profiles and no others.

    Every check in this gate ran at 1280x720 with a mouse and nothing else
    until WP-3, so the profile a failure came from is new information and the
    table that assigns it is worth holding.
    """
    seen = []

    def _record(_page, _base_url):
        return ["found something"]

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (
            ("both", _record, (frontend_gate.DESKTOP, frontend_gate.MOBILE)),
            ("touch only", _record, (frontend_gate.TOUCH_WIDE,)),
        ),
    ):
        failures = run_checks(
            new_page=lambda spec: seen.append(spec) or Mock(),
            base_url="http://127.0.0.1:0",
        )

    # Every profile is opened, in order, even one no check claims.
    assert seen == list(frontend_gate.VIEWPORTS.values())
    assert failures == [
        "both [desktop]: found something",
        "both [mobile]: found something",
        "touch only [wide touch]: found something",
    ]


def test_a_profile_that_cannot_be_opened_is_reported_not_raised() -> None:
    """The same rule as a broken check: report it, keep going.

    Outside the try, a browser that refuses a context ends the run in a
    traceback, which reads as "the gate crashed" rather than "one profile
    could not be opened".
    """

    def _reports(_page, _base_url):
        return ["a real finding"]

    calls = []

    def _new_page(spec):
        calls.append(spec)
        if len(calls) == 1:
            raise RuntimeError("no context")
        return Mock()

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (("later", _reports, (frontend_gate.DESKTOP, frontend_gate.MOBILE)),),
    ):
        failures = run_checks(new_page=_new_page, base_url="http://127.0.0.1:0")

    assert failures == [
        "the desktop profile could not be opened: RuntimeError: no context",
        "later [mobile]: a real finding",
    ]


def test_the_touch_profiles_really_carry_a_coarse_pointer() -> None:
    """The wide-touch profile is the whole point, so its flag is asserted.

    A touch-target rule keyed on (any-pointer: coarse) is only tested if the
    profile actually reports one. Chromium derives that media feature from
    has_touch; drop the flag and the check would pass on a mouse and prove
    nothing. is_mobile stays off deliberately -- it changes device scale and
    scrollbars, which would move every measurement taken so far.
    """
    for profile in (frontend_gate.MOBILE, frontend_gate.TOUCH_WIDE):
        spec = frontend_gate.VIEWPORTS[profile]
        assert spec.get("has_touch") is True, f"{profile} is not a touch device"
        assert "is_mobile" not in spec, f"{profile} must not emulate a phone"

    desktop = frontend_gate.VIEWPORTS[frontend_gate.DESKTOP]
    assert not desktop.get("has_touch"), "the mouse profile must stay a mouse"
    # Wide, so a width-scoped rule cannot be what satisfies the check.
    assert frontend_gate.VIEWPORTS[frontend_gate.TOUCH_WIDE]["viewport"]["width"] >= 860
