"""Streamgraph checks and the fixture job they share.

A slice of the frontend gate. The stream under the heatmap grid is only
worth having if its weeks sit under the grid's columns, so the alignment is
read off rendered geometry (the cells' bounding boxes against the stream's
own `data-columns`), never recomputed from the constants under test.
"""

from __future__ import annotations

import datetime

from scripts.dev._frontend_gate_colour import _contrast_ratio, _parse_rgb_string
from scripts.dev._frontend_gate_shared import wait_for_settled
from scripts.dev._frontend_gate_theme import SET_THEME_EXPRESSION
from scrobblescope import jobs
from scrobblescope.listening_stats import heatmap_statistics

#: A Monday, so the first grid column holds seven real days and `weeks`
#: columns are exactly `weeks * 7` days long.
_FIRST_MONDAY = datetime.date(2025, 1, 6)
_ARTIST_COUNT = 10
_DESKTOP_MIN_WIDTH = 860
_SECOND_WIDTH = 1000
_NARROW_VIEWPORT = {"width": 390, "height": 844}
_STREAM = "#stream-chart"
_GRID_DESKTOP = '#heatmap-result-frame svg[data-layout="desktop"]'
_GRID_MOBILE = '#heatmap-result-frame svg[data-layout="mobile"]'


def _weekly_artists(weeks: int) -> dict:
    """A valid weekly_artists payload: ten artists, largest total first."""
    artists = [
        {
            "name": f"Artist {k}",
            "counts": [
                (10 - k) * (1 + (t * (k + 2) + k * 5) % 6) for t in range(weeks)
            ],
        }
        for k in range(_ARTIST_COUNT)
    ]
    artists.sort(key=lambda a: -sum(a["counts"]))
    return {
        "weeks": [
            (_FIRST_MONDAY + datetime.timedelta(days=7 * t)).isoformat()
            for t in range(weeks)
        ],
        "artists": artists,
        "other": [3 + t % 5 for t in range(weeks)],
    }


def seed_stream_job(weeks: int = 53, payload: bool = True) -> tuple[str, str]:
    """A finished heatmap job over `weeks` grid columns.

    `weekly_artists` is a valid payload with ten artists, or absent when
    `payload` is false. Each week's plays sit on its Monday, so the daily
    counts agree with the payload. Returns (job id, last day).
    """
    job_id = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    stream = _weekly_artists(weeks)
    counts = {}
    for t, monday in enumerate(stream["weeks"]):
        total = stream["other"][t] + sum(a["counts"][t] for a in stream["artists"])
        counts[monday] = total
    last_day = (_FIRST_MONDAY + datetime.timedelta(days=7 * weeks - 1)).isoformat()
    for day in range(7 * weeks):
        counts.setdefault((_FIRST_MONDAY + datetime.timedelta(days=day)).isoformat(), 0)
    results = {
        "username": "frontend-gate",
        "from_date": _FIRST_MONDAY.isoformat(),
        "to_date": last_day,
        "total_scrobbles": sum(counts.values()),
        "max_count": max(counts.values()),
        "daily_counts": counts,
        "statistics": heatmap_statistics(counts, datetime.date.fromisoformat(last_day)),
    }
    if payload:
        results["weekly_artists"] = stream
    jobs.succeed(job_id, results, "Done")
    return job_id, last_day


_READ_ALIGNMENT_JS = """() => {
    const stream = document.querySelector('#stream-chart');
    const grid = document.querySelector('#heatmap-result-frame svg[data-layout="desktop"]');
    if (!stream || !grid) return null;
    const scaleOf = (svg) => {
        const box = svg.getBoundingClientRect();
        return { left: box.left, scale: box.width / svg.viewBox.baseVal.width };
    };
    const s = scaleOf(stream);
    const columns = stream.dataset.columns.split(' ').map(Number);
    const centres = [];
    for (const cell of grid.querySelectorAll('.heatmap-cell')) {
        const box = cell.getBoundingClientRect();
        const x = Math.round(box.left * 100) / 100;
        if (!centres.some((c) => c.left === x)) {
            centres.push({ left: x, centre: box.left + box.width / 2 });
        }
    }
    centres.sort((a, b) => a.left - b.left);
    return {
        layers: stream.querySelectorAll('path.stream-layer').length,
        streamWidth: stream.viewBox.baseVal.width,
        gridWidth: grid.viewBox.baseVal.width,
        streamX: columns.map((x) => s.left + x * s.scale),
        cellX: centres.map((c) => c.centre),
    };
}"""


def _alignment_failures(reading: dict | None, width: int) -> list[str]:
    if reading is None:
        return [f"/heatmap draws no stream chart at {width}px"]
    failures = []
    if reading["layers"] != _ARTIST_COUNT + 1:
        failures.append(
            f"the stream has {reading['layers']} layers at {width}px, expected 11"
        )
    if reading["streamWidth"] != reading["gridWidth"]:
        failures.append(
            f"the stream viewBox is {reading['streamWidth']} wide at {width}px, "
            f"the grid's is {reading['gridWidth']}"
        )
    stream_x, cell_x = reading["streamX"], reading["cellX"]
    if len(stream_x) != len(cell_x):
        failures.append(
            f"the stream plots {len(stream_x)} weeks over {len(cell_x)} grid "
            f"columns at {width}px"
        )
        return failures
    off = [
        (t, round(s - c, 2))
        for t, (s, c) in enumerate(zip(stream_x, cell_x, strict=True))
        if abs(s - c) > 1
    ]
    if off:
        failures.append(
            f"stream weeks sit off their grid column centres at {width}px "
            f"(week, px off): {off[:3]}"
        )
    return failures


def _open_heatmap(page, base_url: str, job_id: str, layout_selector: str) -> None:
    page.goto(f"{base_url}/heatmap?job_id={job_id}", wait_until="load")
    page.locator(layout_selector).wait_for(state="visible")
    wait_for_settled(page)


def check_stream_aligns_with_grid_columns(page, base_url: str) -> list[str]:
    """Every stream week sits under its heatmap column, at two widths."""
    failures = []
    job_id, _last_day = seed_stream_job()
    original = page.viewport_size
    try:
        _open_heatmap(page, base_url, job_id, _GRID_DESKTOP)
        for width in (original["width"], _SECOND_WIDTH):
            page.set_viewport_size({"width": width, "height": original["height"]})
            wait_for_settled(page)
            failures.extend(
                _alignment_failures(page.evaluate(_READ_ALIGNMENT_JS), width)
            )
    finally:
        page.set_viewport_size(original)
        jobs.delete(job_id)
    return failures


def _stream_count(page) -> int:
    return page.locator(_STREAM).count()


def _expect_streams(page, expected: int, when: str) -> list[str]:
    found = _stream_count(page)
    if found == expected:
        return []
    return [f"/heatmap has {found} #stream-chart {when}, expected {expected}"]


def check_stream_absent_without_payload_or_on_mobile(page, base_url: str) -> list[str]:
    """No payload and the mobile layout draw no stream; a resize leaves one."""
    if page.viewport_size["width"] < _DESKTOP_MIN_WIDTH:
        return _mobile_failures(page, base_url)
    return _desktop_failures(page, base_url)


def _mobile_failures(page, base_url: str) -> list[str]:
    job_id, _last_day = seed_stream_job()
    try:
        _open_heatmap(page, base_url, job_id, _GRID_MOBILE)
        return _expect_streams(page, 0, "on the mobile layout with a payload")
    finally:
        jobs.delete(job_id)


def _desktop_failures(page, base_url: str) -> list[str]:
    failures = []
    original = page.viewport_size
    with_payload, _last_day = seed_stream_job()
    without_payload, _last_day = seed_stream_job(payload=False)
    try:
        # Control first: the stream is drawn when it should be.
        _open_heatmap(page, base_url, with_payload, _GRID_DESKTOP)
        failures.extend(_expect_streams(page, 1, "on desktop with a payload"))
        page.set_viewport_size(_NARROW_VIEWPORT)
        page.locator(_GRID_MOBILE).wait_for(state="visible")
        failures.extend(_expect_streams(page, 0, "after resizing to mobile"))
        page.set_viewport_size(original)
        page.locator(_GRID_DESKTOP).wait_for(state="visible")
        wait_for_settled(page)
        failures.extend(_expect_streams(page, 1, "after resizing back to desktop"))

        _open_heatmap(page, base_url, without_payload, _GRID_DESKTOP)
        failures.extend(_expect_streams(page, 0, "on desktop without a payload"))
    finally:
        page.set_viewport_size(original)
        jobs.delete(with_payload)
        jobs.delete(without_payload)
    return failures


#: What the frame's stream tokens resolve to in each theme (heatmap.css).
_OTHER_HEX = {"dark": "#3a3347", "light": "#ddd5c5"}
#: Layer fills are logged against the frame, not held to 3:1: the scrubber
#: panel states every layer as text, so a fill is exempt (rulings S13, U20).
_FLOOR_TEXT = 4.5

_READ_PAINT_JS = """(theme) => {
    const frame = document.getElementById('heatmap-result-frame');
    const stream = document.querySelector('#stream-chart');
    if (!frame || !stream) return null;
    const probe = (token) => {
        const el = document.createElement('div');
        el.style.color = 'var(' + token + ')';
        frame.appendChild(el);
        const colour = getComputedStyle(el).color;
        el.remove();
        return colour;
    };
    const hooks = window.__scrobbleHeatmapTestHooks;
    const fills = {};
    const expected = {};
    for (const path of stream.querySelectorAll('path.stream-layer:not(.stream-layer-other)')) {
        const rank = path.dataset.rank;
        fills[rank] = path.getAttribute('fill');
        expected[rank] = hooks.layerColour(parseInt(rank, 10), theme);
    }
    return {
        fills: fills,
        expected: expected,
        other: stream.querySelector('.stream-layer-other')?.getAttribute('fill'),
        lines: Array.from(stream.querySelectorAll('.stream-gridline'))
            .map((line) => line.getAttribute('stroke')),
        lineToken: probe('--stream-line'),
        label: stream.querySelector('.stream-section-label')?.getAttribute('fill'),
        labelToken: probe('--stream-muted'),
        frame: getComputedStyle(frame).backgroundColor,
    };
}"""


def _rgb(value: str | None) -> tuple[float, float, float]:
    return _parse_rgb_string(value or "")[:3]


def _hex_rgb(value: str) -> tuple[float, float, float]:
    return tuple(float(int(value[i : i + 2], 16)) for i in (1, 3, 5))


def _paint_failures(reading, theme: str) -> list[str]:
    """Compare one theme's stream paint with its tokens and the contrast floors."""
    if reading is None:
        return [f"/heatmap draws no stream chart in the {theme} theme"]
    failures = []
    if not reading["fills"]:
        failures.append(f"the stream draws no artist layers in the {theme} theme")
    if not reading["lines"]:
        failures.append(f"the stream draws no gridlines in the {theme} theme")
    for rank, fill in reading["fills"].items():
        if _rgb(fill) != _rgb(reading["expected"][rank]):
            failures.append(
                f"layer {rank} fill is {fill} in the {theme} theme, "
                f"expected {reading['expected'][rank]}"
            )
    if _rgb(reading["other"]) != _hex_rgb(_OTHER_HEX[theme]):
        failures.append(
            f"'Everything else' fill is {reading['other']} in the {theme} theme, "
            f"expected {_OTHER_HEX[theme]}"
        )
    for index, line in enumerate(reading["lines"]):
        if _rgb(line) != _rgb(reading["lineToken"]):
            failures.append(
                f"gridline {index} stroke is {line} in the {theme} theme, "
                f"expected {reading['lineToken']}"
            )
    if _rgb(reading["label"]) != _rgb(reading["labelToken"]):
        failures.append(
            f"section label fill is {reading['label']} in the {theme} theme, "
            f"expected {reading['labelToken']}"
        )
    frame = _rgb(reading["frame"])
    ratios = [_contrast_ratio(_rgb(fill), frame) for fill in reading["fills"].values()]
    label_ratio = _contrast_ratio(_rgb(reading["label"]), frame)
    print(
        f"[stream colours] {theme}: layer vs frame min {min(ratios):.2f} "
        f"max {max(ratios):.2f}, label vs frame {label_ratio:.2f}"
    )
    if label_ratio < _FLOOR_TEXT:
        failures.append(
            f"the section label is {label_ratio:.2f}:1 against the frame in the "
            f"{theme} theme, floor {_FLOOR_TEXT}"
        )
    return failures


def check_stream_colours_follow_theme_and_meet_contrast(
    page, base_url: str
) -> list[str]:
    """Switching the theme repaints the stream without a re-render."""
    failures = []
    job_id, _last_day = seed_stream_job()
    # The expected layer colour comes from the page's own ramp, which the
    # test seam exposes only when the flag is set before the script runs.
    probe = page.context.new_page()
    try:
        probe.add_init_script("window.__scrobbleHeatmapTestMode = true")
        probe.goto(f"{base_url}/heatmap?job_id={job_id}", wait_until="load")
        probe.locator(_STREAM).wait_for(state="attached")
        probe.evaluate(
            "() => { window.__streamNode = document.querySelector('#stream-chart'); }"
        )
        for theme in ("dark", "light", "dark"):
            probe.evaluate(SET_THEME_EXPRESSION, theme)
            wait_for_settled(probe)
            if not probe.evaluate(
                "() => window.__streamNode === document.querySelector('#stream-chart')"
            ):
                failures.append(f"the {theme} switch re-rendered the stream")
            failures.extend(
                _paint_failures(probe.evaluate(_READ_PAINT_JS, theme), theme)
            )
    finally:
        probe.close()
        jobs.delete(job_id)
    return failures
