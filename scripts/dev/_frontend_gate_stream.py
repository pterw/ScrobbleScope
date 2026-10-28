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
#: The width at which the tallest panel (all rows) nearly fills the chart, so a
#: dropped lift pushes its last row out of the visible box.
_PANEL_VIEWPORT = {"width": 1280, "height": 720}
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
    return _seed_job(weeks, payload, 0)


def _seed_job(weeks: int, payload: bool, skip_days: int) -> tuple[str, str]:
    """`seed_stream_job`, with the window starting `skip_days` after the first
    Monday so the first column is partial. Each week's plays then sit on the
    window's first weekday, which every week has inside the window."""
    job_id = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    stream = _weekly_artists(weeks)
    counts = {}
    for t, monday in enumerate(stream["weeks"]):
        total = stream["other"][t] + sum(a["counts"][t] for a in stream["artists"])
        day = datetime.date.fromisoformat(monday) + datetime.timedelta(days=skip_days)
        counts[day.isoformat()] = total
    last_day = (_FIRST_MONDAY + datetime.timedelta(days=7 * weeks - 1)).isoformat()
    for day in range(skip_days, 7 * weeks):
        counts.setdefault((_FIRST_MONDAY + datetime.timedelta(days=day)).isoformat(), 0)
    results = {
        "username": "frontend-gate",
        "from_date": (_FIRST_MONDAY + datetime.timedelta(days=skip_days)).isoformat(),
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


_WEEKS = 53
_HOVER_RANK = 0
#: Week 0 is the partial first column of the seeded job (it starts mid-week);
#: weeks 30 and 40 sit either side of the panel's flip at week 34.
_HOVER_WEEKS = (0, 30, 40)
_FLIP_AFTER = 34
_OUTSIDE = (2, 2)
_DIM = "0.25"
_HIT_TIMEOUT_MS = 5_000
_PANEL = "#stream-panel"
_RING = "rect.stream-column-ring"
_GUIDE = "line.stream-guide"
_MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)  # fmt: skip

#: A client point inside the band of one layer at one week, found by testing
#: the layer's own fill along that week's column (never by recomputing the
#: stack from the constants under test).
_POINT_IN_LAYER_JS = """([rank, week]) => {
    const svg = document.querySelector('#stream-chart');
    const path = svg.querySelector('path.stream-layer[data-rank="' + rank + '"]');
    const x = Number(svg.dataset.columns.split(' ')[week]);
    const height = svg.viewBox.baseVal.height;
    let first = null;
    let last = null;
    for (let y = 0; y <= height; y += 0.25) {
        if (path.isPointInFill(new DOMPoint(x, y))) {
            if (first === null) first = y;
            last = y;
        }
    }
    if (first === null) return null;
    const at = new DOMPoint(x, (first + last) / 2).matrixTransform(svg.getScreenCTM());
    return { x: at.x, y: at.y };
}"""

#: The same point, offered only once the stream is what the browser hits
#: there: a re-render can still be settling the layout under the pointer.
_HIT_POINT_JS = (
    "(args) => { const point = ("
    + _POINT_IN_LAYER_JS
    + ")(args); if (!point) return null;"
    " const hit = document.elementFromPoint(point.x, point.y);"
    " return hit && hit.closest('#stream-chart') ? point : null; }"
)

_READ_HOVER_JS = """([rank, week]) => {
    const stream = document.querySelector('#stream-chart');
    const grid = document.querySelector('#heatmap-result-frame svg[data-layout="desktop"]');
    const panel = document.querySelector('#stream-panel');
    const layers = Array.from(stream.querySelectorAll('path.stream-layer'));
    const opacity = (el) => getComputedStyle(el).opacity;
    const lefts = [];
    for (const cell of grid.querySelectorAll('.heatmap-cell')) {
        const box = cell.getBoundingClientRect();
        const x = Math.round(box.left * 100) / 100;
        if (!lefts.some((c) => c.left === x)) {
            lefts.push({ left: x, centre: box.left + box.width / 2 });
        }
    }
    lefts.sort((a, b) => a.left - b.left);
    const ring = grid.querySelector('rect.stream-column-ring');
    const ringBox = ring ? ring.getBoundingClientRect() : null;
    const panelBox = panel.getBoundingClientRect();
    const sbox = stream.getBoundingClientRect();
    const hovered = panel.querySelectorAll('.stream-panel-row.is-hovered');
    const visible = document.querySelector('#heatmap-grid').getBoundingClientRect();
    const rows = Array.from(panel.querySelectorAll('.stream-panel-row'));
    const outside = rows.filter((row) => {
        const box = row.getBoundingClientRect();
        return box.top < visible.top - 0.5 || box.bottom > visible.bottom + 0.5;
    });
    return {
        rowCount: rows.length,
        rowsOutside: outside.length,
        siblings: layers.filter((l) => l.dataset.rank !== String(rank)).map(opacity),
        hovered: opacity(layers.find((l) => l.dataset.rank === String(rank))),
        panelShown: !panel.hidden && panelBox.width > 0,
        header: panel.querySelector('.stream-panel-header')?.textContent ?? '',
        hoveredRows: Array.from(hovered).map((r) => r.dataset.rank),
        rings: document.querySelectorAll('rect.stream-column-ring').length,
        guides: stream.querySelectorAll('line.stream-guide').length,
        ringCentre: ringBox ? ringBox.left + ringBox.width / 2 : null,
        columnCentre: lefts[week].centre,
        streamColumn: sbox.left + Number(stream.dataset.columns.split(' ')[week])
            * sbox.width / stream.viewBox.baseVal.width,
        panelLeft: panelBox.left,
        panelRight: panelBox.right,
        panelBottom: panelBox.bottom,
        gridBottom: document.querySelector('#heatmap-grid').getBoundingClientRect().bottom,
    };
}"""


def _week_header(week: int) -> str:
    monday = datetime.date.fromisoformat(_weekly_artists(_WEEKS)["weeks"][week])
    return f"Week of {_MONTHS[monday.month - 1]} {monday.day} - "


def _point_in_layer(page, week: int) -> dict:
    """A viewport point on the hover layer at `week` that the stream receives."""
    page.locator(_STREAM).scroll_into_view_if_needed()
    handle = page.wait_for_function(
        _HIT_POINT_JS, arg=[_HOVER_RANK, week], timeout=_HIT_TIMEOUT_MS
    )
    return handle.json_value()


def _hover(page, week: int) -> dict:
    """Move the mouse onto the hover layer at `week` and read what shows."""
    point = _point_in_layer(page, week)
    page.mouse.move(point["x"], point["y"])
    wait_for_settled(page)
    return page.evaluate(_READ_HOVER_JS, [_HOVER_RANK, week])


def _hover_failures(reading: dict | None, week: int) -> list[str]:
    where = f"hovering week {week}"
    if reading is None:
        return [f"{where}: no point inside the layer to hover"]
    failures = []
    if not reading["siblings"] or any(o != _DIM for o in reading["siblings"]):
        failures.append(f"{where}: sibling layers are {set(reading['siblings'])}")
    if reading["hovered"] != "1":
        failures.append(
            f"{where}: the hovered layer is at opacity {reading['hovered']}"
        )
    if not reading["panelShown"]:
        failures.append(f"{where}: the panel is not shown")
    if not reading["header"].startswith(_week_header(week)):
        failures.append(f"{where}: the panel header reads {reading['header']!r}")
    if reading["hoveredRows"] != [str(_HOVER_RANK)]:
        failures.append(f"{where}: hovered rows are {reading['hoveredRows']}")
    if reading["rings"] != 1 or reading["guides"] != 1:
        failures.append(
            f"{where}: {reading['rings']} rings and {reading['guides']} guides"
        )
    elif abs(reading["ringCentre"] - reading["columnCentre"]) > 1:
        failures.append(f"{where}: the ring is off its heatmap column")
    if reading["panelBottom"] > reading["gridBottom"] + 0.5:
        failures.append(f"{where}: the panel runs past the bottom of the chart area")
    if reading["rowsOutside"]:
        failures.append(
            f"{where}: {reading['rowsOutside']} of {reading['rowCount']} panel rows"
            " are outside the chart's visible box"
        )
    column = reading["streamColumn"]
    if week > _FLIP_AFTER and reading["panelRight"] > column:
        failures.append(f"{where}: the panel does not flip left of the column")
    if week <= _FLIP_AFTER and reading["panelLeft"] < column:
        failures.append(f"{where}: the panel is not right of the column")
    return failures


def _cleared_failures(page, when: str) -> list[str]:
    reading = page.evaluate(_READ_HOVER_JS, [_HOVER_RANK, 0])
    failures = []
    if reading["rings"] or reading["guides"]:
        failures.append(f"{when}: a ring or guide remains")
    if reading["panelShown"]:
        failures.append(f"{when}: the panel is still shown")
    if any(o != "1" for o in reading["siblings"] + [reading["hovered"]]):
        failures.append(f"{when}: a layer is still dimmed")
    return failures


def _resize_failures(page, original: dict) -> list[str]:
    """A re-render with a week shown leaves no ring, panel or dimming."""
    _hover(page, 30)
    page.set_viewport_size(_NARROW_VIEWPORT)
    page.locator(_GRID_MOBILE).wait_for(state="visible")
    page.set_viewport_size(original)
    page.locator(_GRID_DESKTOP).wait_for(state="visible")
    wait_for_settled(page)
    failures = _cleared_failures(page, "after a re-render")
    # A move to the very point the pointer already sits at sends no event.
    page.mouse.move(*_OUTSIDE)
    again = _hover_failures(_hover(page, 30), 30)
    if again:
        failures.append(f"the next pointer move did not show the week again: {again}")
    return failures


def check_stream_hover_shows_panel_and_ring(page, base_url: str) -> list[str]:
    """Hovering a layer dims the rest, shows the panel, guide and column
    ring, and leaving removes all of it; a re-render clears a shown week."""
    failures = []
    original = page.viewport_size
    job_id, _last_day = _seed_job(_WEEKS, True, 2)
    try:
        page.set_viewport_size(_PANEL_VIEWPORT)
        _open_heatmap(page, base_url, job_id, _GRID_DESKTOP)
        for week in _HOVER_WEEKS:
            failures.extend(_hover_failures(_hover(page, week), week))
            page.mouse.move(*_OUTSIDE)
            wait_for_settled(page)
            failures.extend(_cleared_failures(page, f"leaving week {week}"))
        failures.extend(_resize_failures(page, original))
    finally:
        page.set_viewport_size(original)
        jobs.delete(job_id)
    return failures


_DRAG_FROM, _DRAG_TO = 10, 14


def _touch_drag_headers(page) -> list[str]:
    """Headers read while a touch drag crosses from week 10 to week 14."""
    start = _point_in_layer(page, _DRAG_FROM)
    end = _point_in_layer(page, _DRAG_TO)
    session = page.context.new_cdp_session(page)
    headers = []
    try:
        session.send(
            "Input.dispatchTouchEvent",
            {"type": "touchStart", "touchPoints": [start]},
        )
        for fraction in (0.0, 1.0):
            x = start["x"] + (end["x"] - start["x"]) * fraction
            session.send(
                "Input.dispatchTouchEvent",
                {"type": "touchMove", "touchPoints": [{"x": x, "y": start["y"]}]},
            )
            wait_for_settled(page)
            headers.append(
                page.evaluate(
                    "() => document.querySelector('.stream-panel-header')"
                    "?.textContent ?? ''"
                )
            )
        session.send(
            "Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}
        )
    finally:
        session.detach()
    return headers


def check_stream_touch_drag_scrubs(page, base_url: str) -> list[str]:
    """A horizontal touch drag across the stream moves the shown week.
    Chromium only: Firefox has no protocol to dispatch a touch drag."""
    if page.context.browser.browser_type.name != "chromium":
        return []
    job_id, _last_day = seed_stream_job()
    try:
        _open_heatmap(page, base_url, job_id, _GRID_DESKTOP)
        page.locator(_STREAM).scroll_into_view_if_needed()
        headers = _touch_drag_headers(page)
    finally:
        jobs.delete(job_id)
    expected = [_week_header(_DRAG_FROM), _week_header(_DRAG_TO)]
    if [h[: len(e)] for h, e in zip(headers, expected, strict=True)] != expected:
        return [f"a touch drag from week 10 to 14 showed headers {headers}"]
    return []


def check_stream_reduced_motion(page, base_url: str) -> list[str]:
    """The layer fade lasts 150ms normally and nothing under reduced motion."""
    job_id, _last_day = seed_stream_job()
    failures = []
    try:
        for preference, expected in (("no-preference", "0.15s"), ("reduce", "0s")):
            page.emulate_media(reduced_motion=preference)
            _open_heatmap(page, base_url, job_id, _GRID_DESKTOP)
            got = page.locator("path.stream-layer").first.evaluate(
                "el => getComputedStyle(el).transitionDuration"
            )
            if got != expected:
                failures.append(
                    f"stream layer transition lasts {got!r} with reduced motion "
                    f"{preference!r}, expected {expected!r}"
                )
    finally:
        page.emulate_media(reduced_motion="no-preference")
        jobs.delete(job_id)
    return failures
