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

SOURCE_CSS = Path(__file__).resolve().parents[3] / "static" / "css" / "tailwind.src.css"


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


@pytest.mark.parametrize(
    ("gap", "top", "passes"),
    [
        # The form sits 0.25rem (4px) below the well; 1px either side is fine.
        (4, 4, True),
        (24, 3, True),
        (24, 4.9, True),
        (24, 5, True),
        # Raised higher, or off by 2px either way, fails.
        (24, 24, False),
        (0, 0, False),
        (24, 2, False),
        (24, 6, False),
    ],
)
def test_short_window_form_top_stays_on_the_quarter_rem_floor(gap, top, passes) -> None:
    check = _frontend_gate_layout._expanded_placement_failures
    failures = check("1920x700", _expanded(gap=gap, top=top), short_window=True)
    assert (failures == []) == passes
    assert all("1920x700" in line for line in failures)


def test_expanded_measurement_opens_decade_scope_and_thresholds(monkeypatch) -> None:
    """The measurement asks the page for the expanded state."""
    module = _frontend_gate_layout
    calls = []
    monkeypatch.setattr(module, "_reach_state", lambda *a: calls.append(a))
    monkeypatch.setattr(module, "wait_for_settled", lambda _page: None)
    page = MagicMock()

    module._measure_expanded_placement(page, "http://local", 1920, 700)

    assert calls == [
        (
            page,
            (
                ("select", "#release_scope", "decade"),
                ("click", ".disclosure__summary"),
            ),
        )
    ]


def _keys(mode: str) -> dict:
    """The home keys as they should read in `mode`: one shown, none in the form."""
    return {"inForm": 0, "active": [mode], "hiddenOk": True, "ruleOk": True}


MODE_SWITCH = {
    "albumTop": 191.0,
    "heatmapTop": 191.0,
    "keys": {"album": _keys("album"), "heatmap": _keys("heatmap")},
    "albumKeyText": "1 play across the album 5 different tracks by default",
    "restoredKeyText": "7 plays across the album 5 different tracks by default",
}
HEATMAP_FIRST = {"albumTop": 191.0, "heatmapTop": 191.0}


def _run_large_display_check(
    monkeypatch, full: dict, short: dict, overflow=None
) -> list[str]:
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
    monkeypatch.setattr(module, "_measure_mode_switch_shift", lambda *a: MODE_SWITCH)
    monkeypatch.setattr(
        module, "_measure_heatmap_first_shift", lambda *a: HEATMAP_FIRST
    )
    monkeypatch.setattr(
        module,
        "_measure_home_overflow",
        overflow or (lambda *a: _measured_home()),
    )
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


@pytest.mark.parametrize(
    ("full", "short", "line"),
    [
        # Only the roomy window fails: its gap is judged, the short one passes.
        (_expanded(gap=4, top=10), _expanded(gap=30, top=4), FULL_GAP_LINE),
        # Only the short window fails: its form top is judged, not its gap.
        (_expanded(gap=30, top=10), _expanded(gap=4, top=24), SHORT_TOP_LINE),
    ],
    ids=["small-gap-at-1920x1063", "raised-top-at-1920x700"],
)
def test_large_display_check_reports_the_window_that_misses_its_floor(
    monkeypatch, full, short, line
) -> None:
    failures = _run_large_display_check(monkeypatch, full=full, short=short)
    assert len(failures) == 2
    assert "off-centre at 1920x1063" in failures[0]
    assert failures[1] == line


@pytest.mark.parametrize(
    ("heatmap_top", "failed"),
    [(191.0, False), (191.9, False), (135.0, True), (304.0, True)],
    ids=["no-shift", "within-tolerance", "moves-up", "moves-down"],
)
def test_mode_switch_must_stay_put_when_the_mode_changes(heatmap_top, failed) -> None:
    measured = {"albumTop": 191.0, "heatmapTop": heatmap_top}

    failures = _frontend_gate_layout._mode_switch_failures("1920x1063", measured)

    assert bool(failures) is failed
    assert all("1920x1063" in line for line in failures)


SYNCED = [{"text": "Play animations", "pressed": "true"}] * 2
PAUSE_OK = {"shown": 1, "inside": True, "afterClick": SYNCED}


def _home_state(overflow=0, **pause) -> dict:
    return {"overflow": overflow, "pause": dict(PAUSE_OK, **pause)}


def _measured_home(album=None, heatmap=None) -> dict:
    return {"album": album or _home_state(), "heatmap": heatmap or _home_state()}


@pytest.mark.parametrize(
    ("measured", "expected"),
    [
        (_measured_home(), []),
        (_measured_home(album=_home_state(92)), ["scrolls 92px", "album mode"]),
        (_measured_home(heatmap=_home_state(1)), ["scrolls 1px", "heatmap mode"]),
        # The rule or markup that places the button is gone: nothing shows.
        (_measured_home(album=_home_state(shown=0)), ["0 pause buttons", "album"]),
        (_measured_home(heatmap=_home_state(shown=2)), ["2 pause buttons", "heatmap"]),
        (_measured_home(album=_home_state(inside=False)), ["outside the window"]),
        # The hidden copy kept its old label after the click.
        (
            _measured_home(
                heatmap=_home_state(
                    afterClick=[
                        {"text": "Play animations", "pressed": "true"},
                        {"text": "Pause animations", "pressed": "false"},
                    ]
                )
            ),
            ["did not follow a click", "heatmap mode"],
        ),
    ],
    ids=[
        "fits",
        "album-scrolls",
        "heatmap-scrolls",
        "no-pause-button",
        "two-pause-buttons",
        "pause-button-off-screen",
        "hidden-copy-not-synced",
    ],
)
def test_the_home_page_must_not_scroll_vertically_in_either_mode(
    measured, expected
) -> None:
    failures = _frontend_gate_layout._home_overflow_failures("1366x768", measured)

    assert len(failures) == (1 if expected else 0)
    assert all(fragment in failures[0] for fragment in expected)


def test_the_large_display_check_measures_the_home_fit_windows(monkeypatch) -> None:
    """A scrolling home page at 1920x1080 or 1366x768 fails the gate."""
    seen = []

    def overflow(_page, _url, width, height):
        seen.append((width, height))
        return _measured_home(album=_home_state(92))

    failures = _run_large_display_check(
        monkeypatch,
        full=_expanded(gap=30, top=4),
        short=_expanded(gap=30, top=4),
        overflow=overflow,
    )

    assert seen == [(1920, 1080), (1366, 768)]
    assert [line for line in failures if "scrolls 92px" in line] == [
        "/: the home page scrolls 92px vertically in album mode at 1920x1080, "
        "expected none",
        "/: the home page scrolls 92px vertically in album mode at 1366x768, "
        "expected none",
    ]


@pytest.mark.parametrize(
    ("change", "expected_fragment"),
    [
        ({}, None),
        ({"album": {"inForm": 1}}, "form stack holds 1"),
        ({"heatmap": {"inForm": 2}}, "form stack holds 2"),
        ({"album": {"active": ["heatmap"]}}, "album mode shows keys ['heatmap']"),
        ({"heatmap": {"active": []}}, "heatmap mode shows keys []"),
        ({"heatmap": {"hiddenOk": False}}, "heatmap mode shows keys"),
        ({"text": "10 plays across the album 5 different tracks"}, "steppers"),
        ({"text": "1 play across the album 3 different tracks"}, "steppers"),
        ({"album": {"ruleOk": False}}, "album key does not end with the 1px"),
        ({"heatmap": {"ruleOk": False}}, "heatmap key does not end with the 1px"),
        ({"restored": "10 plays across 3 different tracks"}, "restored"),
        ({"restored": "7 plays across the album 3 different tracks"}, "restored"),
    ],
    ids=[
        "clean",
        "album-form-explains",
        "heatmap-form-explains",
        "wrong-key-in-album",
        "no-key-in-heatmap",
        "inactive-key-not-hidden",
        "plays-ignore-stepper",
        "tracks-ignore-stepper",
        "album-key-lacks-rule",
        "heatmap-key-lacks-rule",
        "restored-values-ignored",
        "restored-tracks-ignored",
    ],
)
def test_the_form_stack_holds_no_key_and_each_mode_shows_its_own(
    change, expected_fragment
) -> None:
    measured = {
        "keys": {
            mode: {**_keys(mode), **change.get(mode, {})}
            for mode in ("album", "heatmap")
        },
        "albumKeyText": change.get("text", MODE_SWITCH["albumKeyText"]),
        "restoredKeyText": change.get("restored", MODE_SWITCH["restoredKeyText"]),
    }

    failures = _frontend_gate_layout._home_key_failures("1920x1063", measured)

    if expected_fragment is None:
        assert failures == []
    else:
        assert len(failures) == 1
        assert expected_fragment in failures[0]
        assert "1920x1063" in failures[0]


@pytest.mark.parametrize(
    ("phone", "expected_fragment"),
    [
        ({"keysShown": 0, "yearHintShown": True}, None),
        ({"keysShown": 1, "yearHintShown": True}, "keys are shown at 390px"),
        ({"keysShown": 0, "yearHintShown": False}, "year hint is hidden at 390px"),
    ],
    ids=["clean", "keys-on-phone", "year-hint-missing-on-phone"],
)
def test_a_phone_hides_the_keys_and_keeps_the_year_hint(
    phone, expected_fragment
) -> None:
    failures = _frontend_gate_layout._phone_home_failures(390, phone)

    if expected_fragment is None:
        assert failures == []
    else:
        assert len(failures) == 1
        assert expected_fragment in failures[0]


@pytest.mark.parametrize(
    "stub", [MODE_SWITCH, HEATMAP_FIRST], ids=["album-first", "heatmap-first"]
)
def test_large_display_check_reports_a_mode_switch_that_moves(
    monkeypatch, stub
) -> None:
    def run() -> list[str]:
        return _run_large_display_check(
            monkeypatch, full=_expanded(gap=30, top=10), short=_expanded(gap=30, top=4)
        )

    baseline = run()
    monkeypatch.setitem(stub, "heatmapTop", 304.0)

    assert len(run()) == len(baseline) + 1


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


@pytest.mark.parametrize(
    ("mode", "width", "measure"),
    [
        ("album", 1920, _strip_measure()),
        ("heatmap", 1100, _strip_measure(columns=False, container=400)),
    ],
    ids=["three-columns-when-wide", "stacked-rows-when-narrow"],
)
def test_strip_passes_the_form_its_container_calls_for(mode, width, measure) -> None:
    assert _strip_layout_failures(mode, width, measure) == []


def test_strip_names_the_mode_and_width_of_a_wrapped_term() -> None:
    wrapped = _strip_measure(term_heights=(23, 46, 23))
    assert _strip_layout_failures("heatmap", 1500, wrapped) == [
        "/: heatmap strip term wraps at 1500px"
    ]
    # Up to 1.2 line heights is still one line.
    one_line = _strip_measure(term_heights=(27, 23, 23))
    assert _strip_layout_failures("heatmap", 1500, one_line) == []


@pytest.mark.parametrize(
    ("mode", "width", "measure", "message"),
    [
        (
            "album",
            1920,
            _strip_measure(columns=False, container=800),
            "/: album strip is not three columns at 1920px "
            "(container 800px, columns from 520px)",
        ),
        (
            "heatmap",
            1100,
            _strip_measure(columns=True, container=400),
            "/: heatmap strip is not stacked rows at 1100px "
            "(container 400px, rows below 520px)",
        ),
    ],
    ids=["rows-where-columns-fit", "columns-where-rows-are-needed"],
)
def test_strip_in_the_wrong_form_for_its_container_fails(
    mode, width, measure, message
) -> None:
    assert _strip_layout_failures(mode, width, measure) == [message]


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


def test_strip_display_follows_the_860_cut() -> None:
    hidden = _strip_measure(displayed=False)
    assert _strip_layout_failures("album", 859, hidden) == []
    assert _strip_layout_failures("heatmap", 390, hidden) == []
    assert _strip_layout_failures("heatmap", 859, _strip_measure()) == [
        "/: heatmap strip is displayed at 859px"
    ]
    assert _strip_layout_failures("album", 390, _strip_measure()) == [
        "/: album strip is displayed at 390px"
    ]
    assert _strip_layout_failures("album", 860, hidden) == [
        "/: album strip is not displayed at 860px"
    ]


def _strip_axes(**override) -> dict:
    """A wide columns measurement with only the named axes replaced."""
    return {**_strip_measure(), **override}


def _rows_axes(**override) -> dict:
    """A narrow rows measurement with only the named axes replaced."""
    return {**_strip_measure(columns=False, container=400), **override}


COLUMNS_BROKEN = (
    "/: album strip is not three columns at 1920px "
    "(container 800px, columns from 520px)"
)
ROWS_BROKEN = (
    "/: heatmap strip is not stacked rows at 1100px (container 400px, rows below 520px)"
)


@pytest.mark.parametrize(
    ("measure", "failures"),
    [
        (_strip_axes(itemLefts=[10, 10, 10]), [COLUMNS_BROKEN]),
        (_strip_axes(itemTops=[100, 102, 100]), [COLUMNS_BROKEN]),
        (_strip_axes(itemLefts=[10, 260, 260]), [COLUMNS_BROKEN]),
        (_strip_axes(itemTops=[100, 100.4, 100]), []),
    ],
    ids=["equal-lefts", "offset-tops", "flat-step", "tops-within-tolerance"],
)
def test_strip_columns_need_equal_tops_and_rising_lefts_each_on_their_own(
    measure, failures
) -> None:
    assert _strip_layout_failures("album", 1920, measure) == failures


@pytest.mark.parametrize(
    ("measure", "failures"),
    [
        (_rows_axes(itemTops=[100, 100, 100]), [ROWS_BROKEN]),
        (_rows_axes(itemLefts=[10, 60, 110]), [ROWS_BROKEN]),
        (_rows_axes(itemLefts=[10, 12, 10]), [ROWS_BROKEN]),
        (_rows_axes(itemTops=[100, 160, 160]), [ROWS_BROKEN]),
        (_rows_axes(itemLefts=[10, 10.4, 10]), []),
    ],
    ids=[
        "equal-tops",
        "rising-lefts",
        "offset-lefts",
        "flat-step",
        "lefts-within-tolerance",
    ],
)
def test_strip_rows_need_rising_tops_and_equal_lefts_each_on_their_own(
    measure, failures
) -> None:
    assert _strip_layout_failures("heatmap", 1100, measure) == failures


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


def test_strip_sweep_reaches_the_widths_below_the_860_cut(monkeypatch) -> None:
    """Widths 859 and 390 stay in the sweep: a strip shown there is reported."""
    page = MagicMock()
    monkeypatch.setattr(
        _frontend_gate_layout, "_measure_strip", lambda *_: _strip_measure()
    )
    monkeypatch.setattr(_frontend_gate_layout, "_headline_wrap_failures", lambda *_: [])

    # The stub shows the strip at every width, so each sub-860 width reports it.
    assert _check_desktop_scale_bounds(page, "http://local") == [
        "/: album strip is displayed at 859px",
        "/: heatmap strip is displayed at 859px",
        "/: album strip is displayed at 390px",
        "/: heatmap strip is displayed at 390px",
    ]
