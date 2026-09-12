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

from scripts.dev import frontend_gate
from scripts.dev._frontend_gate_colour import (
    _clamp_px,
    _composite_over,
    _contrast_ratio,
    _divider_contrast_failure,
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
        assert callable(getattr(frontend_gate, name))
