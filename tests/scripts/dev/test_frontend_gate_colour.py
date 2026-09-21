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

from scripts.dev import _frontend_gate_colour, frontend_gate
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

    def test_reports_below_the_threshold(self):
        message = _divider_contrast_failure("light header", 2.5)
        assert message is not None
        assert "2.50:1" in message
        assert "3:1" in message

    def test_blames_the_token_it_was_given(self):
        message = _divider_contrast_failure(
            "index well divider", 1.2, token="--ss-border-divider"
        )
        assert message is not None
        assert "--ss-border-divider" in message
        assert "--shell-border" not in message


class TestFacadeStillReExportsTheMovedHelpers:
    """The split's real guarantee: no caller has to know it happened."""

    @pytest.mark.parametrize(
        "name",
        [
            "_clamp_px",
            "_composite_over",
            "_contrast_ratio",
            "_divider_contrast_failure",
            "_parse_rgb_string",
            "_relative_luminance",
            "_worst_divider_contrast",
        ],
    )
    def test_name_resolves_through_the_gate_module(self, name: str):
        # Identity, not callability: a facade exporting an unrelated function
        # that happens to share the name would satisfy `callable()` while
        # every caller reading the moved implementation's behaviour breaks.
        assert getattr(frontend_gate, name) is getattr(_frontend_gate_colour, name)


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
