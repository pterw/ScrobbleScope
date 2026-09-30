"""Parity tests for the shared slice of the frontend gate (F-B21-51).

The inventories here are mutated in place by `serve_app` (the loading page is
appended for the duration of a run), so every module must hold the *same*
objects. A rebinding anywhere would leave one module checking a list the
fixture never extended.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_shared, frontend_gate
from scripts.dev._frontend_gate_runtime import _launch_browser, _load_playwright
from tests.scripts.dev.gate_parity import defined_names, gate_modules

MOVED = (
    "TOGGLE_TIMEOUT_MS",
    "ERROR_PAGE_PATH",
    "MIGRATED_PAGES",
    "GATE_JOB_IDS",
    "LEGACY_PAGES",
    "ALL_PAGES",
    "_reach_state",
)
SHARED_OBJECTS = ("MIGRATED_PAGES", "ALL_PAGES", "GATE_JOB_IDS")


@pytest.mark.parametrize("name", MOVED)
def test_the_shared_module_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_shared)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", SHARED_OBJECTS)
def test_every_module_holding_an_inventory_holds_the_same_object(name: str) -> None:
    original = getattr(_frontend_gate_shared, name)
    for module in gate_modules():
        if hasattr(module, name):
            assert getattr(module, name) is original, module.__name__


def test_reach_state_clicks_and_selects_with_the_toggle_budget() -> None:
    page = MagicMock()
    target = page.locator.return_value.first
    _frontend_gate_shared._reach_state(
        page, (("click", "#a"), ("select", "#b", "decade"))
    )
    target.click.assert_called_once_with(
        timeout=_frontend_gate_shared.TOGGLE_TIMEOUT_MS
    )
    target.select_option.assert_called_once_with(
        "decade", timeout=_frontend_gate_shared.TOGGLE_TIMEOUT_MS
    )
    assert [c.args[0] for c in page.locator.call_args_list] == ["#a", "#b"]


def test_reach_state_refuses_an_unknown_action() -> None:
    with pytest.raises(ValueError, match="unknown touch-target action 'hover'"):
        _frontend_gate_shared._reach_state(MagicMock(), (("hover", "#a"),))


@pytest.fixture(scope="module")
def settle_page() -> Iterator[object]:
    """A blank Chromium page: the wait helper runs real ``getAnimations``."""
    sync_playwright = _load_playwright()
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright, "chromium")
        page = browser.new_page()
        yield page
        browser.close()


_ANIMATED = (
    "<style>@keyframes go {{ to {{ opacity: 0.5 }} }}"
    "#box {{ animation: go {duration} linear }}</style><div id=box>x</div>"
)


@pytest.mark.browser
def test_wait_for_settled_fails_loudly_when_an_animation_never_ends(
    settle_page,
) -> None:
    settle_page.set_content(_ANIMATED.format(duration="60s"))
    with pytest.raises(RuntimeError, match=r"still animating after 300ms: go"):
        _frontend_gate_shared.wait_for_settled(settle_page, "#box", timeout_ms=300)


@pytest.mark.browser
def test_wait_for_settled_returns_once_a_short_animation_ends(settle_page) -> None:
    settle_page.set_content(_ANIMATED.format(duration="150ms"))
    _frontend_gate_shared.wait_for_settled(settle_page, "#box", timeout_ms=3000)
    assert settle_page.evaluate("() => document.getAnimations().length") == 0


@pytest.mark.browser
def test_wait_for_settled_names_a_missing_element(settle_page) -> None:
    settle_page.set_content("<div></div>")
    with pytest.raises(RuntimeError, match="'#gone' is not in the page"):
        _frontend_gate_shared.wait_for_settled(settle_page, "#gone")
