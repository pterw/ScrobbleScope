"""Parity and behaviour tests for the layout slice of the frontend gate."""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_layout, frontend_gate
from scripts.dev._frontend_gate_layout import (
    REQUIRED_FONT_FAMILIES,
    _check_desktop_scale_bounds,
    _headline_wrap_failures,
    _state_dimension_failures,
    _strip_layout_failures,
    _touch_minimum_failures,
    check_shell_scales_with_text,
)
from tests.scripts.dev.gate_parity import defined_names

SOURCE_CSS = Path(__file__).resolve().parents[3] / "static" / "css" / "tailwind.src.css"

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
    "_form_centring_failures",
    "_measure_expanded_placement",
    "_expanded_placement_failures",
    "_header_geometry_failures",
    "_scale_mechanism_failures",
    "_touch_minimum_failures",
    "_mobile_header_failures",
    "_state_dimension_failures",
    "_headline_wrap_failures",
    "_measure_strip",
    "_strip_layout_failures",
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


def _strip_measure(
    *,
    columns: bool = True,
    container: float = 800,
    font: float = 20,
    term_heights=(23, 23, 23),
    displayed: bool = True,
) -> dict:
    """A strip measurement; columns share a top, rows share a left."""
    if not displayed:
        return {
            "displayed": False,
            "containerWidth": container,
            "wrapFontPx": font,
            "itemTops": [],
            "itemLefts": [],
            "termHeights": [],
            "termLineHeight": 0,
        }
    return {
        "displayed": True,
        "containerWidth": container,
        "wrapFontPx": font,
        "itemTops": [100, 100, 100] if columns else [100, 160, 220],
        "itemLefts": [10, 260, 510] if columns else [10, 10, 10],
        "termHeights": list(term_heights),
        "termLineHeight": 23,
    }


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
        if "data-mode-marks" in selector:
            mode = "heatmap" if '"heatmap"' in selector else "album"
            width = current_width["value"]
            locator.evaluate.return_value = _strip_measure(
                displayed=width >= 860,
                container=400 if width < 1100 else 800,
                columns=width >= 1100,
                term_heights=(23, 46, 23)
                if (mode, width) == ("heatmap", 1100)
                else (23, 23, 23),
            )
        elif selector.endswith(" h1"):
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
    # The strip sweep adds 900/1100 (narrow column) and the hidden cut at
    # 859/390; only the heatmap strip at 1100px wraps a term here.
    assert _check_desktop_scale_bounds(page, "http://local") == [
        "/: album headline wraps at 1200px",
        "/: heatmap headline wraps at 1200px",
        "/: heatmap strip term wraps at 1100px",
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


def _centred_layout() -> dict:
    """A 1080p-like default state: 56px above the card, 136px below (80 = 5rem)."""
    return {
        "rootFontSize": 16,
        "wellTop": 76,
        "formInnerTop": 132,
        "formInnerBottom": 809,
        "viewportHeight": 945,
    }


def test_form_centring_passes_when_the_centring_term_places_the_card() -> None:
    """Twice the 2.5rem lift between the gaps is the unclamped placement."""
    assert (
        _frontend_gate_layout._form_centring_failures("1080p", _centred_layout()) == []
    )


def test_form_centring_reports_a_card_pinned_under_the_header() -> None:
    """A card too tall to centre sits on the 0.25rem clamp and is reported."""
    pinned = dict(_centred_layout(), formInnerTop=80, formInnerBottom=799)
    assert _frontend_gate_layout._form_centring_failures("1080p", pinned) == [
        "/: form is pinned under the header at 1080p (4.0px above the card, "
        "the 0.25rem clamp); the card is too tall to centre"
    ]


def test_form_centring_reports_a_card_off_the_centring_rule() -> None:
    """Clear of the clamp but not where the centring term puts it is reported."""
    shifted = dict(_centred_layout(), formInnerTop=152, formInnerBottom=829)
    failures = _frontend_gate_layout._form_centring_failures("1080p", shifted)
    assert len(failures) == 1
    assert "off-centre at 1080p" in failures[0]
    assert "76.0px above the card and 116.0px below" in failures[0]


def _expanded(gap: float = 24, top: float = 24, root: float = 16) -> dict:
    """An expanded-form measurement; the gap and top are in px."""
    return {
        "rootFontSize": root,
        "gapAboveSwitch": gap,
        "formInnerTop": 76 + top,
        "wellTop": 76,
    }


def test_expanded_placement_holds_the_gap_above_the_switch_inclusively() -> None:
    """24px at root 16 (1.5rem) passes, 4px fails, 22.9px fails, 23.1px passes."""
    check = _frontend_gate_layout._expanded_placement_failures
    assert check("1920x1063", _expanded(gap=24)) == []
    assert check("1920x1063", _expanded(gap=23.1)) == []
    failures = check("1920x1063", _expanded(gap=22.9))
    assert len(failures) == 1 and "1920x1063" in failures[0]
    failures = check("1920x1063", _expanded(gap=4))
    assert len(failures) == 1 and "4.0px" in failures[0]


def test_expanded_placement_floor_follows_the_root_font_size() -> None:
    """The 1.5rem floor is relative: 24px is short at a 20px root (30px)."""
    check = _frontend_gate_layout._expanded_placement_failures
    assert check("1920x1063", _expanded(gap=24, root=20)) != []
    assert check("1920x1063", _expanded(gap=30, root=20)) == []


def test_short_window_form_top_stays_on_the_quarter_rem_floor() -> None:
    """A short window puts the form 0.25rem below the well; raising it fails."""
    check = _frontend_gate_layout._expanded_placement_failures
    assert check("1920x700", _expanded(gap=4, top=4), short_window=True) == []
    failures = check("1920x700", _expanded(gap=24, top=24), short_window=True)
    assert len(failures) == 1 and "1920x700" in failures[0]
    assert check("1920x700", _expanded(gap=0, top=0), short_window=True) != []


def test_short_window_form_top_tolerance_is_one_pixel_either_side() -> None:
    """1px off the 4px floor passes; 2px off fails, above and below."""
    check = _frontend_gate_layout._expanded_placement_failures
    for top in (3, 4.9, 5):
        assert check("1920x700", _expanded(top=top), short_window=True) == []
    for top in (2, 6):
        assert check("1920x700", _expanded(top=top), short_window=True) != []


def test_expanded_measurement_opens_decade_scope_and_thresholds(monkeypatch) -> None:
    """The measurement asks for the expanded state and returns the page reading."""
    module = _frontend_gate_layout
    calls = []
    monkeypatch.setattr(module, "_reach_state", lambda *a: calls.append(a))
    monkeypatch.setattr(module, "wait_for_settled", lambda _page: None)
    page = MagicMock()

    result = module._measure_expanded_placement(page, "http://local", 1920, 700)

    page.set_viewport_size.assert_called_once_with({"width": 1920, "height": 700})
    assert calls == [
        (
            page,
            (
                ("select", "#release_scope", "decade"),
                ("click", ".disclosure__summary"),
            ),
        )
    ]
    assert result is page.evaluate.return_value


def test_collapsed_form_keeps_the_full_lift_and_a_shorter_lift_fails() -> None:
    """The collapsed form keeps the 2.5rem lift; a 1.5rem lift is off-centre."""
    full = _centred_layout()
    assert _frontend_gate_layout._form_centring_failures("1920x1063", full) == []
    # A 1.5rem lift puts the card 16px lower: above 72, below 120 (gap 48, not 80).
    short_lift = dict(full, formInnerTop=148, formInnerBottom=825)
    failures = _frontend_gate_layout._form_centring_failures("1920x1063", short_lift)
    assert len(failures) == 1 and "off-centre at 1920x1063" in failures[0]


def _run_large_display_check(monkeypatch, full: dict, short: dict) -> list[str]:
    """Run the scale-parity check with the 1920x1063 / 1920x700 expanded stubs."""
    module = _frontend_gate_layout
    measured_at = []

    def expanded(_page, _url, width, height):
        measured_at.append((width, height))
        return full if (width, height) == (1920, 1063) else short

    header_px = module._clamp_px(4.25, 2.96875, 4.75, 1920, root_px=20)
    root_width = 27.5 * 20 * ((900 - header_px) / ((42.0625 + 4) * 20))
    state = {"dimensions": {}, "documentHeight": 2000, "viewportHeight": 945}
    monkeypatch.setattr(module, "_measure_expanded_placement", expanded)
    last_window = []

    def scale_dimensions(_page, _url, _selectors, width, height):
        last_window[:] = [(width, height)]
        return _all_named()

    def wide_layout(_page):
        # Only the collapsed 1920x1063 window is off the centring rule.
        if last_window == [(1920, 1063)]:
            return dict(_centred_layout(), formInnerTop=152, formInnerBottom=829)
        return _centred_layout()

    monkeypatch.setattr(module, "_measure_scale_dimensions", scale_dimensions)
    monkeypatch.setattr(module, "_measure_wide_layout", wide_layout)
    monkeypatch.setattr(module, "_measure_zoom_and_transform", lambda _page: [])
    monkeypatch.setattr(module, "_measure_mobile_headers", lambda *a: {})
    monkeypatch.setattr(module, "_measure_fixed_state", lambda *a: state)
    monkeypatch.setattr(module, "_measure_enlarged_root", lambda *a: root_width)
    monkeypatch.setattr(module, "_check_desktop_scale_bounds", lambda *a: [])
    for judge in (
        "_scale_dimension_failures",
        "_composition_bounds_failures",
        "_wide_layout_failures",
        "_header_geometry_failures",
        "_scale_mechanism_failures",
        "_state_dimension_failures",
    ):
        monkeypatch.setattr(module, judge, lambda *a, **k: [])
    page = MagicMock()
    page.evaluate.return_value = {"factor": "", "columns": 1}

    failures = module.check_large_display_scale_parity(page, "http://local")

    assert (1920, 1063) in measured_at and (1920, 700) in measured_at
    return failures


FULL_GAP_LINE = (
    "/: expanded form leaves 4.0px between the header and the mode switch "
    "at 1920x1063, expected at least 1.5rem (24.0px)"
)
SHORT_TOP_LINE = (
    "/: expanded form top is 24.0px below the well at 1920x700, "
    "expected the 0.25rem floor (4.0px)"
)


def test_large_display_check_reports_a_small_expanded_gap_at_1920x1063(
    monkeypatch,
) -> None:
    """Only the roomy window fails: its gap is judged, the short one passes."""
    failures = _run_large_display_check(
        monkeypatch,
        full=_expanded(gap=4, top=10),
        short=_expanded(gap=30, top=4),
    )
    assert len(failures) == 2
    assert "off-centre at 1920x1063" in failures[0]
    assert failures[1] == FULL_GAP_LINE


def test_large_display_check_reports_a_raised_form_top_at_1920x700(
    monkeypatch,
) -> None:
    """Only the short window fails: dropping its call or mislabelling it shows."""
    failures = _run_large_display_check(
        monkeypatch,
        full=_expanded(gap=30, top=10),
        short=_expanded(gap=4, top=24),
    )
    assert len(failures) == 2
    assert "off-centre at 1920x1063" in failures[0]
    assert failures[1] == SHORT_TOP_LINE


def _all_named() -> dict:
    """Every selector the scale-parity check names, measured as empty."""
    names = (
        "hero composition",
        "form composition",
        "wordmark",
        "headline",
        "form",
        "submit",
        "field",
        "label",
        "theme control",
        "input",
        "mode tab",
        "page navigation",
        "header bar",
    )
    return {name: {} for name in names}


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


def test_the_kit_check_loads_the_first_face_of_every_font_token() -> None:
    """Every --font-* token's first family is one check_fonts asks the kit for.

    check_fonts can only warn about a family it loads. A token whose primary
    face is missing from REQUIRED_FONT_FAMILIES renders in its fallback with
    no warning at all -- which is what a new display serif would do if the
    list kept naming only the old one.
    """
    source = SOURCE_CSS.read_text(encoding="utf-8")
    first_faces = re.findall(r'--font-[a-z-]+:\s*"([^"]+)"', source)
    assert len(first_faces) == 5, first_faces
    assert sorted(set(first_faces) - set(REQUIRED_FONT_FAMILIES)) == []


def test_strip_passes_three_columns_when_the_container_is_wide() -> None:
    assert _strip_layout_failures("album", 1920, _strip_measure()) == []


def test_strip_passes_stacked_rows_when_the_container_is_narrow() -> None:
    narrow = _strip_measure(columns=False, container=400)
    assert _strip_layout_failures("heatmap", 1100, narrow) == []


def test_strip_names_the_mode_and_width_of_a_wrapped_term() -> None:
    wrapped = _strip_measure(term_heights=(23, 46, 23))
    assert _strip_layout_failures("heatmap", 1500, wrapped) == [
        "/: heatmap strip term wraps at 1500px"
    ]
    # Up to 1.2 line heights is still one line.
    one_line = _strip_measure(term_heights=(27, 23, 23))
    assert _strip_layout_failures("heatmap", 1500, one_line) == []


def test_strip_in_rows_where_the_container_allows_columns_fails() -> None:
    rows = _strip_measure(columns=False, container=800)
    assert _strip_layout_failures("album", 1920, rows) == [
        "/: album strip is not three columns at 1920px "
        "(container 800px, columns from 520px)"
    ]


def test_strip_in_columns_where_the_container_is_narrow_fails() -> None:
    columns = _strip_measure(columns=True, container=400)
    assert _strip_layout_failures("heatmap", 1100, columns) == [
        "/: heatmap strip is not stacked rows at 1100px "
        "(container 400px, rows below 520px)"
    ]


def test_strip_container_at_exactly_26_em_is_columns() -> None:
    exactly = {"container": 26 * 18.5, "font": 18.5}
    assert _strip_layout_failures("album", 1200, _strip_measure(**exactly)) == []
    rows = _strip_measure(columns=False, **exactly)
    assert _strip_layout_failures("album", 1200, rows) == [
        "/: album strip is not three columns at 1200px "
        "(container 481px, columns from 481px)"
    ]
    below = _strip_measure(columns=False, container=26 * 18.5 - 0.1, font=18.5)
    assert _strip_layout_failures("album", 1200, below) == []


def test_strip_threshold_uses_the_wrap_font_size_not_the_term_size() -> None:
    # 600px wide: columns at a 20px em (threshold 520), rows at a 24px em (624).
    assert _strip_layout_failures("album", 1200, _strip_measure(container=600)) == []
    big_em = _strip_measure(container=600, font=24)
    assert _strip_layout_failures("album", 1200, big_em) == [
        "/: album strip is not stacked rows at 1200px "
        "(container 600px, rows below 624px)"
    ]


def test_strip_hidden_below_860_passes_and_displayed_at_859_fails() -> None:
    hidden = _strip_measure(displayed=False)
    assert _strip_layout_failures("album", 859, hidden) == []
    assert _strip_layout_failures("heatmap", 390, hidden) == []
    assert _strip_layout_failures("heatmap", 859, _strip_measure()) == [
        "/: heatmap strip is displayed at 859px"
    ]
    assert _strip_layout_failures("album", 390, _strip_measure()) == [
        "/: album strip is displayed at 390px"
    ]


def test_strip_hidden_at_860_and_above_fails() -> None:
    hidden = _strip_measure(displayed=False)
    assert _strip_layout_failures("album", 860, hidden) == [
        "/: album strip is not displayed at 860px"
    ]


def _strip_axes(**override) -> dict:
    """A wide columns measurement with only the named axes replaced."""
    return {**_strip_measure(), **override}


def _rows_axes(**override) -> dict:
    """A narrow rows measurement with only the named axes replaced."""
    return {**_strip_measure(columns=False, container=400), **override}


def test_strip_columns_need_equal_tops_and_rising_lefts_each_on_their_own() -> None:
    equal_lefts = _strip_axes(itemLefts=[10, 10, 10])
    offset_tops = _strip_axes(itemTops=[100, 102, 100])
    flat_step = _strip_axes(itemLefts=[10, 260, 260])
    for broken in (equal_lefts, offset_tops, flat_step):
        assert _strip_layout_failures("album", 1920, broken) == [
            "/: album strip is not three columns at 1920px "
            "(container 800px, columns from 520px)"
        ]
    within_tolerance = _strip_axes(itemTops=[100, 100.4, 100])
    assert _strip_layout_failures("album", 1920, within_tolerance) == []


def test_strip_rows_need_rising_tops_and_equal_lefts_each_on_their_own() -> None:
    equal_tops = _rows_axes(itemTops=[100, 100, 100])
    rising_lefts = _rows_axes(itemLefts=[10, 60, 110])
    offset_lefts = _rows_axes(itemLefts=[10, 12, 10])
    flat_step = _rows_axes(itemTops=[100, 160, 160])
    for broken in (equal_tops, rising_lefts, offset_lefts, flat_step):
        assert _strip_layout_failures("heatmap", 1100, broken) == [
            "/: heatmap strip is not stacked rows at 1100px "
            "(container 400px, rows below 520px)"
        ]
    within_tolerance = _rows_axes(itemLefts=[10, 10.4, 10])
    assert _strip_layout_failures("heatmap", 1100, within_tolerance) == []


def test_strip_term_wrap_limit_is_1_2_line_heights_not_more() -> None:
    wrapped = _strip_measure(term_heights=(23, 23 * 1.3, 23))
    assert _strip_layout_failures("album", 1500, wrapped) == [
        "/: album strip term wraps at 1500px"
    ]
    at_limit = _strip_measure(term_heights=(23, 23 * 1.2, 23))
    assert _strip_layout_failures("album", 1500, at_limit) == []


@pytest.mark.parametrize(
    ("override", "problem"),
    [
        ({"itemTops": [100, 100], "itemLefts": [10, 260]}, "fewer than three items"),
        ({"itemTops": [], "itemLefts": []}, "fewer than three items"),
        ({"termHeights": []}, "no measurable term"),
        ({"termLineHeight": float("nan")}, "no measurable term"),
        ({"termLineHeight": "normal"}, "no measurable term"),
        ({"termLineHeight": 0}, "no measurable term"),
    ],
)
def test_strip_fails_closed_on_a_thin_measurement(override, problem) -> None:
    assert _strip_layout_failures("heatmap", 1200, _strip_axes(**override)) == [
        f"/: heatmap strip has {problem} at 1200px"
    ]


def test_strip_sweep_visits_every_width_at_900px_with_a_fresh_page_load(
    monkeypatch,
) -> None:
    """Hidden-cut widths 859 and 390 stay in the sweep; each is loaded, then measured."""
    events: list[tuple] = []
    context = MagicMock()
    probe = context.new_page.return_value
    page = MagicMock()
    page.context.browser.new_context.return_value = context
    probe.set_viewport_size.side_effect = lambda size: events.append(
        ("viewport", size["width"], size["height"])
    )
    probe.goto.side_effect = lambda *args, **kwargs: events.append(("goto",))
    probe.evaluate.side_effect = lambda script: (
        events.append(("fonts",))
        if script == frontend_gate.FONTS_READY_EXPRESSION
        else {}
    )

    def measure(_probe, mode: str) -> dict:
        events.append(("measure", mode))
        return _strip_measure()

    monkeypatch.setattr(_frontend_gate_layout, "_measure_strip", measure)
    monkeypatch.setattr(_frontend_gate_layout, "_headline_wrap_failures", lambda *_: [])

    # The stub shows the strip at every width, so each sub-860 width reports it.
    assert _check_desktop_scale_bounds(page, "http://local") == [
        "/: album strip is displayed at 859px",
        "/: heatmap strip is displayed at 859px",
        "/: album strip is displayed at 390px",
        "/: heatmap strip is displayed at 390px",
    ]
    expected = [
        step
        for width in (900, 1100, 1200, 1500, 1920, 2560, 859, 390)
        for step in (
            ("viewport", width, 900),
            ("goto",),
            ("fonts",),
            ("measure", "album"),
            ("measure", "heatmap"),
        )
    ]
    start = events.index(expected[0])
    assert events[start : start + len(expected)] == expected
