"""Parity and behaviour tests for the layout slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_layout, frontend_gate
from scripts.dev._frontend_gate_layout import (
    _check_desktop_scale_bounds,
    _headline_wrap_failures,
    _state_dimension_failures,
    _touch_minimum_failures,
    check_shell_scales_with_text,
)
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_touch_targets",
    "check_fonts",
    "check_body_font",
    "check_shell_scales_with_text",
    "check_large_display_scale_parity",
    "check_destination_empty_states",
)
CONSTANTS = (
    "FONTS_READY_EXPRESSION",
    "REQUIRED_FONT_FAMILIES",
    "MIN_TOUCH_TARGET_PX",
    "INTERACTIVE_SELECTOR",
    "TOUCH_TARGET_STATES",
    "DEFAULT_STATES",
)
HELPERS = (
    "_small_targets",
    "_measure_scale_dimensions",
    "_measure_wide_layout",
    "_measure_zoom_and_transform",
    "_measure_fixed_state",
    "_measure_mobile_headers",
    "_measure_enlarged_root",
    "_composition_bounds_failures",
    "_expected_scaled_dimension",
    "_scale_dimension_failures",
    "_wide_layout_failures",
    "_header_geometry_failures",
    "_scale_mechanism_failures",
    "_touch_minimum_failures",
    "_mobile_header_failures",
    "_state_dimension_failures",
    "_headline_wrap_failures",
    "_check_desktop_scale_bounds",
)
REEXPORTED = (*CHECKS, *CONSTANTS)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS, *HELPERS))
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_layout)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_layout, name)


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
        "bodyPaddingTop": 0.0,
        "headerPosition": "relative",
    }


def test_mobile_header_failures_accepts_a_compliant_header() -> None:
    """A header meeting every invariant produces no failures."""
    assert (
        _frontend_gate_layout._mobile_header_failures(390, _healthy_mobile_header())
        == []
    )


def test_mobile_header_failures_reports_scrolling_navigation() -> None:
    """Nav content wider than its box, or links outside it, must be reported."""
    overflowing = _healthy_mobile_header() | {"scrollWidth": 500}
    assert (
        "/: mobile navigation requires horizontal scrolling at 390px"
        in _frontend_gate_layout._mobile_header_failures(390, overflowing)
    )
    escaped = _healthy_mobile_header() | {"linksInside": False}
    assert (
        "/: mobile navigation requires horizontal scrolling at 390px"
        in _frontend_gate_layout._mobile_header_failures(390, escaped)
    )


def test_mobile_header_failures_reports_multi_row_navigation() -> None:
    """Two distinct link tops mean a wrapped second row."""
    wrapped = _healthy_mobile_header() | {"rows": 2}
    assert (
        "/: mobile navigation uses 2 row(s) at 320px, expected one directly "
        "visible row" in _frontend_gate_layout._mobile_header_failures(320, wrapped)
    )


def test_mobile_header_failures_reports_theme_control_in_the_header() -> None:
    """The theme control must live in the mobile slot, not the header bar."""
    in_header = _healthy_mobile_header() | {"actionsInHeader": True}
    assert (
        "/: mobile theme control remains in the header at 390px"
        in _frontend_gate_layout._mobile_header_failures(390, in_header)
    )
    no_slot = _healthy_mobile_header() | {"actionsInMobileSlot": False}
    assert (
        "/: mobile theme control remains in the header at 390px"
        in _frontend_gate_layout._mobile_header_failures(390, no_slot)
    )


def test_mobile_header_failures_reports_theme_control_above_content() -> None:
    """The control must sit below the page content, within half a pixel."""
    above = _healthy_mobile_header() | {"actionsTop": 799.0, "contentBottom": 800.0}
    assert (
        "/: mobile theme control is not below the page content at 390px"
        in _frontend_gate_layout._mobile_header_failures(390, above)
    )
    # Exactly at the boundary is compliant: the tolerance is inclusive.
    touching = _healthy_mobile_header() | {"actionsTop": 799.6, "contentBottom": 800.0}
    assert _frontend_gate_layout._mobile_header_failures(390, touching) == []


def test_mobile_header_failures_reports_sub_touch_minimum_theme_control() -> None:
    """A control under 44px fails; exactly 44px passes."""
    small = _healthy_mobile_header() | {"themeHeight": 43.9}
    assert (
        "/: mobile theme control is only 43.9px high at 390px, expected at "
        "least 44px" in _frontend_gate_layout._mobile_header_failures(390, small)
    )
    exact = _healthy_mobile_header() | {"themeHeight": 44.0}
    assert _frontend_gate_layout._mobile_header_failures(390, exact) == []


def test_mobile_header_failures_reports_mismatched_body_offset() -> None:
    """Reject duplicate spacing and viewport-attached headers."""
    for deviation in (
        {"bodyPaddingTop": 68.0},
        {"headerPosition": "fixed"},
        {"headerPosition": "sticky"},
    ):
        assert (
            "/: mobile header must scroll away without a body offset at 390px"
            in _frontend_gate_layout._mobile_header_failures(
                390, _healthy_mobile_header() | deviation
            )
        )
    assert (
        _frontend_gate_layout._mobile_header_failures(
            390, _healthy_mobile_header() | {"bodyPaddingTop": 0.3}
        )
        == []
    )


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


def test_scaled_dimensions_preserve_mark_column_ratio_and_fixed_borders() -> None:
    """A twofold content scale does not double fixed chrome or a column-sized mark."""
    baseline = {
        "wordmark": {"height": 100},
        "hero composition": {"height": 300},
        "form": {"height": 105, "width": 200},
        "form composition": {"height": 207},
    }
    expected = _frontend_gate_layout._expected_scaled_dimension
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
    failures = _frontend_gate_layout._scale_dimension_failures(
        measurements, layouts, scales, {"form": ("height",)}, {"form": ("width",)}
    )
    assert failures == [
        "/: form height is 210.0px at 1440p, expected proportional 205.0px"
    ]
    measurements["4K"]["form"]["width"] += 1
    assert (
        _frontend_gate_layout._scale_dimension_failures(
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
        "formInnerTop": 4,
        "wellTop": 0,
        "wellBottom": 140,
        "formInnerBottom": 104,
        "viewportHeight": 140,
        "headerHeight": 0,
        "rootFontSize": 16,
        "cardLeft": 20,
        "cardRight": 120,
        "heroWidth": 120,
        "heroPaddingLeft": 10,
        "heroPaddingRight": 10,
        "heroInnerWidth": 100,
        "heroMarkWidth": 100,
    }
    assert _frontend_gate_layout._wide_layout_failures({"window": layout}) == []
    broken = dict(
        layout,
        paddingRight=12,
        formInnerLeft=5,
        formInnerTop=30,
        cardRight=115,
        heroInnerWidth=90,
    )
    failures = _frontend_gate_layout._wide_layout_failures({"window": broken})
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
    assert _frontend_gate_layout._header_geometry_failures(sizes, layouts) == []
    sizes["1080p"]["header bar"]["height"] += 1
    sizes["1080p"]["page navigation"] = {"height": 40, "width": 80}
    sizes["1080p"]["theme control"]["height"] += 2
    layouts["1080p"] = {"headerGap": 9, "navGap": 8, "rowSpread": 2}
    failures = _frontend_gate_layout._header_geometry_failures(sizes, layouts)
    assert len(failures) == 6
    assert all("1080p" in failure for failure in failures)


def test_scale_mechanism_rejects_zoom_and_transform_independently() -> None:
    """Both visible and hidden cards must keep native layout scaling."""
    assert (
        _frontend_gate_layout._scale_mechanism_failures(
            [
                {"label": "visible", "zoom": "1", "transform": "none"},
                {"label": "hidden", "zoom": "normal", "transform": "none"},
            ]
        )
        == []
    )
    assert (
        len(
            _frontend_gate_layout._scale_mechanism_failures(
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


def test_enlarged_root_probe_restores_sizing_when_measurement_raises() -> None:
    """A failing geometry read cannot leave the next check at a larger root font."""
    page = MagicMock()
    page.evaluate.side_effect = [None, "18px", RuntimeError("missing form"), None]
    with pytest.raises(RuntimeError, match="missing form"):
        _frontend_gate_layout._measure_enlarged_root(page, "http://local")
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
        _frontend_gate_layout._composition_bounds_failures(
            sizes, layouts, scales, mobile, inputs
        )
        == []
    )
    sizes["4K"]["form composition"]["width"] = 946
    failures = _frontend_gate_layout._composition_bounds_failures(
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
