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


class _ClockPage:
    """A page stand-in whose only clock is the sum of its waits (milliseconds)."""

    def __init__(self, sink: list, arrives_at_ms: int | None) -> None:
        self.sink = sink
        self.arrives_at_ms = arrives_at_ms
        self.now = 0

    def wait_for_timeout(self, ms: int) -> None:
        self.now += ms
        if self.arrives_at_ms is not None and self.now >= self.arrives_at_ms:
            self.sink.append("route")
            self.arrives_at_ms = None


def test_wait_for_held_outlasts_a_slow_debounce_the_old_400ms_sleep_missed() -> None:
    # A request landing at 1.2 s (a loaded machine) used to be counted as
    # "held 0" after a fixed 400 ms sleep.
    sink: list = []
    page = _ClockPage(sink, arrives_at_ms=1200)

    _frontend_gate_forms._wait_for_held(page, sink, 1)

    assert sink == ["route"]


def test_wait_for_held_gives_up_at_its_bound_when_nothing_arrives() -> None:
    sink: list = []
    page = _ClockPage(sink, arrives_at_ms=None)

    _frontend_gate_forms._wait_for_held(page, sink, 1)

    assert sink == []
    assert page.now == (
        _frontend_gate_forms.REQUEST_WAIT_MS + _frontend_gate_forms.NOTHING_MORE_MS
    )


def test_wait_for_held_settles_so_a_surplus_request_is_counted() -> None:
    # The check compares the exact count, so a second request arriving just
    # after the first must still be in the sink when the wait returns.
    sink: list = ["route"]
    page = _ClockPage(sink, arrives_at_ms=100)

    _frontend_gate_forms._wait_for_held(page, sink, 1)

    assert sink == ["route", "route"]
