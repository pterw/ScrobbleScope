"""Parity and unit tests for the heatmap-access slice of the frontend gate."""

from __future__ import annotations

import pytest

from scripts.dev import _frontend_gate_heatmap_access, frontend_gate
from scripts.dev._frontend_gate_heatmap_access import _expected_cell_label
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_heatmap_cells_are_keyboard_accessible",
    "check_heatmap_document_listeners_attach_once",
)
CONSTANTS = ("HEATMAP_PATH",)
HELPERS = ("_expected_cell_label",)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS, *HELPERS))
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_heatmap_access)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", CHECKS)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    # Only the check itself is re-exported by frontend_gate.py's one-line
    # registration import; HEATMAP_PATH stays private to this slice.
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_heatmap_access, name)


def test_heatmap_path_is_the_migrated_heatmap_page() -> None:
    assert _frontend_gate_heatmap_access.HEATMAP_PATH == "/heatmap"


@pytest.mark.parametrize(
    ("iso_date", "count", "expected"),
    [
        ("2025-01-01", 5, "Wednesday 1 January 2025 -- 5 scrobbles"),
        ("2025-01-01", 1, "Wednesday 1 January 2025 -- 1 scrobble"),
        ("2025-01-01", 0, "Wednesday 1 January 2025 -- No scrobbles"),
        ("2026-03-01", 2, "Sunday 1 March 2026 -- 2 scrobbles"),
    ],
)
def test_expected_cell_label_matches_the_js_helper(
    iso_date: str, count: int, expected: str
) -> None:
    assert _expected_cell_label(iso_date, count) == expected
