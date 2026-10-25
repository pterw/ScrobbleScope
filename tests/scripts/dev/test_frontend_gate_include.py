"""The Unmatched albums control's selected-border gate (UI round 2 backlog, T1).

`card_boundary_failures` holds the selected border at 4.5:1 against the
Results card in both themes. A stub page returns canned paints per theme, so
the check runs without a browser.
"""

from __future__ import annotations

import pytest

from scripts.dev import _frontend_gate_include as include
from scripts.dev._frontend_gate_colour import _contrast_ratio

LIGHT_CARD = (240.0, 235.0, 224.0)
DARK_CARD = (24.0, 21.0, 32.0)
CARDS = {"light": LIGHT_CARD, "dark": DARK_CARD}


def _rgb(level: int) -> str:
    return f"rgb({level}, {level}, {level})"


def _grey_beside(card: tuple[float, float, float], floor: float, passes: bool):
    """Return the grey nearest *floor* on the passing or the failing side."""
    levels = [
        (_contrast_ratio((level, level, level), card), level) for level in range(256)
    ]
    if passes:
        ratio, level = min(pair for pair in levels if pair[0] >= floor)
    else:
        ratio, level = max(pair for pair in levels if pair[0] < floor)
    return _rgb(level), ratio


class _CardPage:
    def __init__(self, borders: dict[str, str]) -> None:
        self.borders = borders
        self.theme = "light"

    def evaluate(self, script):
        card = CARDS[self.theme]
        chain = [f"rgb({int(card[0])}, {int(card[1])}, {int(card[2])})"]
        return {"border": self.borders[self.theme], "chain": chain}


def _failures(monkeypatch, borders: dict[str, str]) -> list[str]:
    page = _CardPage(borders)

    def set_theme(stub, theme):
        stub.theme = theme

    monkeypatch.setattr(include, "_set_theme", set_theme)
    return include.card_boundary_failures(page)


@pytest.mark.parametrize(
    ("failing", "probe_floor", "probe_passes"),
    [
        # Just under 4.5:1 in one theme: only that theme fails, the other
        # (a grey at the floor) passes.
        (("light",), 4.5, False),
        (("dark",), 4.5, False),
        # A 3.5:1 boundary clears the old 3:1 floor but not 4.5:1, in both.
        (("light", "dark"), 3.5, True),
    ],
)
def test_card_boundary_under_4_5_fails_in_the_themes_that_miss_it(
    monkeypatch, failing, probe_floor, probe_passes
) -> None:
    borders = {t: _grey_beside(CARDS[t], 4.5, passes=True)[0] for t in CARDS}
    ratios = {}
    for theme in failing:
        borders[theme], ratios[theme] = _grey_beside(
            CARDS[theme], probe_floor, passes=probe_passes
        )
    failures = _failures(monkeypatch, borders)
    assert len(failures) == len(failing)
    assert all(
        f"{theme} theme" in line
        and "against the card" in line
        and f"{ratios[theme]:.2f}:1" in line
        and "under 4.5:1" in line
        for theme, line in zip(failing, failures, strict=True)
    )


class _NoSelectedPage:
    """A page with no checked option: the paint script finds nothing."""

    def evaluate(self, script):
        return None


def test_card_boundary_with_no_selected_option_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(include, "_set_theme", lambda page, theme: None)
    failures = include.card_boundary_failures(_NoSelectedPage())
    assert len(failures) == 2
    assert all("no selected option to measure" in line for line in failures)


def test_translucent_card_border_is_composited_before_it_is_measured(
    monkeypatch,
) -> None:
    # Opaque black and white clear 4.5:1 alone; at 30% alpha over the card
    # they composite to a pale tint well under it.
    borders = {"light": "rgba(0, 0, 0, 0.3)", "dark": "rgba(255, 255, 255, 0.3)"}
    failures = _failures(monkeypatch, borders)
    assert len(failures) == 2
    assert all("under 4.5:1" in line for line in failures)
