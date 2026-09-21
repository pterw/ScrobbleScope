"""Parity and behaviour tests for the forms slice of the frontend gate."""

from __future__ import annotations

import inspect

import pytest

from scripts.dev import _frontend_gate_forms, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_validation_feedback",
    "check_private_profile_is_blocked",
    "check_validator_outage_is_recoverable",
    "check_stale_validator_failure_is_discarded",
    "check_current_validator_failure_replaces_old_verdict",
    "check_true_warning_survives",
    "check_initial_visibility",
)
MOVED = (*CHECKS, "HIDDEN_ON_LOAD", "_collecting_handler", "_year_warning")
REEXPORTED = (*CHECKS, "HIDDEN_ON_LOAD")


@pytest.mark.parametrize("name", MOVED)
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_forms)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", REEXPORTED)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_forms, name)


def test_collecting_handler_takes_exactly_one_parameter_and_appends() -> None:
    # Playwright passes (route, request) to a two-parameter handler, which
    # overwrote a defaulted `pending` list with the request object in CI.
    sink: list = []
    handler = _frontend_gate_forms._collecting_handler(sink)
    assert len(inspect.signature(handler).parameters) == 1
    handler("route-1")
    handler("route-2")
    assert sink == ["route-1", "route-2"]


def test_collecting_handlers_do_not_share_a_sink() -> None:
    first, second = [], []
    _frontend_gate_forms._collecting_handler(first)("a")
    _frontend_gate_forms._collecting_handler(second)("b")
    assert (first, second) == (["a"], ["b"])
