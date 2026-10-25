"""Parity tests for the pure colour maths extracted under F-B21-51.

These helpers moved out of `frontend_gate.py` into
`scripts/dev/_frontend_gate_colour.py`. The move is only safe if the maths and
the import surface are both pinned, so this file does two jobs:

1. asserts the values (WCAG endpoints, blend endpoints, clamp boundaries), and
2. asserts the facade still re-exports every moved name, because the whole
   point of a facade is that no caller has to know the split happened.

The boundary cases are deliberate. A `clamp()` that scales the `vw` term with
the root font size, or a "worst contrast" that keeps the first surface instead
of the minimum, both look right on the happy path and are wrong in the browser.
"""

from __future__ import annotations

import pytest

from scripts.dev import _frontend_gate_colour
from scripts.dev._frontend_gate_colour import (
    _clamp_px,
    _composite_over,
    _contrast_ratio,
    _divider_contrast_failure,
    _is_forbidden_surface,
    _parse_rgb_string,
    _relative_luminance,
    _worst_divider_contrast,
)


class TestParseRgbString:
    """The parser has to read both a computed rgb() and a computed rgba()."""

    def test_reads_three_channels_without_alpha(self):
        assert _parse_rgb_string("rgb(255, 0, 0)") == (255.0, 0.0, 0.0, 1.0)

    def test_reads_a_fractional_alpha(self):
        assert _parse_rgb_string("rgba(0, 0, 0, 0.5)") == (0.0, 0.0, 0.0, 0.5)

    def test_reads_a_zero_alpha_as_zero_not_a_default(self):
        """A transparent colour must not be silently promoted to opaque."""
        assert _parse_rgb_string("rgba(1, 2, 3, 0)") == (1.0, 2.0, 3.0, 0.0)


class TestRelativeLuminance:
    """WCAG anchors, so a refactor cannot drift the transfer function."""

    def test_white_is_one(self):
        assert _relative_luminance((255, 255, 255)) == pytest.approx(1.0)

    def test_black_is_zero(self):
        assert _relative_luminance((0, 0, 0)) == pytest.approx(0.0)

    def test_a_dark_channel_uses_the_linear_segment(self):
        """Values at or below 0.03928 divide by 12.92 rather than curve."""
        assert _relative_luminance((10, 0, 0)) == pytest.approx(
            0.2126 * (10 / 255 / 12.92)
        )


class TestContrastRatio:
    """The two anchors the divider check is built on."""

    def test_black_on_white_is_twenty_one_to_one(self):
        assert _contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)

    def test_a_colour_against_itself_is_one_to_one(self):
        assert _contrast_ratio((90, 90, 90), (90, 90, 90)) == pytest.approx(1.0)

    def test_the_order_of_the_two_colours_does_not_matter(self):
        assert _contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(
            _contrast_ratio((255, 255, 255), (0, 0, 0))
        )


class TestCompositeOver:
    """Blending, including both endpoints."""

    def test_an_opaque_foreground_wins_outright(self):
        assert _composite_over((255.0, 0.0, 0.0, 1.0), (0.0, 0.0, 255.0)) == (
            255.0,
            0.0,
            0.0,
        )

    def test_a_transparent_foreground_leaves_the_background(self):
        assert _composite_over((255.0, 0.0, 0.0, 0.0), (0.0, 0.0, 255.0)) == (
            0.0,
            0.0,
            255.0,
        )

    def test_a_half_alpha_lands_between_the_two(self):
        assert _composite_over((255.0, 0.0, 0.0, 0.5), (0.0, 0.0, 255.0)) == (
            127.5,
            0.0,
            127.5,
        )


class TestClampPx:
    """CSS clamp() resolution, where the two rem bounds scale and vw does not."""

    def test_the_vw_term_when_it_sits_inside_both_bounds(self):
        assert _clamp_px(1.0, 10.0, 20.0, 1000.0) == pytest.approx(100.0)

    def test_clamps_up_to_the_minimum(self):
        assert _clamp_px(10.0, 1.0, 20.0, 100.0, root_px=16.0) == pytest.approx(160.0)

    def test_clamps_down_to_the_maximum(self):
        assert _clamp_px(1.0, 100.0, 3.0, 1000.0, root_px=16.0) == pytest.approx(48.0)

    def test_the_vw_term_does_not_scale_with_the_root_font_size(self):
        """The adversarial case: a naive rewrite applies the root to vw too.

        With the vw term winning in both runs, growing the root font size must
        leave the resolved value untouched. If it moves, the helper would
        disagree with the browser exactly when a reader enlarges their text,
        which is the failure the surrounding checks exist to catch.
        """
        assert _clamp_px(0.1, 10.0, 100.0, 1000.0, root_px=16.0) == pytest.approx(
            _clamp_px(0.1, 10.0, 100.0, 1000.0, root_px=32.0)
        )

    def test_the_rem_bounds_do_scale_with_the_root_font_size(self):
        """The other half of the same claim, so the test above is not vacuous."""
        assert _clamp_px(10.0, 1.0, 20.0, 100.0, root_px=32.0) == pytest.approx(
            2 * _clamp_px(10.0, 1.0, 20.0, 100.0, root_px=16.0)
        )


class TestWorstDividerContrast:
    """A divider over several surfaces takes the lowest ratio, not the first."""

    surfaces = ("rgb(255, 255, 255)", "rgb(200, 200, 200)")

    def test_keeps_the_minimum_across_the_surface_list(self):
        border = "rgba(0, 0, 0, 0.5)"
        individually = [
            _worst_divider_contrast(border, surface) for surface in self.surfaces
        ]
        assert _worst_divider_contrast(border, *self.surfaces) == pytest.approx(
            min(individually)
        )

    def test_adding_another_surface_cannot_raise_the_result(self):
        border = "rgba(0, 0, 0, 0.5)"
        with_one = _worst_divider_contrast(border, self.surfaces[0])
        with_two = _worst_divider_contrast(border, *self.surfaces)
        assert with_two <= with_one + 1e-9


class TestDividerContrastFailure:
    """The message contract, including the token it blames (F-B21-40)."""

    def test_passes_at_exactly_the_threshold(self):
        assert _divider_contrast_failure("light header", 3.0) is None

    @pytest.mark.parametrize(("ratio", "figure"), [(2.5, "2.50:1"), (2.9999, "3.00:1")])
    def test_reports_below_the_threshold(self, ratio, figure):
        message = _divider_contrast_failure("light header", ratio)
        assert message is not None
        assert figure in message
        assert "3:1" in message

    def test_blames_the_token_it_was_given(self):
        message = _divider_contrast_failure(
            "index well divider", 1.2, token="--ss-border-divider"
        )
        assert message is not None
        assert "--ss-border-divider" in message
        assert "--shell-border" not in message


class TestColourSerializations:
    """Every serialization a browser can hand back, read or refused.

    Measured 2026-09-20 in both engines the gate runs: a computed
    `color-mix(in srgb, ...)` comes back as `color(srgb 0.96 0.94 0.91)`, with
    channels in 0-1 rather than 0-255. Read as 0-255 those channels collapse
    to near black, which is how a real contrast measurement on the results
    table reported 1.19:1 for ink that plainly reads against it. Every other
    token the gate measures serialized as rgb()/rgba() in both engines, which
    is why no existing check was wrong -- the defect was waiting for the first
    check to measure a color-mix() surface.
    """

    def test_reads_the_color_srgb_form(self):
        assert _parse_rgb_string("color(srgb 0.98 0.97 1)") == (
            249.9,
            247.35,
            255.0,
            1.0,
        )

    def test_reads_the_color_srgb_form_with_alpha(self):
        assert _parse_rgb_string("color(srgb 0 0 0 / 0.5)") == (0.0, 0.0, 0.0, 0.5)

    def test_still_reads_the_rgb_forms(self):
        assert _parse_rgb_string("rgb(26, 24, 32)") == (26.0, 24.0, 32.0, 1.0)
        assert _parse_rgb_string("rgba(26, 24, 32, 0.5)") == (26.0, 24.0, 32.0, 0.5)

    @pytest.mark.parametrize(
        "value",
        [
            "oklch(0.7 0.15 250)",
            "lab(52.2% 40.1 59.9)",
            "hsl(210 50% 40%)",
            "color(display-p3 0.5 0.2 0.1)",
        ],
    )
    def test_refuses_a_serialization_it_cannot_read(self, value):
        """A wrong number is worse than a stopped check.

        These forms all carry three leading numbers that are not 0-255 sRGB
        channels. Guessing at them produces a plausible-looking ratio from a
        colour nobody painted, and a contrast gate that reports a wrong ratio
        is the "wrong green" `docs/agents/global-rules.md` puts above every
        other rule. The name of the value is in the message because the
        reader will not be the person who wrote the check.
        """
        with pytest.raises(ValueError, match="serialization"):
            _parse_rgb_string(value)


class TestForbiddenSurfaceDetection:
    """A forbidden surface must be caught in whatever form it arrives.

    The scan compares a computed background against the cool-greys the warm
    themes replaced. It used to compare strings, so the same colour arriving
    through a `color-mix()` -- and therefore serialized as `color(srgb ...)`
    -- would not have matched. That is an evasion path, not a false alarm:
    the check would stay green while the surface was on screen.
    """

    def test_matches_the_same_colour_in_another_serialization(self):
        assert _is_forbidden_surface(
            "color(srgb 0.972549 0.976471 0.980392)", ("rgb(248, 249, 250)",)
        )

    def test_matches_the_plain_rgb_form(self):
        assert _is_forbidden_surface("rgb(18, 18, 18)", ("rgb(18, 18, 18)",))

    def test_does_not_match_a_different_colour(self):
        assert not _is_forbidden_surface("rgb(250, 247, 240)", ("rgb(248, 249, 250)",))

    def test_tolerates_a_serialization_the_parser_refuses(self):
        """The scan reads every element on the page, so it cannot raise.

        A page carrying one `oklch()` colour must not take the check down;
        that value simply cannot be compared numerically, so it falls back to
        an exact string match and the rest of the scan continues.
        """
        assert not _is_forbidden_surface("oklch(0.7 0.15 250)", ("rgb(18, 18, 18)",))
        assert _is_forbidden_surface("oklch(0.7 0.15 250)", ("oklch(0.7 0.15 250)",))


# Carried from test_frontend_gate.py when the colour tests were collected here.
def test_relative_luminance_orders_black_grey_white() -> None:
    """Luminance must be monotonic between black and white (anchors: see above)."""
    black = _relative_luminance((0.0, 0.0, 0.0))
    grey = _relative_luminance((128.0, 128.0, 128.0))
    white = _relative_luminance((255.0, 255.0, 255.0))
    assert black < grey < white


# --- Segmented-control contrast gate (UI round 2 backlog, T1) ---------------

LIGHT_TRACK = (240.0, 235.0, 224.0)
DARK_TRACK = (24.0, 21.0, 32.0)


def _rgb(level: int) -> str:
    return f"rgb({level}, {level}, {level})"


def _grey_beside(background: tuple[float, float, float], floor: float, passes: bool):
    """Return the grey nearest *floor* on the passing or the failing side."""
    levels = [
        (_contrast_ratio((level, level, level), background), level)
        for level in range(256)
    ]
    if passes:
        ratio, level = min(pair for pair in levels if pair[0] >= floor)
    else:
        ratio, level = max(pair for pair in levels if pair[0] < floor)
    return _rgb(level), ratio


class _SegPage:
    """A page whose paint depends on the theme the gate last set."""

    def __init__(self, paints: dict[str, dict]) -> None:
        self.paints = paints
        self.theme = "light"

    def evaluate(self, script, arg=None):
        if script is _frontend_gate_colour.SEG_PAINT_JS:
            return self.paints[self.theme]
        if arg in ("light", "dark"):
            self.theme = arg
        elif "'light'" in script:
            self.theme = "light"
        return None


def _paints(
    light_border: str, dark_border: str, selected_text: str = "rgb(0, 0, 0)"
) -> dict[str, dict]:
    def paint(track, text, border, selected):
        return {
            "track": track,
            "unselectedText": text,
            "selectedText": selected,
            "chip": "rgba(0, 0, 0, 0)",
            "chipBorder": border,
        }

    return {
        "light": paint(
            "rgb(240, 235, 224)", "rgb(0, 0, 0)", light_border, selected_text
        ),
        "dark": paint(
            "rgb(24, 21, 32)", "rgb(255, 255, 255)", dark_border, "rgb(255, 255, 255)"
        ),
    }


def _seg_failures(monkeypatch, paints: dict[str, dict]) -> list[str]:
    monkeypatch.setattr(_frontend_gate_colour, "wait_for_settled", lambda *a, **k: None)
    spec = {"track": ".t", "selected": ".s", "unselected": ".u"}
    return _frontend_gate_colour.seg_contrast_failures(
        _SegPage(paints), "Test control", spec
    )


@pytest.mark.parametrize(
    ("failing", "probe_floor", "probe_passes"),
    [
        # Just under 4.5:1 in one theme: only that theme fails.
        (("light",), 4.5, False),
        (("dark",), 4.5, False),
        # A 3.5:1 boundary clears the old 3:1 floor but not 4.5:1, in both.
        (("light", "dark"), 3.5, True),
    ],
)
def test_seg_boundary_under_4_5_fails_in_the_themes_that_miss_it(
    monkeypatch, failing, probe_floor, probe_passes
) -> None:
    tracks = {"light": LIGHT_TRACK, "dark": DARK_TRACK}
    borders = {}
    ratios = {}
    for theme, track in tracks.items():
        if theme in failing:
            borders[theme], ratios[theme] = _grey_beside(
                track, probe_floor, passes=probe_passes
            )
        else:
            borders[theme] = _grey_beside(track, 4.5, passes=True)[0]
    failures = _seg_failures(monkeypatch, _paints(borders["light"], borders["dark"]))
    assert len(failures) == len(failing)
    assert all(
        f"{theme} theme" in line
        and "chip boundary on track" in line
        and f"{ratios[theme]:.2f}:1" in line
        and "under 4.5:1" in line
        for theme, line in zip(failing, failures, strict=True)
    )


def test_selected_text_floor_stays_4_5(monkeypatch) -> None:
    good = _grey_beside(LIGHT_TRACK, 4.5, passes=True)[0]
    border, _ = _grey_beside(LIGHT_TRACK, 4.5, passes=True)
    dark_border, _ = _grey_beside(DARK_TRACK, 4.5, passes=True)
    assert _seg_failures(monkeypatch, _paints(border, dark_border, good)) == []
    low, ratio = _grey_beside(LIGHT_TRACK, 4.5, passes=False)
    failures = _seg_failures(monkeypatch, _paints(border, dark_border, low))
    assert len(failures) == 1
    assert "selected text on chip" in failures[0]
    assert f"{ratio:.2f}:1" in failures[0]


def _ok_paints() -> dict[str, dict]:
    light, _ = _grey_beside(LIGHT_TRACK, 4.5, passes=True)
    dark, _ = _grey_beside(DARK_TRACK, 4.5, passes=True)
    return _paints(light, dark)


def test_missing_control_is_reported_in_both_themes(monkeypatch) -> None:
    failures = _seg_failures(monkeypatch, {"light": None, "dark": None})
    assert len(failures) == 2
    assert all("Test control" in line for line in failures)
    assert all("the control is missing" in line for line in failures)


def test_translucent_chip_border_is_composited_over_the_track(monkeypatch) -> None:
    # Opaque black and white clear 4.5:1 alone; at 30% alpha over the track
    # they composite to a pale tint well under it.
    paints = _ok_paints()
    paints["light"]["chipBorder"] = "rgba(0, 0, 0, 0.3)"
    paints["dark"]["chipBorder"] = "rgba(255, 255, 255, 0.3)"
    failures = _seg_failures(monkeypatch, paints)
    assert len(failures) == 2
    assert all("chip boundary on track" in line for line in failures)


# --- unselected_floor spec key (UI round 2 backlog, T8, RA1) -----------------


def _muted_paints(cell: str = "unselectedText") -> dict[str, dict]:
    """*cell* at about 5:1 on the track in both themes; the rest passes."""
    paints = _ok_paints()
    paints["light"][cell] = _grey_beside(LIGHT_TRACK, 5.0, passes=True)[0]
    paints["dark"][cell] = _grey_beside(DARK_TRACK, 5.0, passes=True)[0]
    return paints


def _spec_failures(monkeypatch, paints: dict, **extra) -> list[str]:
    monkeypatch.setattr(_frontend_gate_colour, "wait_for_settled", lambda *a, **k: None)
    spec = {"track": ".t", "selected": ".s", "unselected": ".u", **extra}
    return _frontend_gate_colour.seg_contrast_failures(
        _SegPage(paints), "Test control", spec
    )


@pytest.mark.parametrize(
    ("cell", "extra", "expected_failures"),
    [
        # Unselected text keeps the 7:1 floor unless the spec lowers it.
        ("unselectedText", {}, 2),
        ("unselectedText", {"unselected_floor": 4.5}, 0),
        # Selected text is held to 4.5:1 whatever the unselected floor.
        ("selectedText", {}, 0),
    ],
)
def test_unselected_text_floor_is_7_to_1_by_default_and_selected_text_keeps_4_5(
    monkeypatch, cell, extra, expected_failures
) -> None:
    failures = _spec_failures(monkeypatch, _muted_paints(cell), **extra)
    assert len(failures) == expected_failures
    assert all("option text on track" in line for line in failures)
    assert all("under 7.0:1" in line for line in failures)


def test_unselected_floor_does_not_lower_the_other_cells(monkeypatch) -> None:
    paints = _muted_paints()
    low, _ = _grey_beside(LIGHT_TRACK, 4.5, passes=False)
    paints["light"]["unselectedText"] = low
    paints["light"]["selectedText"] = low
    paints["light"]["chipBorder"] = low
    failures = _spec_failures(monkeypatch, paints, unselected_floor=4.5)
    cells = sorted(line.split(": ")[1].split(" is ")[0] for line in failures)
    assert cells == [
        "chip boundary on track",
        "option text on track",
        "selected text on chip",
    ]
    assert all("under 4.5:1" in line for line in failures)


class _HoverPage:
    """A page whose hover reads the same per-theme ink for each option."""

    def __init__(self, ink: dict[str, dict[str, str]]) -> None:
        self.ink = ink
        self.theme = "light"
        self.mouse = self

    def move(self, *_args) -> None:
        pass

    def locator(self, selector):
        class _Node:
            def hover(self) -> None:
                pass

        return _Node()

    def evaluate(self, script, arg=None):
        if script is _frontend_gate_colour.SEG_PAINT_JS:
            ink = self.ink[self.theme]
            track = "rgb(240, 235, 224)" if self.theme == "light" else "rgb(24, 21, 32)"
            return {
                "track": track,
                "unselectedText": ink["unselected"],
                "selectedText": ink["selected"],
                "chip": "rgba(0, 0, 0, 0)",
                "chipBorder": "rgb(0, 0, 0)",
            }
        if arg in ("light", "dark"):
            self.theme = arg
        elif "'light'" in script:
            self.theme = "light"
        return None


def _hover_failures(
    monkeypatch, selected_ratio=None, unselected_ratio=5.0, **extra
) -> list[str]:
    """Hover failures for unselected ink at *unselected_ratio* (5:1 default).

    Without *selected_ratio* the selected ink is full black or white.
    """
    monkeypatch.setattr(_frontend_gate_colour, "wait_for_settled", lambda *a, **k: None)
    five_light = _grey_beside(LIGHT_TRACK, unselected_ratio, passes=True)[0]
    five_dark = _grey_beside(DARK_TRACK, unselected_ratio, passes=True)[0]
    selected_light, selected_dark = "rgb(0, 0, 0)", "rgb(255, 255, 255)"
    if selected_ratio is not None:
        passes = selected_ratio >= 4.5
        selected_light = _grey_beside(LIGHT_TRACK, selected_ratio, passes=passes)[0]
        selected_dark = _grey_beside(DARK_TRACK, selected_ratio, passes=passes)[0]
    page = _HoverPage(
        {
            "light": {"unselected": five_light, "selected": selected_light},
            "dark": {"unselected": five_dark, "selected": selected_dark},
        }
    )
    spec = {"track": ".t", "selected": ".s", "unselected": ".u", **extra}
    return _frontend_gate_colour.seg_hover_failures(page, "Test control", spec)


def test_unselected_floor_4_5_accepts_hover_text_the_default_rejects(
    monkeypatch,
) -> None:
    default = _hover_failures(monkeypatch)
    assert len(default) == 2
    assert all("hovered unselected option text on track" in line for line in default)
    assert all("under 7.0:1" in line for line in default)
    assert _hover_failures(monkeypatch, unselected_floor=4.5) == []


def test_hovered_selected_chip_text_under_4_5_is_named(monkeypatch) -> None:
    failures = _hover_failures(monkeypatch, selected_ratio=4.0, unselected_floor=4.5)
    assert len(failures) == 2
    assert all("hovered selected chip text on chip" in line for line in failures)
    assert all("under 4.5:1" in line for line in failures)


def test_unselected_floor_does_not_lower_the_selected_chip_hover_floor(
    monkeypatch,
) -> None:
    # 5:1 clears the chip's own 4.5:1 floor but not the 7:1 default for the
    # unselected text: with the default floor in force and unselected ink at
    # 8:1, the chip must not inherit the unselected floor.
    failures = _hover_failures(monkeypatch, selected_ratio=5.0, unselected_ratio=8.0)
    assert failures == []
