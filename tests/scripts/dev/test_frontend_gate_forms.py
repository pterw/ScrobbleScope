"""Parity and behaviour tests for the forms slice of the frontend gate."""

from __future__ import annotations

import inspect
import re
from html.parser import HTMLParser
from unittest.mock import MagicMock

import pytest

from scripts.dev import _frontend_gate_colour, _frontend_gate_forms


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


# --- Mode switch gate (UI round 2 backlog, T8, RA1) --------------------------


def _count_matches(html: str, selector: str) -> int:
    """Count elements a `.a.b` / `:not(.c)` class selector matches in *html*."""
    forbidden = re.findall(r":not\(\.([\w-]+)\)", selector)
    required = re.findall(r"\.([\w-]+)", re.sub(r":not\(\.[\w-]+\)", "", selector))

    class Counter(HTMLParser):
        count = 0

        def handle_starttag(self, tag, attrs):
            classes = dict(attrs).get("class", "").split()
            if all(c in classes for c in required) and not any(
                c in classes for c in forbidden
            ):
                self.count += 1

    counter = Counter()
    counter.feed(html)
    return counter.count


@pytest.mark.parametrize(
    ("key", "expected"),
    [("track", 1), ("selected", 1), ("unselected", 1)],
)
def test_mode_switch_selectors_match_the_nodes_the_index_template_renders(
    client, key: str, expected: int
) -> None:
    html = client.get("/").get_data(as_text=True)
    selector = _frontend_gate_forms.MODE_SWITCH_SEG[key]
    assert _count_matches(html, selector) == expected


class _ModePage:
    """A stub index page: clicking a tab moves the selected chip."""

    def __init__(
        self,
        border_by_selected: dict[str, str],
        light_ink: str = "rgb(0, 0, 0)",
    ) -> None:
        self.border_by_selected = border_by_selected
        self.light_ink = light_ink
        self.selected = "album"
        self.theme = "light"
        self.clicks: list[str] = []
        self.mouse = self

    def move(self, *_args) -> None:
        pass

    def locator(self, selector):
        page = self

        class _Node:
            def click(self) -> None:
                page.clicks.append(selector)
                page.selected = "heatmap" if "heatmap" in selector else "album"

            def hover(self) -> None:
                pass

        return _Node()

    def evaluate(self, script, arg=None):
        if script is _frontend_gate_colour.SEG_PAINT_JS:
            dark = self.theme == "dark"
            return {
                "track": "rgb(24, 21, 32)" if dark else "rgb(240, 235, 224)",
                "unselectedText": "rgb(255, 255, 255)" if dark else self.light_ink,
                "selectedText": "rgb(255, 255, 255)" if dark else "rgb(0, 0, 0)",
                "chip": "rgba(0, 0, 0, 0)",
                "chipBorder": self.border_by_selected[self.selected],
            }
        if arg in ("light", "dark"):
            self.theme = arg
        elif "'light'" in script:
            self.theme = "light"
        return None


def test_mode_switch_failures_name_the_state_whose_outline_is_under_4_5(
    monkeypatch,
) -> None:
    monkeypatch.setattr(_frontend_gate_colour, "wait_for_settled", lambda *a, **k: None)
    # A transparent outline is invisible on both tracks; mid grey is about 3:1
    # on the light track.
    page = _ModePage({"album": "rgba(0, 0, 0, 0)", "heatmap": "rgb(128, 128, 128)"})
    failures = _frontend_gate_forms.mode_switch_failures(page)
    assert failures
    assert all("under 4.5:1" in line for line in failures)
    assert any("Mode switch (Top albums selected)" in line for line in failures)
    assert any("Mode switch (Heatmap selected)" in line for line in failures)


def test_mode_switch_failures_restore_top_albums_and_keep_light_clear(
    monkeypatch,
) -> None:
    monkeypatch.setattr(_frontend_gate_colour, "wait_for_settled", lambda *a, **k: None)
    page = _ModePage({"album": "rgb(0, 0, 0)", "heatmap": "rgb(0, 0, 0)"})
    # Black clears 4.5:1 on the light track but not on the dark one.
    failures = _frontend_gate_forms.mode_switch_failures(page)
    assert failures
    assert all("dark theme" in line for line in failures)
    assert not any("light theme" in line for line in failures)
    assert page.clicks == ["#mode-tab-heatmap", "#mode-tab-album"]
    assert page.selected == "album"


def test_mode_switch_failures_include_the_hover_measure(monkeypatch) -> None:
    monkeypatch.setattr(_frontend_gate_colour, "wait_for_settled", lambda *a, **k: None)
    # Mid grey is about 3:1 on the light track: under the 4.5:1 hover floor.
    page = _ModePage(
        {"album": "rgb(0, 0, 0)", "heatmap": "rgb(0, 0, 0)"},
        light_ink="rgb(128, 128, 128)",
    )
    failures = _frontend_gate_forms.mode_switch_failures(page)
    hovered = [line for line in failures if "hovered" in line]
    assert any("Top albums selected), light theme: hovered" in x for x in hovered)
    assert any("Heatmap selected), light theme: hovered" in x for x in hovered)
    assert all("under 4.5:1" in line for line in hovered)


def test_mode_switch_failures_restore_top_albums_when_a_measure_raises(
    monkeypatch,
) -> None:
    def explode(page, label, spec):
        if "Heatmap" in label:
            raise RuntimeError("measure failed")
        return []

    monkeypatch.setattr(_frontend_gate_forms, "seg_contrast_failures", explode)
    monkeypatch.setattr(_frontend_gate_colour, "wait_for_settled", lambda *a, **k: None)
    page = _ModePage({"album": "rgb(0, 0, 0)", "heatmap": "rgb(0, 0, 0)"})
    with pytest.raises(RuntimeError, match="measure failed"):
        _frontend_gate_forms.mode_switch_failures(page)
    assert page.selected == "album"


def test_include_check_reports_what_the_mode_switch_measure_finds(
    monkeypatch,
) -> None:
    failure = "/ Mode switch (stub): chip boundary on track is under 4.5:1"
    monkeypatch.setattr(
        _frontend_gate_forms, "mode_switch_failures", lambda page: [failure]
    )
    monkeypatch.setattr(_frontend_gate_forms, "seg_contrast_failures", lambda *a: [])
    monkeypatch.setattr(_frontend_gate_forms, "seg_hover_failures", lambda *a: [])
    monkeypatch.setattr(
        _frontend_gate_forms, "_unmatched_help_contrast_failures", lambda page: []
    )
    failures = _frontend_gate_forms.check_include_unmatched_control(
        MagicMock(), "http://x"
    )
    assert failure in failures
