"""Colour maths and segmented-control colour checks for the frontend gate.

F-B21-51 records that `frontend_gate.py` has grown to roughly ten times its
largest sibling and prescribes a split along the check groups. This module is
the first, safest slice of that split: the helpers here take numbers and
strings, never a `page`, so they carry no browser or fixture dependency and can
be pinned by plain pytest. The segmented-control checks (`seg_*`) at the end
are the exception: they drive a `page` and wait with `wait_for_settled`.

That property is the point. A split of a 4,000-line module is verified by the
browser gate, and the browser gate is the thing being moved, so the parts that
can be proved without a browser should move first and be covered first. The
names keep their leading underscore and are re-exported from `frontend_gate`
so any caller or future test that imports them from the gate keeps working.

Source of the maths: WCAG 2.x relative-luminance and contrast-ratio
definitions, and CSS `clamp()` resolution semantics.
"""

from __future__ import annotations

import re

from scripts.dev._frontend_gate_shared import wait_for_settled

__all__ = [
    "_clamp_px",
    "_composite_over",
    "_contrast_ratio",
    "_divider_contrast_failure",
    "_is_forbidden_surface",
    "_parse_rgb_string",
    "_relative_luminance",
    "_worst_divider_contrast",
    "seg_contrast_cells",
    "seg_contrast_failures",
    "seg_hover_failures",
]

#: The computed-colour serializations this module can read.
#:
#: Measured in both engines the gate runs, 2026-09-20: every design token the
#: gate reads comes back as `rgb()` or `rgba()`, except a `color-mix()`, which
#: both engines serialize as `color(srgb r g b)` with channels in 0-1 rather
#: than 0-255. Anything else -- `oklch()`, `lab()`, `hsl()`, or `color()` in a
#: wider gamut -- also leads with three numbers, and reading those as sRGB
#: channels yields a plausible ratio for a colour nobody painted.
_RGB_FUNCTION_RE = re.compile(r"^rgba?\(", re.IGNORECASE)
_COLOR_SRGB_RE = re.compile(r"^color\(\s*srgb\s", re.IGNORECASE)


def _parse_rgb_string(value: str) -> tuple[float, float, float, float]:
    """Parse a computed colour string into an (r, g, b, a) tuple of 0-255 channels.

    Handles ``rgb()``/``rgba()`` and the ``color(srgb r g b / a)`` form, which
    is how a browser serializes a computed ``color-mix()``. That form states
    its channels in 0-1, and reading them as 0-255 collapses any such colour
    to near black -- the results table's own surface is a ``color-mix()``, so
    a contrast measurement against it reported 1.19:1 for ink that plainly
    reads against it.
    """
    text = value.strip()
    if _COLOR_SRGB_RE.match(text):
        scale = 255.0
    elif _RGB_FUNCTION_RE.match(text):
        scale = 1.0
    else:
        raise ValueError(
            f"unsupported colour serialization {value!r}: this module reads "
            "rgb(), rgba() and color(srgb ...) only. Teach it the new form "
            "rather than letting a contrast measurement guess at one."
        )
    numbers = [float(part) for part in re.findall(r"[\d.]+", text)]
    red, green, blue = (number * scale for number in numbers[:3])
    alpha = numbers[3] if len(numbers) > 3 else 1.0
    return red, green, blue, alpha


def _is_forbidden_surface(value: str, forbidden: tuple[str, ...]) -> bool:
    """Return True when *value* paints one of the *forbidden* colours.

    Compares colours, not strings. The same colour has more than one
    serialization -- a cool grey arriving through a `color-mix()` reads as
    `color(srgb 0.97 0.98 0.98)`, and a string comparison against
    `rgb(248, 249, 250)` would miss it while the surface was on screen.

    This runs over every element on a page, so it cannot raise: a
    serialization the parser refuses falls back to an exact string match and
    the scan continues. That is the right trade here and the wrong one for a
    measurement, which is why the parser itself still refuses.
    """

    def channels(colour: str) -> tuple[int, int, int, float] | None:
        try:
            red, green, blue, alpha = _parse_rgb_string(colour)
        except (ValueError, IndexError):
            return None
        return round(red), round(green), round(blue), round(alpha, 3)

    measured = channels(value)
    for candidate in forbidden:
        if value == candidate:
            return True
        expected = channels(candidate)
        if measured is not None and expected is not None and measured == expected:
            return True
    return False


def _composite_over(
    foreground: tuple[float, float, float, float],
    background: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Alpha-composite a translucent foreground colour over an opaque one."""
    fg_red, fg_green, fg_blue, alpha = foreground
    bg_red, bg_green, bg_blue = background
    return (
        fg_red * alpha + bg_red * (1 - alpha),
        fg_green * alpha + bg_green * (1 - alpha),
        fg_blue * alpha + bg_blue * (1 - alpha),
    )


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG relative luminance of an sRGB colour given as 0-255 channels."""

    def channel(value: float) -> float:
        normalised = value / 255
        if normalised <= 0.03928:
            return normalised / 12.92
        return ((normalised + 0.055) / 1.055) ** 2.4

    red, green, blue = rgb
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast_ratio(
    rgb_a: tuple[float, float, float], rgb_b: tuple[float, float, float]
) -> float:
    """WCAG contrast ratio between two opaque sRGB colours."""
    luminance_a = _relative_luminance(rgb_a) + 0.05
    luminance_b = _relative_luminance(rgb_b) + 0.05
    return max(luminance_a, luminance_b) / min(luminance_a, luminance_b)


def _clamp_px(
    min_rem: float,
    vw_percent: float,
    max_rem: float,
    width_px: float,
    root_px: float = 16,
) -> float:
    """Mirror a CSS ``clamp(<min_rem>rem, <vw_percent>vw, <max_rem>rem)``.

    ``vw`` is a percentage of the viewport width in CSS pixels; it never
    scales with the root font size, only the rem bounds do. Python has to
    keep those two independent to reproduce the browser's resolved value.
    """
    preferred = vw_percent * width_px / 100
    return min(max_rem * root_px, max(min_rem * root_px, preferred))


def _worst_divider_contrast(border: str, *surfaces: str) -> float:
    """The lowest contrast a translucent divider reaches against its surfaces.

    A divider is painted over whatever sits beside it, not over one known
    background, so an alpha that clears 3:1 against one surface can still
    fail against another. Compositing every candidate surface and keeping
    the minimum is what "adjacent surface" has to mean for a token shared
    across the header and the rest of the shell.
    """
    border_rgba = _parse_rgb_string(border)
    ratios = []
    for surface in surfaces:
        surface_rgb = _parse_rgb_string(surface)[:3]
        composited = _composite_over(border_rgba, surface_rgb)
        ratios.append(_contrast_ratio(composited, surface_rgb))
    return min(ratios)


def _divider_contrast_failure(
    label: str, ratio: float, token: str = "--shell-border"
) -> str | None:
    """Name a divider-contrast failure, or None once the ratio clears 3:1.

    ``token`` names which custom property the message blames. F-B21-40 made
    this a parameter rather than a literal: the same helper now checks both
    the shared ``--shell-border`` and the index page's own
    ``--ss-border-divider``, and a message that always said "--shell-border"
    would misattribute a failing index divider to the wrong token.
    """
    if ratio >= 3.0:
        return None
    return (
        f"/ {label}: {token} composites to {ratio:.2f}:1 against its "
        "adjacent surface, expected at least 3:1"
    )


#: The owner's ruling: 4.5 is a floor, not a goal. Option text aims for 7:1
#: (AAA); the selected chip's boundary is a non-text boundary, held at 4.5:1
#: (RA2, one stronger outline: the token clears 4.5:1 on every surface).
SEG_TEXT_FLOOR = 7.0
SEG_BOUNDARY_FLOOR = 4.5

#: The selected option's text is the primary on its soft chip, 5.47:1 light and
#: 6.38:1 dark: an owner exception to the 7:1 aim (2026-10-25, UI round 2
#: backlog: "Keep primary, lower the gate"), held at the 4.5:1 AA floor. The
#: chip's 1px outline at 4.5:1 carries the selected state.
SEG_SELECTED_TEXT_FLOOR = 4.5

#: Takes {track, selected, unselected} selectors; returns the painted colours.
SEG_PAINT_JS = """spec => {
    const track = document.querySelector(spec.track);
    const selected = document.querySelector(spec.selected);
    const unselected = document.querySelector(spec.unselected);
    if (!track || !selected || !unselected) return null;
    const paint = node => getComputedStyle(node);
    return {
        track: paint(track).backgroundColor,
        unselectedText: paint(unselected).color,
        selectedText: paint(selected).color,
        chip: paint(selected).backgroundColor,
        chipBorder: paint(selected).borderTopColor,
    };
}"""


def seg_contrast_cells(page, spec: dict) -> dict | None:
    """Measure one segmented control in the current theme, or None if absent.

    The cells are option text on its track, the selected text on its chip and
    the chip's boundary against the track. A transparent colour is composited
    over the track, so the chip fill is read as painted.
    """
    paint = page.evaluate(SEG_PAINT_JS, spec)
    if paint is None:
        return None
    track = _parse_rgb_string(paint["track"])[:3]

    def over_track(value: str) -> tuple[float, float, float]:
        return _composite_over(_parse_rgb_string(value), track)

    chip = over_track(paint["chip"])
    return {
        "option text on track": _contrast_ratio(
            _parse_rgb_string(paint["unselectedText"])[:3], track
        ),
        "selected text on chip": _contrast_ratio(
            _parse_rgb_string(paint["selectedText"])[:3], chip
        ),
        "chip boundary on track": _contrast_ratio(
            over_track(paint["chipBorder"]), track
        ),
    }


def seg_contrast_failures(page, label: str, spec: dict) -> list[str]:
    """Hold a segmented control at 7:1 option text and a 4.5:1 chip boundary.

    Runs in both themes and restores light. The options take a 0.2s colour
    transition, so the read waits it out.
    """
    failures = []
    try:
        for theme in ("light", "dark"):
            page.evaluate(
                "(t) => document.documentElement.setAttribute('data-theme', t)",
                theme,
            )
            wait_for_settled(page, spec["track"])
            cells = seg_contrast_cells(page, spec)
            if cells is None:
                failures.append(
                    f"/ {label}: the control is missing, nothing to measure"
                )
                continue
            floors = {
                "option text on track": SEG_TEXT_FLOOR,
                "selected text on chip": SEG_SELECTED_TEXT_FLOOR,
                "chip boundary on track": SEG_BOUNDARY_FLOOR,
            }
            for cell, ratio in cells.items():
                if ratio < floors[cell]:
                    failures.append(
                        f"/ {label}, {theme} theme: {cell} is {ratio:.2f}:1, "
                        f"under {floors[cell]}:1"
                    )
    finally:
        page.evaluate(
            "() => document.documentElement.setAttribute('data-theme', 'light')"
        )
    return failures


def seg_hover_failures(page, label: str, spec: dict) -> list[str]:
    """Hold hovered segment text: the unselected option at 7:1, then the chip.

    Hovering an unselected option deepens its ink to the base-content token,
    and the checked chip keeps its own ink on hover, held at the selected-text
    floor (SEG_SELECTED_TEXT_FLOOR). Both are measured in both
    themes against the surface each text sits on, after the colour
    transition, and the pointer is moved away and light restored.
    """
    failures = []
    try:
        for theme in ("light", "dark"):
            page.evaluate(
                "(t) => document.documentElement.setAttribute('data-theme', t)",
                theme,
            )
            for state, key, surface, floor in (
                ("unselected option", "unselected", "track", SEG_TEXT_FLOOR),
                ("selected chip", "selected", "chip", SEG_SELECTED_TEXT_FLOOR),
            ):
                page.locator(spec[key]).hover()
                wait_for_settled(page, spec[key])
                paint = page.evaluate(SEG_PAINT_JS, spec)
                if paint is None:
                    failures.append(
                        f"/ {label}: the control is missing, nothing to hover"
                    )
                    break
                track = _parse_rgb_string(paint["track"])[:3]
                ground = (
                    track
                    if surface == "track"
                    else _composite_over(_parse_rgb_string(paint["chip"]), track)
                )
                text = paint[
                    "unselectedText" if key == "unselected" else "selectedText"
                ]
                ratio = _contrast_ratio(_parse_rgb_string(text)[:3], ground)
                if ratio < floor:
                    failures.append(
                        f"/ {label}, {theme} theme: hovered {state} text on "
                        f"{surface} is {ratio:.2f}:1, under {floor}:1"
                    )
    finally:
        page.mouse.move(0, 0)
        page.evaluate(
            "() => document.documentElement.setAttribute('data-theme', 'light')"
        )
    return failures
