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
    _assert_loading_progress_state,
    _check_desktop_scale_bounds,
    _clamp_px,
    _composite_over,
    _contrast_ratio,
    _divider_contrast_failure,
    _headline_wrap_failures,
    _launch_browser,
    _load_playwright,
    _parse_matrix_scalex,
    _parse_rgb_string,
    _relative_luminance,
    _touch_minimum_failures,
    _worst_divider_contrast,
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
                return {
                    "height": 95.0,
                    "expected": 95.0,
                    "navTarget": 60.0,
                    "expectedTarget": 60.0,
                    "navGap": 15.0,
                    "expectedGap": 15.0,
                }
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


def test_parse_rgb_string_reads_rgb_and_rgba_forms() -> None:
    """The parser must recover alpha when present and default it to opaque."""
    assert _parse_rgb_string("rgb(26, 24, 32)") == (26.0, 24.0, 32.0, 1.0)
    assert _parse_rgb_string("rgba(26, 24, 32, 0.5)") == (26.0, 24.0, 32.0, 0.5)


def test_composite_over_blends_by_alpha() -> None:
    """A translucent foreground must blend proportionally with its backdrop."""
    # Half-alpha white over black must land exactly halfway, per channel.
    assert _composite_over((255.0, 255.0, 255.0, 0.5), (0.0, 0.0, 0.0)) == (
        127.5,
        127.5,
        127.5,
    )
    # An opaque foreground must pass through unchanged regardless of backdrop.
    assert _composite_over((10.0, 20.0, 30.0, 1.0), (200.0, 200.0, 200.0)) == (
        10.0,
        20.0,
        30.0,
    )


def test_relative_luminance_orders_black_grey_white() -> None:
    """Luminance must be 0 for black, 1 for white, and monotonic between."""
    black = _relative_luminance((0.0, 0.0, 0.0))
    grey = _relative_luminance((128.0, 128.0, 128.0))
    white = _relative_luminance((255.0, 255.0, 255.0))
    assert black == 0.0
    assert white == 1.0
    assert black < grey < white


def test_contrast_ratio_is_symmetric_and_maximal_for_black_on_white() -> None:
    """Contrast ratio must not depend on argument order and must cap at 21:1."""
    black = (0.0, 0.0, 0.0)
    white = (255.0, 255.0, 255.0)
    assert _contrast_ratio(black, white) == pytest.approx(21.0, abs=0.01)
    assert _contrast_ratio(black, white) == _contrast_ratio(white, black)
    # Identical colours never separate, so the ratio floors at 1:1.
    assert _contrast_ratio(black, black) == 1.0


def test_worst_divider_contrast_is_the_minimum_across_surfaces() -> None:
    """A divider painted over several surfaces is only as good as the worst one."""
    border = "rgba(26, 24, 32, 0.5)"
    high_contrast_surface = "rgb(255, 255, 255)"
    low_contrast_surface = "rgb(40, 38, 46)"
    worst = _worst_divider_contrast(border, high_contrast_surface, low_contrast_surface)
    against_low_only = _worst_divider_contrast(border, low_contrast_surface)
    assert worst == pytest.approx(against_low_only)
    assert worst < _worst_divider_contrast(border, high_contrast_surface)


def test_divider_contrast_failure_boundary_is_exactly_3_to_1() -> None:
    """The 3:1 boundary must pass at 3.0 and fail just below it.

    Repo rule: this must fail if `_divider_contrast_failure` is deleted or its
    comparison is loosened (e.g. `> 3.0` instead of `>= 3.0`), so both sides of
    the boundary are asserted rather than only the failing side.
    """
    assert _divider_contrast_failure("light", 3.0) is None
    assert _divider_contrast_failure("light", 4.5) is None
    assert _divider_contrast_failure("light", 2.9999) is not None
    failure = _divider_contrast_failure("light", 1.27)
    assert failure == (
        "/ light: --shell-border composites to 1.27:1 against its "
        "adjacent surface, expected at least 3:1"
    )


def test_divider_contrast_failure_names_the_token_it_checks() -> None:
    """A caller must be able to attribute a failure to a specific token.

    F-B21-40: the same helper now checks both the shared --shell-border and
    the index page's own --ss-border-divider. This must fail if the `token`
    parameter is removed or its default silently changes, since a message
    that always says "--shell-border" would misattribute a failing index
    divider to the wrong token.
    """
    failure = _divider_contrast_failure(
        "index divider light", 1.12, token="--ss-border-divider"
    )
    assert failure == (
        "/ index divider light: --ss-border-divider composites to 1.12:1 "
        "against its adjacent surface, expected at least 3:1"
    )
    # The default stays --shell-border for every existing caller.
    assert _divider_contrast_failure("light", 1.27) == (
        "/ light: --shell-border composites to 1.27:1 against its "
        "adjacent surface, expected at least 3:1"
    )


def test_clamp_px_resolves_floor_preferred_and_ceiling() -> None:
    """`_clamp_px` must mirror CSS clamp(): floor, vw-scaled middle, ceiling."""
    # Below the point where 2.96875vw reaches the 4.25rem floor.
    assert _clamp_px(4.25, 2.96875, 4.75, 1000) == pytest.approx(4.25 * 16)
    # At 1920px, 2.96875vw is still under the 4.75rem ceiling and over the
    # 4.25rem floor at root 16px, so the floor still wins (matches the header
    # bar's ruled 68px at a real 1080p window).
    assert _clamp_px(4.25, 2.96875, 4.75, 1920) == pytest.approx(4.25 * 16)
    # Above the point where the preferred value exceeds the ceiling.
    assert _clamp_px(4.25, 2.96875, 4.75, 2560) == pytest.approx(4.75 * 16)
    # A non-default root font size scales both bounds, not the vw term.
    assert _clamp_px(4.25, 2.96875, 4.75, 1920, root_px=20) == pytest.approx(4.25 * 20)


def test_desktop_scale_bounds_reports_wrapped_headlines_and_closes_context() -> None:
    """The boundary probe must report real wrapping and release its context."""
    assert _touch_minimum_failures(
        1920,
        {
            ".too-short": {"width": 44, "height": 43.8},
            ".minimum": {"width": 44, "height": 43.9},
        },
    ) == ["/: .too-short loses its touch minimum at 1920px"]

    current_width = {"value": 1200}
    context = MagicMock()
    probe = context.new_page.return_value
    page = MagicMock()
    page.context.browser.new_context.return_value = context

    def set_viewport_size(viewport: dict[str, int]) -> None:
        """Track the active width so the fake can return proportional heights."""
        current_width["value"] = viewport["width"]

    def locate(selector: str) -> MagicMock:
        """Wrap the headline only at 1200px; every other desktop width is clean.

        This proves the widened one-line assertion (1200/1500/1920/2560) reports
        a real per-width failure instead of a single hard-coded boundary check.
        """
        locator = MagicMock()
        if selector.endswith(" h1"):
            wraps = current_width["value"] == 1200
            locator.evaluate.return_value = (
                {"height": 50, "lineHeight": 20}
                if wraps
                else {"height": 20, "lineHeight": 20}
            )
        return locator

    def evaluate(script: str):
        """Return valid touch geometry while preserving the headline failure."""
        if script == frontend_gate.FONTS_READY_EXPRESSION:
            return None
        factor = 1.075 * current_width["value"] / 1920
        if "rect.width" in script:
            return {
                selector: {"width": 44, "height": 44}
                for selector in (
                    ".mode-pill",
                    ".seg__option",
                    ".decade-pill",
                    ".disclosure__summary",
                    ".stepper__value",
                    ".ss-input",
                )
            }
        return {
            selector: max(44, authored * factor)
            for selector, authored in {
                ".mode-pill": 44,
                ".seg__option": 38,
                ".decade-pill": 30,
                ".disclosure__summary": 32,
            }.items()
        }

    probe.set_viewport_size.side_effect = set_viewport_size
    probe.locator.side_effect = locate
    probe.evaluate.side_effect = evaluate

    assert _headline_wrap_failures(probe, 1200) == [
        "/: album headline wraps at 1200px",
        "/: heatmap headline wraps at 1200px",
    ]
    # The full sweep covers the breakpoint (1200), an intermediate windowed
    # width (1500), and both real profiles above it (1920, 2560); only the
    # 1200px case wraps here, so the aggregate below proves the loop reports
    # per-width, not just the first width it tries.
    assert _check_desktop_scale_bounds(page, "http://local") == [
        "/: album headline wraps at 1200px",
        "/: heatmap headline wraps at 1200px",
    ]
    page.context.browser.new_context.assert_called_once_with(has_touch=True)
    context.close.assert_called_once()


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
        assert frontend_gate.PLANNED_RUNS == 2 * sum(
            len(profiles) for _, _, profiles in frontend_gate.CHECKS
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
