"""Parity and behaviour tests for the theme slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_theme, frontend_gate
from scripts.dev._frontend_gate_theme import (
    check_theme_persistence,
    check_theme_survives_blocked_storage,
)
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_divider_contrast",
    "check_theme_tokens",
    "check_index_design_tokens",
    "check_theme_persistence",
    "check_index_entrance_motion",
    "check_mark_follows_theme",
    "check_theme_survives_blocked_storage",
    "check_heatmap_zero_cells_follow_theme",
    "check_heatmap_export_header_matches_page",
)
CONSTANTS = ("THEME_EXPRESSION", "SET_THEME_EXPRESSION", "FORBIDDEN_SURFACES")
MOVED = (*CHECKS, *CONSTANTS, "_computed_colour", "_BLOCK_STORAGE")
REEXPORTED = (*CHECKS, *CONSTANTS)


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_theme)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_theme, name)


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
