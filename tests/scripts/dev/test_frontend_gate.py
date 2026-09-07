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
    _state_dimension_failures,
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


def _healthy_mobile_header() -> dict:
    """A header measurement that satisfies every mobile-header invariant."""
    return {
        "scrollWidth": 300,
        "clientWidth": 390,
        "linksInside": True,
        "rows": 1,
        "actionsInHeader": False,
        "actionsInMobileSlot": True,
        "actionsTop": 900.0,
        "contentBottom": 800.0,
        "themeHeight": 46.0,
        "headerHeight": 68.0,
        "bodyPaddingTop": 68.0,
    }


def test_mobile_header_failures_accepts_a_compliant_header() -> None:
    """A header meeting every invariant produces no failures."""
    assert frontend_gate._mobile_header_failures(390, _healthy_mobile_header()) == []


def test_mobile_header_failures_reports_scrolling_navigation() -> None:
    """Nav content wider than its box, or links outside it, must be reported."""
    overflowing = _healthy_mobile_header() | {"scrollWidth": 500}
    assert (
        "/: mobile navigation requires horizontal scrolling at 390px"
        in frontend_gate._mobile_header_failures(390, overflowing)
    )
    escaped = _healthy_mobile_header() | {"linksInside": False}
    assert (
        "/: mobile navigation requires horizontal scrolling at 390px"
        in frontend_gate._mobile_header_failures(390, escaped)
    )


def test_mobile_header_failures_reports_multi_row_navigation() -> None:
    """Two distinct link tops mean a wrapped second row."""
    wrapped = _healthy_mobile_header() | {"rows": 2}
    assert (
        "/: mobile navigation uses 2 row(s) at 320px, expected one directly "
        "visible row" in frontend_gate._mobile_header_failures(320, wrapped)
    )


def test_mobile_header_failures_reports_theme_control_in_the_header() -> None:
    """The theme control must live in the mobile slot, not the header bar."""
    in_header = _healthy_mobile_header() | {"actionsInHeader": True}
    assert (
        "/: mobile theme control remains in the header at 390px"
        in frontend_gate._mobile_header_failures(390, in_header)
    )
    no_slot = _healthy_mobile_header() | {"actionsInMobileSlot": False}
    assert (
        "/: mobile theme control remains in the header at 390px"
        in frontend_gate._mobile_header_failures(390, no_slot)
    )


def test_mobile_header_failures_reports_theme_control_above_content() -> None:
    """The control must sit below the page content, within half a pixel."""
    above = _healthy_mobile_header() | {"actionsTop": 799.0, "contentBottom": 800.0}
    assert (
        "/: mobile theme control is not below the page content at 390px"
        in frontend_gate._mobile_header_failures(390, above)
    )
    # Exactly at the boundary is compliant: the tolerance is inclusive.
    touching = _healthy_mobile_header() | {"actionsTop": 799.6, "contentBottom": 800.0}
    assert frontend_gate._mobile_header_failures(390, touching) == []


def test_mobile_header_failures_reports_sub_touch_minimum_theme_control() -> None:
    """A control under 44px fails; exactly 44px passes."""
    small = _healthy_mobile_header() | {"themeHeight": 43.9}
    assert (
        "/: mobile theme control is only 43.9px high at 390px, expected at "
        "least 44px" in frontend_gate._mobile_header_failures(390, small)
    )
    exact = _healthy_mobile_header() | {"themeHeight": 44.0}
    assert frontend_gate._mobile_header_failures(390, exact) == []


def test_mobile_header_failures_reports_mismatched_body_offset() -> None:
    """Body padding-top must equal the fixed header's height exactly.

    The header is fixed (owner ruling 2026-09-07): too small a padding puts
    content under the bar, too large leaves a dead gap above the content.
    """
    small = _healthy_mobile_header() | {
        "headerHeight": 68.0,
        "bodyPaddingTop": 67.2,
    }
    assert (
        "/: mobile body offset does not match its header at 390px"
        in frontend_gate._mobile_header_failures(390, small)
    )
    # Within half a pixel is compliant.
    touching = _healthy_mobile_header() | {
        "headerHeight": 68.0,
        "bodyPaddingTop": 67.7,
    }
    assert frontend_gate._mobile_header_failures(390, touching) == []


def test_state_dimension_failures_reports_only_material_fixed_viewport_changes() -> (
    None
):
    """Expanded controls may add height but cannot rescale the composition."""
    baseline = {"form width": 481.6, "headline font": 45.2}
    states = {
        "decade filter": {"form width": 481.4, "headline font": 45.2},
        "thresholds open": {"form width": 325.2, "headline font": 30.5},
        "missing measurement": {"form width": 481.6},
    }

    assert _state_dimension_failures(baseline, states) == [
        "/: form width changes from 481.6px to 325.2px in thresholds open "
        "at a fixed viewport",
        "/: headline font changes from 45.2px to 30.5px in thresholds open "
        "at a fixed viewport",
        "/: missing measurement did not measure headline font",
    ]


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
        factor = (
            1.075 * current_width["value"] / 1920
            if current_width["value"] <= 1920
            else 1.075 * (0.35 + 0.65 * current_width["value"] / 1920)
        )
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


def test_install_cdn_routes_fulfills_bootstrap_and_passes_the_kit() -> None:
    """The blocker serves the generic CDN; the licensed kit passes through.

    The Adobe families are licensed web fonts (owner ruling 2026-09-07):
    none may be served from a repo fixture, so use.typekit.net must reach
    the real origin. Only cdnjs Bootstrap is route-served.
    """
    page = MagicMock()
    handlers = {}
    page.route.side_effect = lambda pattern, handler: handlers.__setitem__(
        pattern, handler
    )
    frontend_gate.install_cdn_routes(page)

    assert len(handlers) == 2  # CDN blocker + the Impeccable Live abort
    cdn_handler = handlers["**/*"]

    typekit_route, bootstrap_route, other_route = MagicMock(), MagicMock(), MagicMock()
    typekit_route.request.url = "https://use.typekit.net/rwy8ghw.css"
    bootstrap_route.request.url = (
        "https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css"
    )
    other_route.request.url = "http://127.0.0.1:1/static/css/shell.css"

    cdn_handler(typekit_route)
    cdn_handler(bootstrap_route)
    cdn_handler(other_route)

    typekit_route.continue_.assert_called_once()
    typekit_route.fulfill.assert_not_called()
    bootstrap_route.fulfill.assert_called_once()
    bootstrap_route.continue_.assert_not_called()
    other_route.continue_.assert_called_once()
    other_route.fulfill.assert_not_called()


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
    assert page.route.call_count == (0 if live_fonts else 4)
    assert page.set_default_navigation_timeout.call_args.args == (10_000,)


def test_bootstrap_fixture_is_lazy_cached_and_retries_failed_reads(tmp_path) -> None:
    """A missing fixture fails only when requested and can recover without reimport."""
    frontend_gate._bootstrap_fixture.cache_clear()
    try:
        with patch.object(frontend_gate, "FIXTURE_DIR", tmp_path):
            frontend_gate.install_cdn_routes(MagicMock())
            with pytest.raises(FileNotFoundError):
                frontend_gate._bootstrap_fixture()
            fixture = tmp_path / "bootstrap_fixture.css"
            fixture.write_text("body { color: red; }", encoding="utf-8")
            assert frontend_gate._bootstrap_fixture() == "body { color: red; }"
            fixture.write_text("changed", encoding="utf-8")
            assert frontend_gate._bootstrap_fixture() == "body { color: red; }"
    finally:
        frontend_gate._bootstrap_fixture.cache_clear()


def test_scaled_dimensions_preserve_mark_column_ratio_and_fixed_borders() -> None:
    """A twofold content scale does not double fixed chrome or a column-sized mark."""
    baseline = {
        "wordmark": {"height": 100},
        "hero composition": {"height": 300},
        "form": {"height": 105, "width": 200},
        "form composition": {"height": 207},
    }
    expected = frontend_gate._expected_scaled_dimension
    assert expected("wordmark", "height", baseline, 2, 150, 100) == 150
    assert expected("hero composition", "height", baseline, 2, 150, 100) == 550
    assert expected("form", "height", baseline, 2, 150, 100) == 205
    assert expected("form composition", "height", baseline, 2, 150, 100) == 407
    assert expected("form", "width", baseline, 2, 150, 100) == 400

    measurements = {
        label: {"form": {"height": height, "width": 200}}
        for label, height in (
            ("1080p", 105),
            ("1200p measured", 205),
            ("1440p", 210),
            ("4K", 205),
        )
    }
    scales = {"1080p": 1, "1200p measured": 2, "1440p": 2, "4K": 2}
    layouts = {label: {"heroInnerWidth": 100} for label in scales}
    failures = frontend_gate._scale_dimension_failures(
        measurements, layouts, scales, {"form": ("height",)}, {"form": ("width",)}
    )
    assert failures == [
        "/: form height is 210.0px at 1440p, expected proportional 205.0px"
    ]
    measurements["4K"]["form"]["width"] += 1
    assert (
        frontend_gate._scale_dimension_failures(
            measurements, layouts, scales, {"form": ("height",)}, {"form": ("width",)}
        )[-1]
        == "/: form width changes outside the shared composition"
    )


def test_wide_layout_reports_gutter_card_and_mark_regressions() -> None:
    """Balanced columns pass; independently broken geometry remains diagnosable."""
    layout = {
        "formInnerLeft": 20,
        "formLeft": 0,
        "formRight": 140,
        "formInnerRight": 120,
        "paddingLeft": 10,
        "paddingRight": 10,
        "formInnerTop": 20,
        "wellTop": 0,
        "wellBottom": 140,
        "formInnerBottom": 120,
        "cardLeft": 20,
        "cardRight": 120,
        "heroWidth": 120,
        "heroPaddingLeft": 10,
        "heroPaddingRight": 10,
        "heroInnerWidth": 100,
        "heroMarkWidth": 100,
    }
    assert frontend_gate._wide_layout_failures({"window": layout}) == []
    broken = dict(
        layout,
        paddingRight=12,
        formInnerLeft=5,
        formInnerTop=30,
        cardRight=115,
        heroInnerWidth=90,
    )
    failures = frontend_gate._wide_layout_failures({"window": broken})
    assert len(failures) == 7
    assert all("window" in failure for failure in failures)
    assert any("well padding" in failure for failure in failures)
    assert any("wordmark" in failure for failure in failures)


def test_header_geometry_retains_clamps_gaps_and_wrap_thresholds() -> None:
    """Measured floors and ceilings pass; every header contract still reports drift."""
    sizes = {
        "1080p": {
            "header bar": {"height": 68},
            "page navigation": {"height": 44, "width": 92},
            "theme control": {"height": 44.4},
        },
        "1440p": {
            "header bar": {"height": 76},
            "page navigation": {"height": 48, "width": 115.968},
            "theme control": {"height": 48.4},
        },
    }
    layouts = {label: {"headerGap": 8, "navGap": 8, "rowSpread": 1} for label in sizes}
    assert frontend_gate._header_geometry_failures(sizes, layouts) == []
    sizes["1080p"]["header bar"]["height"] += 1
    sizes["1080p"]["page navigation"] = {"height": 40, "width": 80}
    sizes["1080p"]["theme control"]["height"] += 2
    layouts["1080p"] = {"headerGap": 9, "navGap": 8, "rowSpread": 2}
    failures = frontend_gate._header_geometry_failures(sizes, layouts)
    assert len(failures) == 6
    assert all("1080p" in failure for failure in failures)


def test_scale_mechanism_rejects_zoom_and_transform_independently() -> None:
    """Both visible and hidden cards must keep native layout scaling."""
    assert (
        frontend_gate._scale_mechanism_failures(
            [
                {"label": "visible", "zoom": "1", "transform": "none"},
                {"label": "hidden", "zoom": "normal", "transform": "none"},
            ]
        )
        == []
    )
    assert (
        len(
            frontend_gate._scale_mechanism_failures(
                [
                    {
                        "label": "hidden",
                        "zoom": "1.5",
                        "transform": "matrix(1,0,0,1,0,0)",
                    },
                ]
            )
        )
        == 2
    )


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


def test_single_stat_probe_reports_reserved_space_and_offcentre_content() -> None:
    """Hidden stats and centering failures remain independently visible."""
    page = MagicMock()
    page.evaluate.side_effect = [
        None,
        {"scrobblesWidth": 0, "daysWidth": 0, "pagesCenter": 3},
    ]
    assert frontend_gate._check_single_stat_layout(page) == []
    page.evaluate.side_effect = [
        None,
        {"scrobblesWidth": 1, "daysWidth": 0, "pagesCenter": 4},
    ]
    assert len(frontend_gate._check_single_stat_layout(page)) == 2


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


def test_enlarged_root_probe_restores_sizing_when_measurement_raises() -> None:
    """A failing geometry read cannot leave the next check at a larger root font."""
    page = MagicMock()
    page.evaluate.side_effect = [None, "18px", RuntimeError("missing form"), None]
    with pytest.raises(RuntimeError, match="missing form"):
        frontend_gate._measure_enlarged_root(page, "http://local")
    assert page.evaluate.call_args.args == (
        "fontSize => { document.documentElement.style.fontSize = fontSize; }",
        "18px",
    )


def test_composition_bounds_detects_mobile_and_cap_drift() -> None:
    """A plausible wide split must not hide mobile regressions or a stale form cap."""
    sizes = {
        "1080p": {
            "hero composition": {"width": 300},
            "form composition": {"width": 440},
        },
        "1440p": {
            "hero composition": {"width": 450},
            "form composition": {"width": 660},
        },
        "4K": {"form composition": {"width": 770}},
    }
    scales = {"1080p": 1, "1440p": 1.5, "4K": 1.75}
    layouts = {"1080p": {"applicationWidth": 400, "heroWidth": 300}}
    mobile = {"factor": "", "columns": 1}
    inputs = {"input": {"height": 44, "fontSize": 16}}
    assert (
        frontend_gate._composition_bounds_failures(
            sizes, layouts, scales, mobile, inputs
        )
        == []
    )
    sizes["4K"]["form composition"]["width"] = 946
    failures = frontend_gate._composition_bounds_failures(
        sizes,
        layouts,
        scales,
        {"factor": "1.75", "columns": 2},
        {"input": {"height": 43, "fontSize": 15}},
    )
    assert failures == [
        "/: desktop factor leaked into the mobile one-column layout",
        "/: mobile input lost its touch or text minimum",
        "/: form cap is 946px at a real 4K window, expected proportional 770px",
    ]
