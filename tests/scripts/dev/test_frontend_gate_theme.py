"""Parity and behaviour tests for the theme slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev._frontend_gate_theme import (
    check_theme_persistence,
    check_theme_survives_blocked_storage,
    headline_font_failures,
)


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

    with patch("scripts.dev._frontend_gate_theme.MIGRATED_PAGES", ("/",)):
        assert check_theme_persistence(page, "http://127.0.0.1:0") == []

    assert state == {"saved": "true", "theme": "dark"}


def test_the_same_headline_family_passes_however_it_is_written() -> None:
    """Quoting and spacing are not a different font."""
    assert (
        headline_font_failures(
            '"orpheuspro", Georgia, serif', "orpheuspro,Georgia,serif"
        )
        == []
    )


def test_a_different_headline_family_is_reported_with_both_names() -> None:
    failures = headline_font_failures(
        '"instrument-serif", Georgia, serif', "orpheuspro, Georgia, serif"
    )

    assert len(failures) == 1
    assert "instrument-serif" in failures[0]
    assert "orpheuspro" in failures[0]


def test_a_different_fallback_tail_is_a_different_headline_family() -> None:
    """The whole list is compared: the same first face is not enough."""
    failures = headline_font_failures(
        '"orpheuspro", Georgia, serif', "orpheuspro, serif"
    )

    assert len(failures) == 1
    assert "Georgia" in failures[0]
    assert "orpheuspro, serif" in failures[0]


@pytest.mark.parametrize("page_family", [None, ""])
def test_a_drawn_headline_font_against_an_empty_page_family_is_reported(
    page_family: str | None,
) -> None:
    failures = headline_font_failures("orpheuspro, serif", page_family)

    assert len(failures) == 1
    assert "orpheuspro" in failures[0]


def test_single_and_double_quotes_are_the_same_headline_family() -> None:
    assert (
        headline_font_failures(
            "'orpheuspro', 'instrument-serif', serif",
            '"orpheuspro", "instrument-serif", serif',
        )
        == []
    )


@pytest.mark.parametrize(
    "drawn",
    ["600 26px degular, sans-serif", "italic bold 26px/1.2 degular, sans-serif"],
)
def test_a_canvas_font_with_style_weight_and_size_matches_on_family(
    drawn: str,
) -> None:
    """ctx.font is recorded whole; only its family list is compared."""
    assert headline_font_failures(drawn, "degular, sans-serif") == []


@pytest.mark.parametrize(
    "drawn", ["400 26px degular, sans-serif", "26px degular, sans-serif"]
)
def test_a_saved_headline_drawn_at_another_weight_is_reported(drawn: str) -> None:
    failures = headline_font_failures(drawn, "degular, sans-serif", "600")

    assert len(failures) == 1
    assert "weight 400" in failures[0]
    assert "600" in failures[0]


@pytest.mark.parametrize("drawn", [None, ""])
def test_a_saved_header_with_no_headline_font_is_reported(drawn: str | None) -> None:
    assert headline_font_failures(drawn, "orpheuspro, Georgia, serif") == [
        "saved heatmap header records no headline font"
    ]
