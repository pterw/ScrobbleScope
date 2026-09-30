"""Tests for the repository-owned frontend gate runtime.

Every test here is unit level and starts no browser. The browser behaviour is
covered by running the gate itself, which is what the Quality Gate does.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts.dev import frontend_gate
from scripts.dev.frontend_gate import (
    FrontendGateError,
    _launch_browser,
    run_checks,
)


@pytest.mark.parametrize("browser_name", ("chromium", "firefox"))
def test_headed_reaches_the_browser_launch(browser_name) -> None:
    """--headed is the option you reach for when a reported failure looks wrong.

    Nothing asserted the flag reached launch, so it silently did nothing.
    """
    playwright = MagicMock()

    _launch_browser(playwright, browser_name, headless=False)

    assert getattr(playwright, browser_name).launch.call_args.kwargs == {
        "headless": False
    }


@pytest.mark.parametrize("browser_name", ("chromium", "firefox"))
def test_launch_is_headless_by_default(browser_name) -> None:
    """CI has no display, so the default must stay headless."""
    playwright = MagicMock()

    _launch_browser(playwright, browser_name)

    assert getattr(playwright, browser_name).launch.call_args.kwargs == {
        "headless": True
    }
    other = "firefox" if browser_name == "chromium" else "chromium"
    getattr(playwright, other).launch.assert_not_called()


def test_a_raising_check_is_reported_and_the_run_continues() -> None:
    """One broken check must not hide every check after it."""

    def _explodes(_page, _base_url):
        raise TypeError("bad selector")

    def _reports(_page, _base_url):
        return ["a real finding"]

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (
            ("exploding", _explodes, (frontend_gate.DESKTOP,), "g1"),
            ("later", _reports, (frontend_gate.DESKTOP,), "g1"),
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
            (
                "both",
                _record,
                (frontend_gate.DESKTOP, frontend_gate.MOBILE),
                "g1",
            ),
            ("touch only", _record, (frontend_gate.TOUCH_WIDE,), "g1"),
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
        (
            (
                "later",
                _reports,
                (frontend_gate.DESKTOP, frontend_gate.MOBILE),
                "g1",
            ),
        ),
    ):
        failures = run_checks(new_page=_new_page, base_url="http://127.0.0.1:0")

    assert failures == [
        "g1 [desktop]: context could not be opened: RuntimeError: no context",
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


@pytest.mark.parametrize("raised", (False, True))
def test_main_runs_and_closes_both_engines_with_named_failures(raised, capsys):
    """A failed engine must not hide the other engine or leave browsers open."""
    from contextlib import nullcontext

    chromium, firefox = MagicMock(), MagicMock()
    outcomes = [RuntimeError("broken check") if raised else ["bad geometry"], []]
    with (
        patch.object(
            frontend_gate, "_load_playwright", return_value=lambda: nullcontext(Mock())
        ),
        patch.object(
            frontend_gate, "serve_app", return_value=nullcontext("http://local")
        ),
        patch.object(
            frontend_gate, "_launch_browser", side_effect=[chromium, firefox]
        ) as launch,
        patch.object(frontend_gate, "run_checks", side_effect=outcomes),
    ):
        assert frontend_gate.main([]) == 1
    assert [call.args[1] for call in launch.call_args_list] == ["chromium", "firefox"]
    assert chromium.close.call_count == firefox.close.call_count == 1
    assert "chromium" in capsys.readouterr().err


@pytest.mark.parametrize("fault", ("launch", "close", None))
def test_main_isolates_lifecycle_faults_and_reports_complete_success(fault, capsys):
    """The next engine still runs after a failed launch or cleanup; success names both."""
    from contextlib import nullcontext

    chromium, firefox = MagicMock(), MagicMock()
    if fault == "close":
        chromium.close.side_effect = RuntimeError("close failed")
    launches = [
        FrontendGateError("chromium missing") if fault == "launch" else chromium,
        firefox,
    ]
    with (
        patch.object(
            frontend_gate, "_load_playwright", return_value=lambda: nullcontext(Mock())
        ),
        patch.object(
            frontend_gate, "serve_app", return_value=nullcontext("http://local")
        ),
        patch.object(frontend_gate, "_launch_browser", side_effect=launches) as launch,
        patch.object(frontend_gate, "run_checks", return_value=[]) as checks,
    ):
        assert frontend_gate.main(["--headed"]) == (1 if fault else 0)
    assert [call.args[1] for call in launch.call_args_list] == ["chromium", "firefox"]
    assert all(call.kwargs == {"headless": False} for call in launch.call_args_list)
    assert checks.call_count == (1 if fault == "launch" else 2)
    firefox.close.assert_called_once()
    output = capsys.readouterr()
    if fault:
        assert "chromium" in output.err
        assert "checks passed" not in output.out
    else:
        assert "chromium, firefox" in output.out
        assert f"in {frontend_gate.PLANNED_RUNS} runs" in output.out
        assert frontend_gate.PLANNED_RUNS == sum(
            sum(
                1
                for entry in frontend_gate.CHECKS
                if profile in entry[2] and entry[3] in frontend_gate.groups_for(browser)
            )
            for browser in frontend_gate.BROWSER_NAMES
            for profile in frontend_gate.VIEWPORTS
        )


def test_a_stalled_group_gets_a_fresh_page_for_the_next_group() -> None:
    """A wedged page must not leak into the next group's checks.

    The 2026-09-07 CI run cascaded one navigation timeout through every
    later check on the same shared page object; one fresh page per group
    is what bounds that damage to the group that caused it.
    """
    pages = []

    def _new_page(spec):
        page = Mock()
        pages.append(page)
        return page

    with patch(
        "scripts.dev.frontend_gate.CHECKS",
        (
            ("first", lambda p, b: [], (frontend_gate.DESKTOP,), "g1"),
            ("second", lambda p, b: [], (frontend_gate.DESKTOP,), "g2"),
        ),
    ):
        run_checks(new_page=_new_page, base_url="http://127.0.0.1:0")

    assert len(pages) == 2
    assert pages[0] is not pages[1]


def test_firefox_scope_runs_only_the_canary_group() -> None:
    """Firefox is a canary: it runs the fastest, fixture-served group only.

    The 2026-09-01 remediation plan measured both engines agreeing within
    0.1px at four window profiles, so a full second pass doubles the stall
    surface for near-zero signal. Chromium runs every group.
    """
    scope = frontend_gate.groups_for("firefox")
    assert scope == ("static assets & tokens",)
    assert len(frontend_gate.groups_for("chromium")) == len(frontend_gate.CHECK_GROUPS)


def test_fail_fast_navigation_timeout_is_configured() -> None:
    """Contexts get the 10s navigation timeout, not Playwright's 30s default.

    The 30s default turned one stalled subresource into a 30s wait per
    check; the timeout is what bounds the damage to one failed check.
    """
    assert frontend_gate.NAVIGATION_TIMEOUT_MS == 10_000


@pytest.mark.parametrize("live_fonts", (False, True))
def test_main_preserves_route_policy_through_real_runner(live_fonts) -> None:
    """The runner must preserve the factory's live-CDN policy on every engine."""
    from contextlib import nullcontext

    browser = MagicMock()
    page = browser.new_context.return_value.new_page.return_value
    with (
        patch.object(
            frontend_gate, "_load_playwright", return_value=lambda: nullcontext(Mock())
        ),
        patch.object(
            frontend_gate, "serve_app", return_value=nullcontext("http://local")
        ),
        patch.object(frontend_gate, "_launch_browser", return_value=browser),
        patch.object(
            frontend_gate,
            "CHECKS",
            (
                (
                    "probe",
                    lambda p, b: [],
                    (frontend_gate.DESKTOP,),
                    frontend_gate.STATIC_ASSETS,
                ),
            ),
        ),
    ):
        assert frontend_gate.main(["--live-fonts"] if live_fonts else []) == 0
    # One localhost:8400 abort route per browser engine (chromium, firefox).
    assert page.route.call_count == (0 if live_fonts else 2)
    if not live_fonts:
        assert page.route.call_args.args[0] == "http://localhost:8400/**"
    assert page.set_default_navigation_timeout.call_args.args == (10_000,)


# --- Subresource load faults (advisory diagnostic) ---


class _EventPage:
    """A page stand-in that keeps the handlers registered with ``on``."""

    def __init__(self) -> None:
        self.handlers: dict[str, list] = {}

    def on(self, event, handler) -> None:
        self.handlers.setdefault(event, []).append(handler)

    def emit(self, event, payload) -> None:
        for handler in self.handlers.get(event, []):
            handler(payload)


def _request(url, resource_type="stylesheet", failure=None):
    return SimpleNamespace(url=url, resource_type=resource_type, failure=failure)


BASE = "http://127.0.0.1:5001"


def test_recorder_names_a_failed_app_stylesheet_and_a_5xx_script() -> None:
    page = _EventPage()
    faults = frontend_gate.record_load_faults(page, BASE)

    page.emit(
        "requestfailed",
        _request(f"{BASE}/static/css/tailwind.css", failure="net::ERR_NO_BUFFER_SPACE"),
    )
    script = _request(f"{BASE}/static/js/index.js", "script")
    page.emit("response", SimpleNamespace(status=503, request=script))

    assert faults == [
        f"{BASE}/static/css/tailwind.css (net::ERR_NO_BUFFER_SPACE)",
        f"{BASE}/static/js/index.js (HTTP 503)",
    ]


def test_recorder_ignores_foreign_origins_other_types_and_good_responses() -> None:
    page = _EventPage()
    faults = frontend_gate.record_load_faults(page, BASE)

    page.emit("requestfailed", _request("https://cdn.example.com/x.css"))
    page.emit("requestfailed", _request(f"{BASE}/validate_user", "fetch"))
    page.emit(
        "response", SimpleNamespace(status=200, request=_request(f"{BASE}/a.css"))
    )
    page.emit(
        "response",
        SimpleNamespace(status=404, request=_request(f"{BASE}/img.png", "image")),
    )

    assert faults == []


def test_a_failing_check_carries_the_load_fault_but_a_passing_one_stays_clean() -> None:
    page = _EventPage()
    frontend_gate.record_load_faults(page, BASE)

    def failing(page, base_url):
        page.emit(
            "requestfailed",
            _request(f"{BASE}/static/css/loading.css", failure="net::ERR_FAILED"),
        )
        return ["progress fill is rgba(0, 0, 0, 0)"]

    def passing(page, base_url):
        page.emit(
            "requestfailed",
            _request(f"{BASE}/static/css/x.css", failure="net::ERR_FAILED"),
        )
        return []

    def raising(page, base_url):
        page.emit(
            "requestfailed",
            _request(f"{BASE}/static/js/x.js", "script", "net::ERR_FAILED"),
        )
        raise RuntimeError("boom")

    red = frontend_gate._run_check(page, BASE, "fill", "desktop", failing)
    green = frontend_gate._run_check(page, BASE, "ok", "desktop", passing)
    crashed = frontend_gate._run_check(page, BASE, "bad", "desktop", raising)

    assert len(red) == 1
    assert red[0].startswith("fill [desktop]: progress fill is rgba(0, 0, 0, 0)")
    assert "1 app resource(s) failed to load" in red[0]
    assert f"{BASE}/static/css/loading.css (net::ERR_FAILED)" in red[0]
    assert green == []
    assert "raised RuntimeError: boom" in crashed[0]
    assert f"{BASE}/static/js/x.js" in crashed[0]
    assert "loading.css" not in crashed[0]


def test_a_check_on_a_page_without_a_recorder_reports_no_note() -> None:
    result = frontend_gate._run_check(
        Mock(), BASE, "n", "desktop", lambda page, base_url: ["broken"]
    )

    assert result == ["n [desktop]: broken"]
