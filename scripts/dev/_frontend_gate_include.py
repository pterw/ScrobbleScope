"""The real Results page of an "Include unmatched albums" run.

A slice of the frontend gate (F-B21-51). The behaviour script tests the page's
scripts against hand-built markup, and the pytest route tests read the HTML,
but neither one paints the page. This check seeds an include job (three
matched rows with durations, two unmatched rows, one per reason) and reads the
rendered page: the two markers and the "unknown" release text at 7:1, the
Albums control's text and selected-state boundary, hiding the unmatched rows,
the Sort leaderboard hover ink, forced colours and horizontal overflow.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_colour import (
    _composite_over,
    _contrast_ratio,
    _parse_rgb_string,
    seg_contrast_failures,
    seg_hover_failures,
)
from scripts.dev._frontend_gate_shared import wait_for_settled
from scrobblescope import jobs
from scrobblescope.domain import normalize_name

#: Text on the surface it paints over: AAA, since the owner ruled that the
#: 4.5:1 floor is not a goal (2026-09-30).
INCLUDE_TEXT_FLOOR = 7.0

#: The selected option's border against the card around the control: the
#: non-text contrast floor.
INCLUDE_BOUNDARY_FLOOR = 3.0

#: The two widths the page must fit without a horizontal scrollbar.
INCLUDE_OVERFLOW_WIDTHS = (390, 1280)

_ALBUMS_SEG = {
    "track": ".seg:has(#results_albums_all)",
    "selected": "label[for=results_albums_all]",
    "unselected": "label[for=results_albums_matched]",
}

#: The Sort leaderboard buttons. Listening Time is the unselected one once
#: "Matched only" has enabled it.
_SORT_SEG = {
    "track": ".seg:has(#toggle-sort-plays)",
    "selected": "#toggle-sort-plays",
    "unselected": "#toggle-sort-playtime",
}

#: A node's ink and the backgrounds from it up to the root.
_PAINT_JS = """node => {
    const chain = [];
    for (let el = node; el; el = el.parentElement) {
        chain.push(getComputedStyle(el).backgroundColor);
    }
    return {text: getComputedStyle(node).color, chain};
}"""

#: The checked Albums option's border, and the backgrounds above the track
#: (the card the control sits on).
_CARD_JS = """() => {
    const seg = document.querySelector('.seg:has(#results_albums_all)');
    const chip = document.querySelector(
        '#results_albums_all:checked + label, '
        + '#results_albums_matched:checked + label');
    if (!seg || !chip) return null;
    const chain = [];
    for (let el = seg.parentElement; el; el = el.parentElement) {
        chain.push(getComputedStyle(el).backgroundColor);
    }
    return {border: getComputedStyle(chip).borderTopColor, chain};
}"""


def _matched_row(artist, album, plays, seconds, duration):
    """A matched result as the pipeline builds it, with a duration."""
    return {
        "artist": artist,
        "album": album,
        "play_count": plays,
        "play_time_seconds": seconds,
        "play_time": duration,
        "release_date": "2025-03-04",
        "provider": "spotify",
        "album_url": "https://open.spotify.com/album/sp-gate-include",
        "_normalized_key": normalize_name(artist, album),
    }


def _unmatched_row(album, reason, plays):
    """An included unmatched result, as ``merge_unmatched_rows`` builds it."""
    artist = f"{album} Band"
    return {
        "artist": artist,
        "album": album,
        "play_count": plays,
        "play_time_seconds": 0,
        "play_time": "",
        "release_date": None,
        "provider": None,
        "album_url": None,
        "unmatched_reason": reason,
        "_normalized_key": normalize_name(artist, album),
    }


def _surface(chain: list[str]) -> tuple[float, float, float]:
    """Composite a child-to-root chain of backgrounds over the white canvas."""
    surface = (255.0, 255.0, 255.0)
    for colour in reversed(chain):
        surface = _composite_over(_parse_rgb_string(colour), surface)
    return surface


def _set_theme(page, theme: str) -> None:
    page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
    wait_for_settled(page)


def text_contrast_failures(page, label: str, selector: str, count: int) -> list[str]:
    """Hold every node of *selector* at 7:1 on what paints behind it, both themes."""
    failures = []
    try:
        for theme in ("light", "dark"):
            _set_theme(page, theme)
            nodes = page.locator(selector)
            if nodes.count() != count:
                failures.append(
                    f"/results {label}: {nodes.count()} of {selector} on the "
                    f"page, expected {count}"
                )
                continue
            for index in range(count):
                paint = nodes.nth(index).evaluate(_PAINT_JS)
                surface = _surface(paint["chain"])
                ink = _composite_over(_parse_rgb_string(paint["text"]), surface)
                ratio = _contrast_ratio(ink, surface)
                if ratio < INCLUDE_TEXT_FLOOR:
                    failures.append(
                        f"/results {label} {index + 1}, {theme} theme: text is "
                        f"{ratio:.2f}:1 on its surface, under {INCLUDE_TEXT_FLOOR}:1"
                    )
    finally:
        _set_theme(page, "light")
    return failures


def card_boundary_failures(page) -> list[str]:
    """Hold the Albums control's selected border at 3:1 against the card."""
    failures = []
    try:
        for theme in ("light", "dark"):
            _set_theme(page, theme)
            paint = page.evaluate(_CARD_JS)
            if paint is None:
                failures.append(
                    "/results Albums control: no selected option to measure"
                )
                continue
            card = _surface(paint["chain"])
            border = _composite_over(_parse_rgb_string(paint["border"]), card)
            ratio = _contrast_ratio(border, card)
            if ratio < INCLUDE_BOUNDARY_FLOOR:
                failures.append(
                    f"/results Albums control, {theme} theme: selected border "
                    f"is {ratio:.2f}:1 against the card, under "
                    f"{INCLUDE_BOUNDARY_FLOOR}:1"
                )
    finally:
        _set_theme(page, "light")
    return failures


def overflow_failures(page, state: str) -> list[str]:
    """Fail when the page scrolls sideways at either checked width."""
    failures = []
    viewport = page.viewport_size
    try:
        for width in INCLUDE_OVERFLOW_WIDTHS:
            page.set_viewport_size({"width": width, "height": 800})
            wait_for_settled(page)
            if page.evaluate("() => document.documentElement.scrollWidth > innerWidth"):
                failures.append(
                    f"/results include run ({state}) overflows horizontally "
                    f"at {width}px"
                )
    finally:
        if viewport is not None:
            page.set_viewport_size(viewport)
    return failures


def matched_only_failures(page) -> list[str]:
    """Choose "Matched only" and read what the listener sees."""
    failures = []
    page.locator("label[for=results_albums_matched]").click()
    heights = page.locator("tbody tr[data-unmatched]:not([data-unmatched=''])")
    heights = heights.evaluate_all(
        "rows => rows.map(r => r.getBoundingClientRect().height)"
    )
    if len(heights) != 2 or any(height != 0 for height in heights):
        failures.append(
            f"/results Matched only: unmatched row heights are {heights}, "
            "expected two rows of 0"
        )
    ranks = page.locator("tbody tr:not([hidden]) .rank-num").all_text_contents()
    ranks = [rank.strip() for rank in ranks]
    if ranks != ["01", "02", "03"]:
        failures.append(f"/results Matched only: visible ranks read {ranks}")
    if page.locator("#toggle-sort-playtime").is_disabled():
        failures.append("/results Matched only: Listening Time is still disabled")
    return failures


def forced_colours_failures(page) -> list[str]:
    """Under forced colours the selected Albums option's border is Highlight."""
    failures = []
    page.emulate_media(forced_colors="active")
    try:
        wait_for_settled(page)
        reading = page.evaluate(
            """() => {
                const probe = document.createElement('div');
                probe.style.border = '2px solid Highlight';
                document.body.appendChild(probe);
                const highlight = getComputedStyle(probe).borderTopColor;
                probe.remove();
                const chip = document.querySelector(
                    '#results_albums_matched:checked + label, '
                    + '#results_albums_all:checked + label');
                return {
                    highlight,
                    border: chip ? getComputedStyle(chip).borderTopColor : null,
                };
            }"""
        )
        if reading["border"] != reading["highlight"]:
            failures.append(
                "/results Albums control, forced colours: selected option "
                f"border is {reading['border']}, not Highlight "
                f"({reading['highlight']})"
            )
    finally:
        page.emulate_media(forced_colors="null")
    return failures


def check_include_results_page(page, base_url: str) -> list[str]:
    """The real include-run Results page keeps its type legible and its ranks true.

    Seeds an include job and reads the rendered page. Every colour pairing is
    measured in both themes against the surface that paints behind the text:
    the two markers and the "unknown" release words, the Albums control's
    option text, selected text and selected-state boundary, and the Sort
    leaderboard's hovered option. "Matched only" must take both unmatched rows
    out of the layout (zero height), rank the rest 01..03 and enable Listening
    Time. Forced colours draw the selected option's border in Highlight, and
    the page never scrolls sideways at 390px or 1280px.
    """
    job_id = jobs.create(
        {
            "username": "gate",
            "year": 2025,
            "sort_mode": "playcount",
            "include_unmatched": True,
        }
    )
    failures = []

    def empty_spotlight(route):
        route.fulfill(json={})

    try:
        jobs.succeed(
            job_id,
            [
                _matched_row("Alpha Band", "Alpha", 50, 3000, "50 mins"),
                _unmatched_row("Lost One", "no_spotify_match", 45),
                _matched_row("Beta Band", "Beta", 40, 2000, "33 mins"),
                _unmatched_row("Lost Two", "provider_unavailable", 35),
                _matched_row("Gamma Band", "Gamma", 30, 1000, "16 mins"),
            ],
            "Done",
        )
        page.route("**/api/artist_spotlight?*", empty_spotlight)
        page.goto(f"{base_url}/results?job_id={job_id}", wait_until="domcontentloaded")
        wait_for_settled(page)

        failures.extend(
            text_contrast_failures(page, "marker", ".provider-badge--unmatched", 2)
        )
        failures.extend(
            text_contrast_failures(
                page, "unknown release", ".release-date-value--unknown", 2
            )
        )
        failures.extend(seg_contrast_failures(page, "Albums control", _ALBUMS_SEG))
        failures.extend(card_boundary_failures(page))
        failures.extend(overflow_failures(page, "all albums"))

        failures.extend(matched_only_failures(page))
        failures.extend(
            seg_contrast_failures(
                page,
                "Albums control (Matched only)",
                {
                    **_ALBUMS_SEG,
                    "selected": _ALBUMS_SEG["unselected"],
                    "unselected": _ALBUMS_SEG["selected"],
                },
            )
        )
        failures.extend(card_boundary_failures(page))
        failures.extend(seg_hover_failures(page, "Sort leaderboard", _SORT_SEG))
        failures.extend(forced_colours_failures(page))
        failures.extend(overflow_failures(page, "matched only"))
    finally:
        try:
            page.unroute("**/api/artist_spotlight?*", empty_spotlight)
        finally:
            jobs.delete(job_id)
    return failures
