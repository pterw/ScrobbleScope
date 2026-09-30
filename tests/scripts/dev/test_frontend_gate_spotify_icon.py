"""Parity and behaviour tests for the Spotify-icon slice of the frontend gate
(F-B21-60 part 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.dev import _frontend_gate_spotify_icon, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

REPO_ROOT = Path(__file__).resolve().parents[3]
CHECK_NAME = "spotlight spotify icon size and link target"
CHECK = "check_spotlight_spotify_icon_size_and_link_target"


class _ThemedPage:
    """A page stand-in: remembers the theme the helper sets and answers the
    icon probe with the report given for that theme."""

    def __init__(self, reports, load_times_out=()):
        self.reports = reports
        self.load_times_out = load_times_out
        self.theme = None
        self.calls = []

    def wait_for_function(self, expression, arg=None, timeout=None):
        self.calls.append(("wait", self.theme, arg, timeout))
        if self.theme in self.load_times_out:
            raise TimeoutError("icon never loaded")

    def evaluate(self, expression, argument=None):
        if "setAttribute('data-theme'" in expression:
            self.theme = argument
            self.calls.append(("theme", argument))
            return None
        if "pathname)" in expression and "map(" in expression:
            return [self.reports[self.theme]["src"]]
        self.calls.append(("probe", self.theme))
        return dict(self.reports[self.theme])


def _report(theme, **overrides):
    """A report the helper accepts, for `theme`, with `overrides` applied."""
    report = {
        "missing": False,
        "shown": 1,
        "width": 25.1,
        "height": 24.0,
        "src": _frontend_gate_spotify_icon.ICON_FILE_FOR_THEME[theme],
        "loaded": True,
        "nearest": {"gap": 12.0, "name": "neighbour"},
    }
    report.update(overrides)
    return report


def _failures(light=None, dark=None):
    page = _ThemedPage(
        {"light": light or _report("light"), "dark": dark or _report("dark")}
    )
    return _frontend_gate_spotify_icon.spotify_icon_failures(
        page, "#icon-holder", "icon", clear_scope="#scope"
    )


def test_the_slice_defines_the_check_and_helper() -> None:
    names = defined_names(_frontend_gate_spotify_icon)
    assert {CHECK, "spotify_icon_failures", "ICON_FILE_FOR_THEME"} <= names
    assert CHECK not in defined_names(frontend_gate)


def test_the_check_resolves_through_the_gate_module_and_is_registered() -> None:
    assert getattr(frontend_gate, CHECK) is getattr(_frontend_gate_spotify_icon, CHECK)
    entry = next(entry for entry in frontend_gate.CHECKS if entry[0] == CHECK_NAME)
    assert entry[1] is getattr(_frontend_gate_spotify_icon, CHECK)
    assert set(entry[2]) == {frontend_gate.DESKTOP, frontend_gate.MOBILE}


def test_each_theme_expects_the_official_monochrome_file() -> None:
    files = _frontend_gate_spotify_icon.ICON_FILE_FOR_THEME
    assert files["light"].endswith("/Primary_Logo_Black_RGB.svg")
    assert files["dark"].endswith("/Primary_Logo_White_RGB.svg")
    for url in files.values():
        assert (REPO_ROOT / url.lstrip("/")).is_file(), url


def test_a_compliant_icon_passes_in_both_themes() -> None:
    assert _failures() == []


def test_an_icon_below_21px_fails() -> None:
    failures = _failures(light=_report("light", width=21.0, height=20.0))
    assert failures == [
        "icon [light]: Spotify icon renders 21.0x20.0px, below the 21px minimum"
    ]


def test_the_wrong_file_for_the_theme_fails() -> None:
    wrong = _frontend_gate_spotify_icon.ICON_FILE_FOR_THEME["light"]
    failures = _failures(dark=_report("dark", src=wrong))
    assert len(failures) == 1
    assert failures[0].startswith("icon [dark]: Spotify icon shows")


def test_an_unloaded_file_fails() -> None:
    failures = _failures(light=_report("light", loaded=False))
    assert len(failures) == 1
    assert "did not load" in failures[0]


def test_a_neighbour_inside_half_the_icon_height_fails() -> None:
    failures = _failures(
        light=_report("light", nearest={"gap": 11.0, "name": "artist-name"})
    )
    assert failures == [
        "icon [light]: 'artist-name' is 11.0px from the Spotify icon, "
        "inside its 12.0px clear space"
    ]


def test_no_file_or_two_files_displayed_fails() -> None:
    failures = _failures(light=_report("light", shown=0), dark=_report("dark", shown=2))
    assert failures == [
        "icon [light]: 0 Spotify icon files are displayed, expected 1",
        "icon [dark]: 2 Spotify icon files are displayed, expected 1",
    ]


@pytest.mark.parametrize("theme", ("light", "dark"))
def test_a_missing_container_fails_once(theme: str) -> None:
    reports = {"light": _report("light"), "dark": _report("dark")}
    reports[theme] = {"missing": True}
    page = _ThemedPage(reports)
    failures = _frontend_gate_spotify_icon.spotify_icon_failures(
        page, "#icon-holder", "icon"
    )
    assert failures == [
        f"icon [{theme}]: no #icon-holder element to hold the Spotify icon"
    ]


def test_each_theme_waits_for_its_icon_to_load_before_it_is_judged() -> None:
    page = _ThemedPage({"light": _report("light"), "dark": _report("dark")})
    assert (
        _frontend_gate_spotify_icon.spotify_icon_failures(page, "#icon-holder", "icon")
        == []
    )
    timeout = _frontend_gate_spotify_icon.ICON_LOAD_TIMEOUT_MS
    assert page.calls == [
        ("theme", "light"),
        ("wait", "light", "#icon-holder", timeout),
        ("probe", "light"),
        ("theme", "dark"),
        ("wait", "dark", "#icon-holder", timeout),
        ("probe", "dark"),
    ]


def test_an_icon_that_never_loads_is_reported_by_name_and_not_judged() -> None:
    page = _ThemedPage(
        {"light": _report("light"), "dark": _report("dark")},
        load_times_out=("dark",),
    )
    failures = _frontend_gate_spotify_icon.spotify_icon_failures(
        page, "#icon-holder", "icon"
    )
    assert failures == [
        "icon [dark]: Spotify icon file "
        "['/static/images/brand/spotify/Primary_Logo_White_RGB.svg'] "
        "did not load within 5000ms"
    ]
    assert ("probe", "dark") not in page.calls
    assert ("probe", "light") in page.calls


def test_the_load_wait_reads_naturalwidth_not_complete_alone() -> None:
    script = _frontend_gate_spotify_icon._ICON_LOADED_JS
    assert "img.complete && img.naturalWidth > 0" in script
    assert "display !== 'none'" in script
