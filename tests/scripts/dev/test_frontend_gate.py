"""Tests for the repository-owned frontend gate runtime.

Every test here is unit level and starts no browser. The browser behaviour is
covered by running the gate itself, which is what the Quality Gate does.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from scripts.dev import frontend_gate
from scripts.dev.frontend_gate import (
    SETUP_COMMAND,
    FrontendGateError,
    _assert_loading_progress_state,
    _launch_browser,
    _load_playwright,
    _parse_matrix_scalex,
    check_pipeline_state_machines,
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


def test_parse_matrix_scalex_recovers_scale_and_handles_boundaries() -> None:
    """The matrix parser must extract scaleX, support zero/identity, and handle invalid strings."""
    assert _parse_matrix_scalex("matrix(0.2255, 0, 0, 1, 0, 0)") == pytest.approx(
        0.2255
    )
    assert _parse_matrix_scalex("matrix(0.9, 0, 0, 1, 0, 0)") == pytest.approx(0.9)
    assert _parse_matrix_scalex("matrix(1, 0, 0, 1, 0, 0)") == pytest.approx(1.0)
    assert _parse_matrix_scalex("none") == 0.0
    assert _parse_matrix_scalex(None) == 0.0
    assert _parse_matrix_scalex("") == 0.0
    assert _parse_matrix_scalex("invalid") is None
    assert _parse_matrix_scalex("matrix()") is None


def test_assert_loading_progress_state_reports_mismatches() -> None:
    """The progress state assertion must report any discrepancy in valuenow, valuetext, visible text, or scale."""
    page = MagicMock()
    valid_state = {
        "valuenow": "23",
        "valuetext": "FETCHING SCROBBLES · PAGE 23 / 102",
        "transform": "matrix(0.2255, 0, 0, 1, 0, 0)",
        "phaseText": "FETCHING SCROBBLES · PAGE 23 / 102",
    }
    page.evaluate.return_value = dict(valid_state)

    # Clean match produces no failures
    assert (
        _assert_loading_progress_state(
            page,
            "#track",
            "#bar",
            "#text",
            expected_valuenow=23,
            expected_scalex=0.2255,
            expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
        )
        == []
    )

    # Mismatched valuenow
    page.evaluate.return_value = dict(valid_state, valuenow="99")
    failures = _assert_loading_progress_state(
        page,
        "#track",
        "#bar",
        "#text",
        expected_valuenow=23,
        expected_scalex=0.2255,
        expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
    )
    assert len(failures) == 1
    assert "aria-valuenow was '99'" in failures[0]

    # Mismatched valuetext
    page.evaluate.return_value = dict(valid_state, valuetext="Wrong")
    failures = _assert_loading_progress_state(
        page,
        "#track",
        "#bar",
        "#text",
        expected_valuenow=23,
        expected_scalex=0.2255,
        expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
    )
    assert len(failures) == 1
    assert "aria-valuetext was 'Wrong'" in failures[0]

    # Mismatched visible text
    page.evaluate.return_value = dict(valid_state, phaseText="Stale text")
    failures = _assert_loading_progress_state(
        page,
        "#track",
        "#bar",
        "#text",
        expected_valuenow=23,
        expected_scalex=0.2255,
        expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
    )
    assert len(failures) == 1
    assert "visible text was 'Stale text'" in failures[0]

    # Mismatched scale
    page.evaluate.return_value = dict(
        valid_state, transform="matrix(0.5, 0, 0, 1, 0, 0)"
    )
    failures = _assert_loading_progress_state(
        page,
        "#track",
        "#bar",
        "#text",
        expected_valuenow=23,
        expected_scalex=0.2255,
        expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
    )
    assert len(failures) == 1
    assert "scaleX was 0.5" in failures[0]


def test_install_cdn_routes_aborts_only_the_overlay_origin() -> None:
    """Only the developer overlay's origin is routed; everything else is untouched."""
    page = MagicMock()
    frontend_gate.install_cdn_routes(page)
    assert page.route.call_count == 1
    pattern, handler = page.route.call_args.args
    assert pattern == "http://localhost:8400/**"
    route = MagicMock()
    handler(route)
    route.abort.assert_called_once_with()


def test_install_cdn_routes_respects_live_fonts_flag() -> None:
    """--live-fonts restores real-CDN navigation for local calibration."""
    page = MagicMock()
    frontend_gate.install_cdn_routes(page, live_fonts=True)
    page.route.assert_not_called()


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


def test_phase_repository_probe_checks_real_isolation_and_invalid_views() -> None:
    """The extracted diagnostic exercises real storage and detects missing snapshots."""
    job = frontend_gate.create_job({"username": "probe"})
    try:
        assert frontend_gate._check_phase_repository_isolation(job) == []
        assert frontend_gate.get_job_progress(job)["phase"]["current"] == 23
        with (
            patch.object(frontend_gate, "get_job_progress", return_value=None),
            patch.object(frontend_gate, "get_job_context", return_value=None),
        ):
            failures = frontend_gate._check_phase_repository_isolation(job)
        assert len(failures) == 6
    finally:
        frontend_gate.delete_job(job)


def test_replaced_job_probe_reports_stale_delivery_and_cleans_up() -> None:
    """Late old-job data is checked and temporary job/routes are removed on faults."""
    page = MagicMock()
    held = MagicMock()
    held.request.url = "http://local/progress?job_id=old-job"
    page.route.side_effect = lambda pattern, handler: handler(held)
    page.locator.return_value.get_attribute.return_value = "20"
    page.locator.return_value.inner_text.return_value = "PAGE 20 / 100"
    with (
        patch.object(frontend_gate, "create_job", return_value="replacement"),
        patch.object(frontend_gate, "set_job_progress"),
        patch.object(frontend_gate, "delete_job") as delete,
    ):
        failures = frontend_gate._exercise_replaced_job_progress(
            page, "http://local", "old-job", "/heatmap?job_id=old-job"
        )
        assert failures == [
            "stale out-of-order progress response regressed aria-valuenow",
            "stale out-of-order progress response regressed visible text",
        ]
        assert held.fulfill.call_args.kwargs["status"] == 200
        response = held.fulfill.call_args.kwargs
        payload = response.get("json") or json.loads(response["body"])
        assert payload == {
            "progress": 20,
            "phase": {
                "key": "lastfm_fetch",
                "label": "Fetching scrobbles",
                "unit": "page",
                "current": 20,
                "total": 100,
            },
        }
        delete.assert_called_once_with("replacement")
        page.unroute.assert_called_once_with("**/progress?job_id=*")
        page.goto.side_effect = RuntimeError("navigation broke")
        with pytest.raises(RuntimeError, match="navigation broke"):
            frontend_gate._exercise_replaced_job_progress(
                page, "http://local", "old-job", "/heatmap?job_id=old-job"
            )
        assert delete.call_count == 2
        assert page.unroute.call_count == 2


@pytest.mark.parametrize("client", ("album", "heatmap"))
def test_counted_sequence_updates_real_storage_and_detects_stale_text(client) -> None:
    """Both clients receive the same phase transitions and report an uncleared fraction."""
    job = frontend_gate.create_job({"username": "probe"})
    page = MagicMock()
    snapshots = []
    expected = [
        (
            "23",
            "FETCHING SCROBBLES \u00b7 PAGE 23 / 102",
            "matrix(0.2255, 0, 0, 1, 0, 0)",
        ),
        ("90", "FETCHING SCROBBLES \u00b7 PAGE 90 / 100", "matrix(0.9, 0, 0, 1, 0, 0)"),
        ("92", "Counting daily scrobbles", "matrix(0.92, 0, 0, 1, 0, 0)"),
    ]

    def read_state(script, selectors):
        """Capture the producer state before returning the simulated browser frame."""
        snapshots.append(frontend_gate.get_job_progress(job))
        value, text, transform = expected[len(snapshots) - 1]
        return {
            "valuenow": value,
            "valuetext": text,
            "phaseText": text,
            "transform": transform,
        }

    page.evaluate.side_effect = read_state
    page.locator.return_value.inner_text.return_value = "PAGE 90 / 100"
    try:
        failures = frontend_gate._exercise_counted_progress(
            page, "http://local", job, "/loading", ("#track", "#bar", "#text"), client
        )
        assert failures == [f"{client} uncounted frame retained stale phase fraction"]
        assert [snapshot["progress"] for snapshot in snapshots] == [20, 90, 92]
        assert [snapshot.get("phase") for snapshot in snapshots] == [
            {
                "key": "lastfm_fetch",
                "label": "Fetching scrobbles",
                "unit": "page",
                "current": 23,
                "total": 102,
            },
            {
                "key": "lastfm_fetch",
                "label": "Fetching scrobbles",
                "unit": "page",
                "current": 90,
                "total": 100,
            },
            None,
        ]
    finally:
        frontend_gate.delete_job(job)
