"""Parity and behaviour tests for the assets slice of the frontend gate."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.dev import _frontend_gate_assets, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

MOVED = (
    "BOOTSTRAP_MARKER",
    "TAILWIND_MARKER",
    "_stylesheet_hrefs",
    "check_stylesheet_isolation",
)
REEXPORTED = ("BOOTSTRAP_MARKER", "TAILWIND_MARKER", "check_stylesheet_isolation")


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_assets)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_assets, name)


def _page_with(hrefs: list[str]) -> MagicMock:
    page = MagicMock()
    page.eval_on_selector_all.return_value = hrefs
    return page


@pytest.mark.parametrize(
    ("hrefs", "count"),
    [
        ([], 0),
        (
            [
                "/static/css/tailwind.css",
                "https://cdnjs.cloudflare.com/x/bootstrap.min.css",
            ],
            2,
        ),
    ],
)
def test_isolation_fails_unless_exactly_one_framework_sheet(hrefs, count) -> None:
    with patch("scripts.dev._frontend_gate_assets.ALL_PAGES", ["/"]):
        failures = _frontend_gate_assets.check_stylesheet_isolation(
            _page_with(hrefs), "http://127.0.0.1:0"
        )
    assert failures == [
        f"/ loads {count} framework stylesheets, expected exactly 1: {hrefs}"
    ]


def test_isolation_passes_one_tailwind_sheet_beside_other_css() -> None:
    hrefs = ["/static/css/tailwind.css", "https://use.typekit.net/rwy8ghw.css"]
    with patch("scripts.dev._frontend_gate_assets.ALL_PAGES", ["/"]):
        assert (
            _frontend_gate_assets.check_stylesheet_isolation(
                _page_with(hrefs), "http://127.0.0.1:0"
            )
            == []
        )
