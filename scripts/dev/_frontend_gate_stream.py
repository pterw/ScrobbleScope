"""Streamgraph checks and the fixture job they share.

A slice of the frontend gate. The stream under the heatmap grid is only
worth having if its weeks sit under the grid's columns, so the alignment is
read off rendered geometry (the cells' bounding boxes against the stream's
own `data-columns`), never recomputed from the constants under test.
"""

from __future__ import annotations

import datetime
from base64 import b64encode
from pathlib import Path

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
#: Tracking that stands in for a wider fallback face (what CI's Linux runner
#: draws the panel in when the kit is refused): with it the panel's longest
#: header measures past the 260px minimum width.
_WIDE_FALLBACK_CSS = ".stream-panel { letter-spacing: 0.15em; }"
#: A 60-character artist name, to give the panel more width than the room
#: beside a column near the chart's right edge.
_LONG_NAME = "The Extraordinarily Long-Winded Orchestra of Wandering Souls"
_STREAM = "#stream-chart"
_GRID_DESKTOP = '#heatmap-result-frame svg[data-layout="desktop"]'
_GRID_MOBILE = '#heatmap-result-frame svg[data-layout="mobile"]'


def _weekly_artists(weeks: int, long_name: bool = False) -> dict:
    """Ten featured artists and a residual-only third week.

    `long_name` gives the first artist a 60-character name."""
    artists = [
        {
            "name": _LONG_NAME if long_name and k == 0 else f"Artist {k}",
            "counts": [
                (10 - k) * (1 + (t * (k + 2) + k * 5) % 6) for t in range(weeks)
            ],
        }
        for k in range(10)
    ]
    artists.sort(key=lambda a: -sum(a["counts"]))
    if weeks > 2:
        for artist in artists:
            artist["counts"][2] = 0
    return {
        "weeks": [
            (_FIRST_MONDAY + datetime.timedelta(days=7 * t)).isoformat()
            for t in range(weeks)
        ],
        "artists": artists,
        # Enough exposed margin to verify halo pixels without sampling its contour.
        "other": [80 + t % 5 + (160 if t % 3 == 0 else 0) for t in range(weeks)],
    }


def seed_stream_job(weeks: int = 53, payload: bool = True) -> tuple[str, str]:
    """A finished heatmap job over `weeks` grid columns.

    `weekly_artists` is a valid payload with ten artists, or absent when
    `payload` is false. Each week's plays sit on its Monday, so the daily
    counts agree with the payload. Returns (job id, last day).
    """
    return _seed_job(weeks, payload, 0)


def _seed_job(
    weeks: int,
    payload: bool,
    skip_days: int,
    long_name: bool = False,
    stream: dict | None = None,
    end_early: int = 0,
) -> tuple[str, str]:
    """`seed_stream_job`, with the window starting `skip_days` after the first
    Monday so the first column is partial. Each week's plays then sit on the
    window's first weekday, which every week has inside the window. An explicit
    `stream` supplies degenerate payloads for the same real job lifecycle.
    `end_early` excludes days at the end to exercise a partial last week."""
    job_id = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    stream = _weekly_artists(weeks, long_name) if stream is None else stream
    counts = {}
    for t, monday in enumerate(stream["weeks"]):
        total = stream["other"][t] + sum(a["counts"][t] for a in stream["artists"])
        day = datetime.date.fromisoformat(monday) + datetime.timedelta(days=skip_days)
        counts[day.isoformat()] = total
    last_day = (
        _FIRST_MONDAY + datetime.timedelta(days=7 * weeks - end_early - 1)
    ).isoformat()
    for day in range(skip_days, 7 * weeks - end_early):
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
    const box = stream.getBoundingClientRect();
    const lines = Array.from(stream.querySelectorAll('.stream-gridline'));
    return {
        layers: stream.querySelectorAll('path.stream-layer').length,
        ranks: Array.from(stream.querySelectorAll('path.stream-layer'))
            .map((path) => path.dataset.rank),
        streamWidth: stream.viewBox.baseVal.width,
        gridWidth: grid.viewBox.baseVal.width,
        streamX: columns.map((x) => s.left + x * s.scale),
        cellX: centres.map((c) => c.centre),
        months: Array.from(stream.querySelectorAll('.stream-month-label')).map(label => {
            const bounds = label.getBoundingClientRect();
            return { text: label.textContent, x: Number(label.getAttribute('x')),
                below: Number(label.getAttribute('y')) > Number(lines[0].getAttribute('y2')),
                inside: bounds.left >= box.left - 0.5 && bounds.right <= box.right + 0.5
                    && bounds.bottom <= box.bottom + 0.5 };
        }),
        lineX: lines.map(line => Number(line.getAttribute('x1'))),
        gridMonths: Array.from(grid.querySelectorAll('.heatmap-month-label')).map(label =>
            ({ text: label.textContent, x: Number(label.getAttribute('x')) })),
        caption: stream.querySelector('.stream-caption')?.textContent ?? '',
    };
}"""


def _alignment_failures(reading: dict | None, width: int) -> list[str]:
    if reading is None:
        return [f"/heatmap draws no stream chart at {width}px"]
    failures = []
    if reading["layers"] != _ARTIST_COUNT:
        failures.append(
            f"the stream has {reading['layers']} layers at {width}px, "
            f"expected {_ARTIST_COUNT} named artist layers"
        )
    if set(reading["ranks"]) != {str(rank) for rank in range(_ARTIST_COUNT)}:
        failures.append(
            f"the stream's named artist ranks differ at {width}px: {reading['ranks']}"
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
    months = reading["months"]
    if len(months) != len(reading["gridMonths"]) or len(reading["lineX"]) != len(
        months
    ):
        failures.append(
            f"bottom month labels or calendar gridlines differ at {width}px"
        )
    else:
        for label, line_x, grid_month in zip(
            months, reading["lineX"], reading["gridMonths"], strict=True
        ):
            if (
                label["text"] != grid_month["text"]
                or label["x"] != grid_month["x"]
                or label["x"] != line_x
                or not label["below"]
                or not label["inside"]
            ):
                failures.append(
                    f"bottom month is misplaced at {width}px: {label}, {grid_month}"
                )
    if "0.25" not in reading["caption"] or "other" not in reading["caption"].lower():
        failures.append(
            "the stream caption does not explain compressed other listening"
        )
    return failures


def _open_heatmap(page, base_url: str, job_id: str, layout_selector: str) -> None:
    page.goto(f"{base_url}/heatmap?job_id={job_id}", wait_until="load")
    page.locator(layout_selector).wait_for(state="visible")
    wait_for_settled(page)


def check_stream_aligns_with_grid_columns(page, base_url: str) -> list[str]:
    """Every stream week sits under its heatmap column, at two widths."""
    failures = []
    jobs_to_check = [_seed_job(53, True, 2), _seed_job(52, True, 2, end_early=3)]
    original = page.viewport_size
    try:
        for job_id, _last_day in jobs_to_check:
            _open_heatmap(page, base_url, job_id, _GRID_DESKTOP)
            for width in (original["width"], _SECOND_WIDTH):
                page.set_viewport_size({"width": width, "height": original["height"]})
                wait_for_settled(page)
                reading = page.evaluate(_READ_ALIGNMENT_JS)
                failures.extend(_alignment_failures(reading, width))
                if _last_day == "2026-01-01" and (
                    not reading["gridMonths"]
                    or reading["gridMonths"][-1]["text"] != "Jan"
                    or reading["gridWidth"] - reading["gridMonths"][-1]["x"] > 20
                ):
                    failures.append(
                        "the partial end-week fixture does not reach January"
                    )
    finally:
        page.set_viewport_size(original)
        for job_id, _last_day in jobs_to_check:
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
    residual = _weekly_artists(_WEEKS)
    residual["artists"] = []
    only_other, _last_day = _seed_job(_WEEKS, True, 0, stream=residual)
    empty = {**residual, "other": [0] * _WEEKS}
    all_zero, _last_day = _seed_job(_WEEKS, True, 0, stream=empty)
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
        _open_heatmap(page, base_url, only_other, _GRID_DESKTOP)
        failures.extend(_expect_streams(page, 1, "with only residual plays"))
        if _stream_count(page):
            if page.locator(f"{_STREAM} path.stream-layer").count():
                failures.append("a residual-only chart paints a named artist layer")
            if page.locator(f"{_STREAM} path.stream-halo").count() != 1:
                failures.append("residual-only listening has no contextual halo")
            page.locator(_STREAM).focus()
            page.keyboard.press("Home")
            failures.extend(
                _step_failures(
                    page, 0, 0, "residual-only keyboard focus", residual["other"][0]
                )
            )
            page.keyboard.press("ArrowRight")
            failures.extend(
                _step_failures(
                    page, 1, 0, "residual-only next week", residual["other"][1]
                )
            )
        _open_heatmap(page, base_url, all_zero, _GRID_DESKTOP)
        failures.extend(_expect_streams(page, 0, "with an all-zero payload"))
    finally:
        page.set_viewport_size(original)
        jobs.delete(with_payload)
        jobs.delete(without_payload)
        jobs.delete(only_other)
        jobs.delete(all_zero)
    return failures


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
    for (const path of stream.querySelectorAll('path.stream-layer')) {
        const rank = path.dataset.rank;
        if (!/^\\d+$/.test(rank)) continue;
        fills[rank] = path.getAttribute('fill');
        expected[rank] = hooks.layerColour(parseInt(rank, 10), theme);
    }
    return {
        fills: fills,
        expected: expected,
        halo: stream.querySelector('.stream-halo') ? {
            fill: stream.querySelector('.stream-halo').getAttribute('fill'),
            stroke: stream.querySelector('.stream-halo').getAttribute('stroke'),
            pointer: getComputedStyle(stream.querySelector('.stream-halo')).pointerEvents,
            behind: Array.from(stream.querySelectorAll('.stream-layer')).every(path =>
                !!(stream.querySelector('.stream-halo').compareDocumentPosition(path)
                    & Node.DOCUMENT_POSITION_FOLLOWING)),
        } : null,
        haloFill: probe('--stream-halo-fill'),
        haloStroke: probe('--stream-halo-stroke'),
        lines: Array.from(stream.querySelectorAll('.stream-gridline'))
            .map((line) => line.getAttribute('stroke')),
        lineToken: probe('--stream-line'),
        label: stream.querySelector('.stream-section-label')?.getAttribute('fill'),
        labelToken: probe('--stream-muted'),
        frame: getComputedStyle(frame).backgroundColor,
    };
}"""


def _rgb(value: str | None) -> tuple[float, float, float]:
    """Read a computed colour or a six-digit stream palette hex value."""
    if value and value.startswith("#") and len(value) == 7:
        return _hex_rgb(value)
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
    halo = reading["halo"]
    if (
        not halo
        or _rgb(halo["fill"]) != _rgb(reading["haloFill"])
        or _rgb(halo["stroke"]) != _rgb(reading["haloStroke"])
        or halo["pointer"] != "none"
        or not halo["behind"]
    ):
        failures.append(
            f"the {theme} halo paint, order or pointer behavior differs: {halo}"
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
_HOVER_WEEKS = (0, 30, 33, 40)
_FLIP_AFTER = 34
#: A 1024x768 window: the far weeks leave less room than the panel's minimum
#: on the reference's side, so first, flip and last weeks are hovered there.
_LAPTOP_VIEWPORT = {"width": 1024, "height": 768}
_LAPTOP_WEEKS = (0, _FLIP_AFTER, _WEEKS - 1)
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
    const opacity = (el) => el ? getComputedStyle(el).opacity : null;
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
    const host = document.querySelector('#heatmap-grid');
    const visible = host.getBoundingClientRect();
    const rows = Array.from(panel.querySelectorAll(
        '.stream-panel-row, .stream-panel-hidden'));
    const outside = rows.filter((row) => {
        const box = row.getBoundingClientRect();
        return box.top < visible.top - 0.5 || box.bottom > visible.bottom + 0.5;
    });
    return {
        rowCount: rows.length,
        rowsOutside: outside.length,
        verticalScroll: host.scrollHeight > host.clientHeight + 1
            || panel.scrollHeight > panel.clientHeight + 1,
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
        gridBottom: visible.bottom,
        gridLeft: visible.left,
        gridRight: visible.right,
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


def _hover_failures(
    reading: dict | None,
    week: int,
    wide_fallback: bool = False,
    reference_side: bool = True,
) -> list[str]:
    face = " (wide fallback face)" if wide_fallback else ""
    if not reference_side:
        face = " (laptop width)"
    where = f"hovering week {week}{face}"
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
    if reading["verticalScroll"]:
        failures.append(f"{where}: the chart or panel requires vertical scrolling")
    if (
        reading["panelLeft"] < reading["gridLeft"] - 0.5
        or reading["panelRight"] > reading["gridRight"] + 0.5
    ):
        failures.append(f"{where}: the panel runs past the side of the chart area")
    column = reading["streamColumn"]
    if not reference_side:
        # A laptop-width chart can leave too little room on the reference's
        # side; the panel then opens to the other one, never across the column.
        if reading["panelLeft"] < column < reading["panelRight"]:
            failures.append(f"{where}: the panel sits over the column")
        return failures
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


_READ_CONTEXT_JS = """() => {
    const svg = document.querySelector('#stream-chart');
    const halo = svg.querySelector('.stream-halo');
    const button = document.querySelector('#stream-context-toggle');
    return {
        pressed: button.getAttribute('aria-pressed'),
        visibility: getComputedStyle(halo).visibility,
        paths: Array.from(svg.querySelectorAll('path.stream-layer')).map(path =>
            [path.dataset.rank, path.getAttribute('d')]),
        sameNodes: window.__streamGateArtistNodes.every((path, i) =>
            path === svg.querySelectorAll('path.stream-layer')[i]),
        label: button.getAttribute('aria-label') || button.textContent.trim(),
    };
}"""


def check_stream_context_toggle_preserves_artists(page, base_url: str) -> list[str]:
    """GIVEN a context halo, WHEN keys toggle it, THEN only its visibility changes.

    Actual weekly rows, artist nodes and path coordinates survive both states;
    the control is reached by Tab and activates with Space and Enter.
    """
    failures = []
    job_id, _last_day = seed_stream_job()
    try:
        _open_heatmap(page, base_url, job_id, _GRID_DESKTOP)
        page.evaluate("""() => { window.__streamGateArtistNodes =
            Array.from(document.querySelectorAll('#stream-chart path.stream-layer')); }""")
        initial = page.evaluate(_READ_CONTEXT_JS)
        if (
            initial["pressed"] != "true"
            or initial["visibility"] != "visible"
            or not initial["label"]
        ):
            failures.append(f"the default-on context control differs: {initial}")
        _hover(page, 6)
        counts = page.evaluate(_PANEL_ROWS_JS)["counts"]
        for key, pressed, visibility in (
            ("Space", "false", "hidden"),
            ("Enter", "true", "visible"),
        ):
            # Walk backwards from the grid so this proves a keyboard-reachable control.
            page.locator(f"{_GRID_DESKTOP} .heatmap-cell[tabindex='0']").focus()
            for _ in range(_MAX_TAB_PRESSES):
                page.keyboard.press("Shift+Tab")
                if page.locator("#stream-context-toggle").evaluate(
                    "el => el === document.activeElement"
                ):
                    break
            else:
                failures.append("Tab traversal cannot reach Other listening")
                break
            outline = page.locator("#stream-context-toggle").evaluate(
                "el => getComputedStyle(el).outlineStyle"
            )
            if outline == "none":
                failures.append("the context toggle has no keyboard focus indicator")
            page.keyboard.press(key)
            current = page.evaluate(_READ_CONTEXT_JS)
            if (
                current["pressed"] != pressed
                or current["visibility"] != visibility
                or current["paths"] != initial["paths"]
                or not current["sameNodes"]
            ):
                failures.append(
                    f"{key} changes more than context visibility: {current}"
                )
            failures.extend(_hover_failures(_hover(page, 6), 6))
            if page.evaluate(_PANEL_ROWS_JS)["counts"] != counts:
                failures.append(f"{key} changes true weekly tooltip counts")
            row = page.evaluate(_PANEL_ROWS_JS)["ranks"].index(str(_HOVER_RANK))
            failures.extend(_step_failures(page, 6, row, f"after context {pressed}"))
    finally:
        jobs.delete(job_id)
    return failures


def check_stream_hover_shows_panel_and_ring(page, base_url: str) -> list[str]:
    """Hovering a layer dims the rest, shows the panel, guide and column
    ring, and leaving removes all of it; a re-render clears a shown week."""
    failures = []
    original = page.viewport_size
    job_id, _last_day = _seed_job(_WEEKS, True, 2, long_name=True)
    try:
        page.set_viewport_size(_LAPTOP_VIEWPORT)
        failures.extend(
            _hover_pass(page, base_url, job_id, False, _LAPTOP_WEEKS, False)
        )
        page.set_viewport_size(_PANEL_VIEWPORT)
        for wide_fallback in (False, True):
            failures.extend(_hover_pass(page, base_url, job_id, wide_fallback))
        failures.extend(_resize_failures(page, original))
    finally:
        page.set_viewport_size(original)
        jobs.delete(job_id)
    return failures


_PANEL_TRACKING_JS = (
    "() => getComputedStyle(document.querySelector('#stream-panel')).letterSpacing"
)


def _is_kit_request(url: str) -> bool:
    return "typekit.net" in url


def _hover_pass(
    page,
    base_url: str,
    job_id: str,
    wide_fallback: bool,
    weeks: tuple = _HOVER_WEEKS,
    reference_side: bool = True,
) -> list[str]:
    """Hover each week; `wide_fallback` refuses the Adobe kit and widens the
    panel's text to what a Linux runner's fallback face measures, so a panel
    that only fits the narrow faces fails here as it did in CI.
    `reference_side` False lets the panel open to either side of the column."""
    failures = []
    tag = None
    if wide_fallback:
        page.route(_is_kit_request, lambda route: route.abort())
    try:
        _open_heatmap(page, base_url, job_id, _GRID_DESKTOP)
        if wide_fallback:
            tag = page.add_style_tag(content=_WIDE_FALLBACK_CSS)
            tracking = page.evaluate(_PANEL_TRACKING_JS)
            if tracking == "normal":
                failures.append(
                    "the wide fallback tracking is not in effect on the panel"
                )
        for week in weeks:
            reading = _hover(page, week)
            failures.extend(
                _hover_failures(reading, week, wide_fallback, reference_side)
            )
            page.mouse.move(*_OUTSIDE)
            wait_for_settled(page)
            failures.extend(_cleared_failures(page, f"leaving week {week}"))
        # A week without featured plays still scrubs the real residual total.
        point = page.locator(_STREAM).evaluate("""svg => {
            const box = svg.getBoundingClientRect();
            return { x: box.left + Number(svg.dataset.columns.split(' ')[2])
                * box.width / svg.viewBox.baseVal.width, y: box.top + box.height / 2 };
        }""")
        page.mouse.move(point["x"], point["y"])
        failures.extend(_step_failures(page, 2, -1, "residual-only pointer week"))
        reading = page.evaluate(_READ_HOVER_JS, [_HOVER_RANK, 2])
        if reading["guides"] != 1 or any(
            opacity != "1" for opacity in reading["siblings"] + [reading["hovered"]]
        ):
            failures.append(
                "a residual-only pointer week dims artists or loses its guide"
            )
    finally:
        if wide_fallback:
            page.unroute(_is_kit_request)
        if tag is not None:
            tag.evaluate("el => el.remove()")
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


_START_WEEK = 26
_LAST_WEEK = _WEEKS - 1
_MAX_TAB_PRESSES = 5
_FOCUS_THEMES = ("dark", "light")
_FLOOR_NON_TEXT = 3.0
_RING_PX = 6  # outline width 2 plus offset 4: how far it paints past the chart
#: Key, then the week and panel row it should leave the stream on (row 0 is the
#: top of the stack). Edges clamp: Left at week 0 and Right at the last week
#: stay put, Up at the top stays on row 0.
_KEY_STEPS = (
    ("ArrowRight", _START_WEEK + 1, 0),
    ("ArrowDown", _START_WEEK + 1, 1),
    ("ArrowLeft", _START_WEEK, 1),
    ("Home", 0, 1),
    ("ArrowLeft", 0, 1),
    ("End", _LAST_WEEK, 1),
    ("ArrowRight", _LAST_WEEK, 1),
    ("ArrowUp", _LAST_WEEK, 0),
    ("ArrowUp", _LAST_WEEK, 0),
)

_ACTIVE_JS = """() => {
    const el = document.activeElement;
    return {
        isStream: !!el && el.id === 'stream-chart',
        isCell: !!el && el.classList.contains('heatmap-cell'),
        isSentinel: !!el && el.id === 'stream-gate-sentinel',
    };
}"""

#: A stop the check adds to its own page right after the stream, so a Tab out of
#: the stream has somewhere to land that is not browser chrome.
_ADD_SENTINEL_JS = """() => {
    const sentinel = document.createElement('button');
    sentinel.id = 'stream-gate-sentinel';
    sentinel.type = 'button';
    document.querySelector('#stream-chart').after(sentinel);}"""

_REMOVE_SENTINEL_JS = """() => {
    const sentinel = document.getElementById('stream-gate-sentinel');
    if (sentinel) sentinel.remove();
}"""

_PANEL_ROWS_JS = """() => {
    const rows = Array.from(document.querySelectorAll('#stream-panel .stream-panel-row'));
    const other = rows.find((row) => row.dataset.rank === 'other');
    const rules = document.querySelectorAll('#stream-panel .stream-panel-rule');
    const counts = rows.map(row => row.querySelector('.stream-panel-count'));
    return {
        ranks: rows.map((r) => r.dataset.rank),
        counts: rows.map((row, i) => [row.dataset.rank,
            Number(counts[i].textContent.replaceAll(',', ''))]),
        hovered: rows.findIndex((r) => r.classList.contains('is-hovered')),
        otherCount: other ? Number(other.querySelector('.stream-panel-count').textContent.replaceAll(',', '')) : null,
        otherWeight: other ? getComputedStyle(other).fontWeight : null,
        circles: rows.every(row => {
            const marker = row.querySelector('.stream-panel-swatch');
            if (!marker) return false;
            const css = getComputedStyle(marker);
            const width = parseFloat(css.width);
            return width >= 8 && width <= 10 && css.width === css.height
                && (css.borderRadius === '50%' || parseFloat(css.borderRadius) >= width / 2);
        }),
        alignedCounts: counts.every(count =>
            Math.abs(count.getBoundingClientRect().right - counts[0].getBoundingClientRect().right) <= 0.5
            && getComputedStyle(count).fontVariantNumeric.includes('tabular-nums')),
        rules: rules.length,
        ruleBeforeOther: !!other && other.previousElementSibling?.classList.contains('stream-panel-rule'),
        contributors: document.querySelectorAll('#stream-panel .stream-panel-hidden').length,
    };
}"""

_READ_OUTLINE_JS = """() => {
    const stream = document.querySelector('#stream-chart');
    const frame = document.getElementById('heatmap-result-frame');
    const grid = document.getElementById('heatmap-grid');
    const css = getComputedStyle(stream);
    const box = stream.getBoundingClientRect();
    const room = grid.getBoundingClientRect();
    return {
        style: css.outlineStyle,
        width: css.outlineWidth,
        offset: css.outlineOffset,
        colour: css.outlineColor,
        frame: getComputedStyle(frame).backgroundColor,
        left: box.left - room.left,
        right: room.right - box.right,
        bottom: room.bottom - box.bottom,
    };
}"""


#: The stream and everything inside it that a Tab can land on.
_STOPS_IN_STREAM_JS = """() => {
    const stream = document.querySelector('#stream-chart');
    return [stream, ...stream.querySelectorAll('*')].filter((el) => el.tabIndex >= 0).length;
}"""

#: The layer fade lasts 150ms; a reading taken inside it is not "still dimmed".
_FADE_MS = 300


def _cleared_after(page, when: str) -> list[str]:
    wait_for_settled(page)
    page.wait_for_timeout(_FADE_MS)
    return _cleared_failures(page, when)


def _tab_to_stream(page) -> list[str]:
    """Tab from the Save button: one grid cell stop, then the stream, then out."""
    page.locator("#heatmap-save-image").focus()
    for _ in range(_MAX_TAB_PRESSES):
        page.keyboard.press("Tab")
        if page.evaluate(_ACTIVE_JS)["isCell"]:
            break
    else:
        return ["Tab never reaches the grid's cell stop"]
    page.keyboard.press("Tab")
    if not page.evaluate(_ACTIVE_JS)["isStream"]:
        return ["the Tab after the grid's cell stop does not reach the stream"]
    return []


def _step_failures(
    page, week: int, row: int, when: str, expected_total: int | None = None
) -> list[str]:
    """The week, ring and panel row the stream shows right now."""
    wait_for_settled(page)
    reading = page.evaluate(_READ_HOVER_JS, [_HOVER_RANK, week])
    rows = page.evaluate(_PANEL_ROWS_JS)
    failures = []
    if not reading["panelShown"]:
        failures.append(f"{when}: the panel is not shown")
    payload = _weekly_artists(_WEEKS)
    if expected_total is None:
        expected_total = payload["other"][week] + sum(
            artist["counts"][week] for artist in payload["artists"]
        )
    expected_header = f"{_week_header(week)}{expected_total:,} scrobbles"
    if reading["header"] != expected_header:
        failures.append(
            f"{when}: the panel header reads {reading['header']!r}, expected {expected_header!r}"
        )
    if reading["rings"] != 1:
        failures.append(f"{when}: {reading['rings']} column rings")
    elif abs(reading["ringCentre"] - reading["columnCentre"]) > 1:
        failures.append(f"{when}: the ring is not on week {week}'s column")
    if rows["hovered"] != row:
        failures.append(
            f"{when}: panel row {rows['hovered']} is hovered, expected {row}"
        )
    if rows["otherCount"] != payload["other"][week]:
        failures.append(f"{when}: the residual count is {rows['otherCount']}")
    if rows["otherWeight"] != "400" or not rows["circles"] or not rows["alignedCounts"]:
        failures.append(
            f"{when}: tooltip markers, numeric alignment or residual weight differ: {rows}"
        )
    expected_counts = (
        {
            str(rank): artist["counts"][week]
            for rank, artist in enumerate(payload["artists"])
            if artist["counts"][week] > 0
        }
        if expected_total != payload["other"][week]
        else {}
    )
    expected_counts["other"] = payload["other"][week]
    if dict(rows["counts"]) != expected_counts:
        failures.append(
            f"{when}: the tooltip changes actual artist or residual counts: {rows}"
        )
    if (
        rows["rules"] != (1 if len(rows["ranks"]) > 1 else 0)
        or (len(rows["ranks"]) > 1 and not rows["ruleBeforeOther"])
        or rows["contributors"]
    ):
        failures.append(
            f"{when}: the residual divider or removed contributor rows differ: {rows}"
        )
    if 0 <= row < len(rows["ranks"]) and rows["ranks"][row] == "other":
        opacities = reading["siblings"] + [reading["hovered"]]
        if any(o != "1" for o in opacities if o is not None):
            failures.append(
                f"{when}: selecting the residual dims artist paths: {opacities}"
            )
    return failures


def _walk_failures(page) -> list[str]:
    failures = _step_failures(page, _START_WEEK, 0, "on focus")
    for key, week, row in _KEY_STEPS:
        page.keyboard.press(key)
        failures.extend(_step_failures(page, week, row, f"{key} to week {week}"))
    # Down from the top reaches every numeric row, ending on "Everything else".
    rows = page.evaluate(_PANEL_ROWS_JS)["ranks"]
    for _ in range(len(rows) + 1):
        page.keyboard.press("ArrowDown")
    failures.extend(
        _step_failures(page, _LAST_WEEK, len(rows) - 1, "ArrowDown to the end")
    )
    if rows[-1] != "other":
        failures.append(f"the panel's last row is {rows[-1]!r}, not 'other'")
    return failures


def _outline_failures(page) -> list[str]:
    """The focus outline is 2px at offset 4px, unclipped, and clears 3:1."""
    failures = []
    original = page.evaluate("() => document.documentElement.dataset.theme ?? ''")
    ratios = []
    try:
        for theme in _FOCUS_THEMES:
            page.evaluate(SET_THEME_EXPRESSION, theme)
            wait_for_settled(page)
            reading = page.evaluate(_READ_OUTLINE_JS)
            if (reading["style"], reading["width"], reading["offset"]) != (
                "solid",
                "2px",
                "4px",
            ):
                failures.append(
                    f"{theme}: the focus outline is {reading['style']} "
                    f"{reading['width']} at offset {reading['offset']}"
                )
            if (
                min(reading["left"], reading["right"], reading["bottom"])
                < _RING_PX - 0.5
            ):
                failures.append(
                    f"{theme}: the focus outline is clipped by the grid box"
                )
            ratios.append(
                _contrast_ratio(_rgb(reading["colour"]), _rgb(reading["frame"]))
            )
    finally:
        page.evaluate(
            "(theme) => theme ? document.documentElement.setAttribute('data-theme', theme)"
            " : document.documentElement.removeAttribute('data-theme')",
            original,
        )
    print(
        f"[stream focus] outline vs frame min {min(ratios):.2f} max {max(ratios):.2f}"
    )
    if min(ratios) < _FLOOR_NON_TEXT:
        failures.append(
            f"the focus outline is {min(ratios):.2f}:1 against the frame, "
            f"floor {_FLOOR_NON_TEXT}"
        )
    return failures


def _blur_resize_failures(page, original: dict) -> list[str]:
    """A re-render with the stream focused leaves no ring, panel or focus."""
    page.locator(_STREAM).focus()
    wait_for_settled(page)
    failures = []
    if page.evaluate(_READ_HOVER_JS, [_HOVER_RANK, 0])["rings"] != 1:
        failures.append("focusing the stream shows no column ring before the resize")
    page.set_viewport_size(_NARROW_VIEWPORT)
    page.locator(_GRID_MOBILE).wait_for(state="visible")
    page.set_viewport_size(original)
    page.locator(_GRID_DESKTOP).wait_for(state="visible")
    wait_for_settled(page)
    failures.extend(_cleared_after(page, "after a re-render with focus"))
    if page.evaluate(_ACTIVE_JS)["isStream"]:
        failures.append("the stream still has focus after a re-render")
    return failures


def check_stream_is_one_keyboard_tab_stop(page, base_url: str) -> list[str]:
    """Tab reaches the stream once, the arrow keys move week and layer, and
    a blur or a re-render clears what it showed."""
    job_id, _last_day = seed_stream_job()
    original = page.viewport_size
    try:
        _open_heatmap(page, base_url, job_id, _GRID_DESKTOP)
        page.mouse.move(*_OUTSIDE)
        failures = _tab_to_stream(page)
        if failures:
            return failures
        failures.extend(_outline_failures(page))
        failures.extend(_walk_failures(page))
        page.keyboard.press("Home")
        for _ in range(6):
            page.keyboard.press("ArrowRight")
        for _ in range(_ARTIST_COUNT + 1):
            page.keyboard.press("ArrowDown")
        failures.extend(_step_failures(page, 6, _ARTIST_COUNT, "dense week end"))
        _hover(page, _START_WEEK)
        page.mouse.move(*_OUTSIDE)
        page.keyboard.press("ArrowUp")
        failures.extend(
            _step_failures(page, 6, _ARTIST_COUNT - 1, "after pointer leave")
        )
        if page.evaluate(_STOPS_IN_STREAM_JS) != 1:
            failures.append("the stream holds more than one tab stop")
        # The sentinel is added only now: in flow, it would add height below
        # the stream and hide a clipped outline from the check above.
        page.evaluate(_ADD_SENTINEL_JS)
        # A further Tab leaves the stream for the sentinel, then Shift+Tab walks back.
        page.keyboard.press("Tab")
        if not page.evaluate(_ACTIVE_JS)["isSentinel"]:
            failures.append("a further Tab from the stream does not leave it")
        page.keyboard.press("Shift+Tab")
        page.keyboard.press("Shift+Tab")
        if not page.evaluate(_ACTIVE_JS)["isCell"]:
            failures.append(
                "Shift+Tab from the stream does not return to the grid cell"
            )
        failures.extend(_cleared_after(page, "after Shift+Tab left the stream"))
        page.locator(_STREAM).focus()
        page.locator(_STREAM).blur()
        failures.extend(_cleared_after(page, "after blur"))
        failures.extend(_blur_resize_failures(page, original))
    finally:
        page.evaluate(_REMOVE_SENTINEL_JS)
        page.set_viewport_size(original)
        jobs.delete(job_id)
    return failures


# Save image. The export is drawn by hand, so a stream the page shows can
# still be missing from the file; the file is read back pixel by pixel.
_EXPORT_SCALE = 2
_EXPORT_PAD = 28
#: The export puts the stream flush under the grid, as the page does, so the
#: canvas grows by exactly the stream's rounded CSS height times the export
#: scale (the header and grid heights are the same in both saves). One CSS
#: pixel of rounding, 1 * _EXPORT_SCALE = 2 px, is the whole allowance.
_HEIGHT_TOLERANCE = _EXPORT_SCALE
_JPEG_TOLERANCE = 12
_SAVE_BUTTON = "#heatmap-save-image"
_SAVED_WEEK = 30

#: Where in the stream (viewBox units, found by testing the layers' own
#: fills) to look in the saved file: the layer on the centre line at the
#: tallest week, and another named artist at its widest.
_PLAN_JS = """([theme, week]) => {
    const svg = document.querySelector('#stream-chart');
    const hooks = window.__scrobbleHeatmapTestHooks;
    const xs = svg.dataset.columns.split(' ').map(Number);
    const grid = svg.querySelector('line.stream-gridline');
    const centre = (Number(grid.getAttribute('y1')) + Number(grid.getAttribute('y2'))) / 2;
    const height = svg.viewBox.baseVal.height;
    const paths = Array.from(svg.querySelectorAll('path.stream-layer'));
    const fills = (path, x, y) => path.isPointInFill(new DOMPoint(x, y));
    const band = (path, x, step) => {
        let first = null;
        let last = null;
        for (let y = 0; y <= height; y += step) {
            if (fills(path, x, y)) {
                if (first === null) first = y;
                last = y;
            }
        }
        return first === null ? null : { first, last };
    };
    const extent = (x) => {
        let first = null;
        let last = null;
        for (let y = 0; y <= height; y += 1) {
            if (paths.some((p) => fills(p, x, y))) {
                if (first === null) first = y;
                last = y;
            }
        }
        return first === null ? 0 : last - first;
    };
    const extents = xs.map(extent);
    const tallest = extents.indexOf(Math.max(...extents));
    const x = xs[tallest];
    const onCentre = paths.find((p) => fills(p, x, centre))
        || paths.find((p) => band(p, x, 1));
    const featured = paths.find((p) => p !== onCentre);
    const widths = xs.map((wx) => {
        const b = band(featured, wx, 0.5);
        return b ? b.last - b.first : 0;
    });
    const widest = widths.indexOf(Math.max(...widths));
    const mid = (path, px) => {
        const b = band(path, px, 0.25);
        return (b.first + b.last) / 2;
    };
    const rank = onCentre.dataset.rank;
    // Find an exposed halo margin, not its artist-covered geometric centre.
    const halo = svg.querySelector('.stream-halo');
    let margin = null;
    for (const wx of xs) {
        let start = null;
        for (let y = 0; y <= height + 0.5; y += 0.5) {
            const exposed = y <= height && fills(halo, wx, y)
                && !paths.some(path => fills(path, wx, y));
            if (exposed && start === null) start = y;
            if (!exposed && start !== null) {
                const width = y - start;
                if (!margin || width > margin.width) margin = { x: wx, y: start + width / 2, width };
                start = null;
            }
        }
    }
    if (!margin || margin.width < 5) throw new Error('No exposed halo margin for export probe');
    const surface = getComputedStyle(document.querySelector('#heatmap-result-frame'))
        .getPropertyValue('--heatmap-surface').trim();
    const expectedHalo = halo.getAttribute('visibility') === 'hidden'
        ? surface : halo.getAttribute('fill');
    const box = svg.getBoundingClientRect();
    return {
        cssHeight: Math.round(box.height),
        unitX: Math.round(box.width) / svg.viewBox.baseVal.width,
        unitY: Math.round(box.height) / height,
        label: svg.querySelector('.stream-section-label').textContent,
        column: { x: xs[week] * (Math.round(box.width) / svg.viewBox.baseVal.width),
                  step: (xs[1] - xs[0]) * (Math.round(box.width) / svg.viewBox.baseVal.width) },
        probes: [
            { name: 'halo margin', x: margin.x, y: margin.y, expected: expectedHalo },
            { name: 'layer ' + rank + ' at week ' + tallest, x, y: mid(onCentre, x),
              expected: hooks.layerColour(Number(rank), theme) },
            { name: 'layer ' + featured.dataset.rank + ' at week ' + widest, x: xs[widest],
              y: mid(featured, xs[widest]),
              expected: hooks.layerColour(Number(featured.dataset.rank), theme) },
        ],
    };
}"""

_READ_SAVED_JS = """async ([data, plan, scale, pad, streamHeight]) => {
    const image = new Image();
    image.src = 'data:image/jpeg;base64,' + data;
    await image.decode();
    const canvas = document.createElement('canvas');
    canvas.width = image.width;
    canvas.height = image.height;
    const context = canvas.getContext('2d');
    context.drawImage(image, 0, 0);
    const top = image.height / scale - pad - streamHeight;
    const pixels = plan ? plan.probes.map((p) => {
        const px = Math.round((pad + p.x * plan.unitX) * scale);
        const py = Math.round((top + p.y * plan.unitY) * scale);
        const d = context.getImageData(px - 1, py - 1, 3, 3).data;
        const sum = [0, 0, 0];
        for (let i = 0; i < d.length; i += 4) for (let c = 0; c < 3; c++) sum[c] += d[i + c] / 9;
        return sum;
    }) : [];
    return { width: image.width, height: image.height, pixels };
}"""

#: The largest per-channel difference between two saves of the same page over
#: the shown week's column (one column either side), the grid part above the
#: stream and the stream part, so a ring or a guide left in shows up.
_READ_COLUMN_DIFF_JS = """async ([rest, shown, plan, scale, pad, streamHeight]) => {
    const load = async (data) => {
        const image = new Image();
        image.src = 'data:image/jpeg;base64,' + data;
        await image.decode();
        const canvas = document.createElement('canvas');
        canvas.width = image.width;
        canvas.height = image.height;
        const context = canvas.getContext('2d');
        context.drawImage(image, 0, 0);
        return { image, context };
    };
    const a = await load(rest);
    const b = await load(shown);
    if (a.image.width !== b.image.width || a.image.height !== b.image.height) return null;
    const x0 = Math.round((pad + plan.column.x - plan.column.step) * scale);
    const x1 = Math.round((pad + plan.column.x + plan.column.step) * scale);
    const split = Math.round(b.image.height - (pad + streamHeight) * scale);
    const largest = (y0, y1) => {
        const w = x1 - x0;
        const da = a.context.getImageData(x0, y0, w, y1 - y0).data;
        const db = b.context.getImageData(x0, y0, w, y1 - y0).data;
        let max = 0;
        for (let i = 0; i < da.length; i++) {
            if (i % 4 !== 3) max = Math.max(max, Math.abs(da[i] - db[i]));
        }
        return max;
    };
    return { grid: largest(0, split), stream: largest(split, b.image.height) };
}"""


def _save_image(page) -> bytes:
    """Save for real; the click comes from script so the pointer stays put."""
    with page.expect_download(timeout=15_000) as downloaded:
        page.evaluate(f"() => document.querySelector('{_SAVE_BUTTON}').click()")
    return Path(downloaded.value.path()).read_bytes()


def _decode(page, image_bytes: bytes, plan=None, stream_height: int = 0) -> dict:
    return page.evaluate(
        _READ_SAVED_JS,
        [
            b64encode(image_bytes).decode("ascii"),
            plan,
            _EXPORT_SCALE,
            _EXPORT_PAD,
            stream_height,
        ],
    )


def _saved_image_failures(theme, plan, drawn, saved, baseline_height) -> list[str]:
    """Judge one theme's saved image against what the page drew and showed."""
    stream = (drawn or {}).get("stream")
    if not stream:
        return [f"the saved image records no stream in the {theme} theme"]
    failures = []
    if stream.get("label") != plan["label"]:
        failures.append(
            f"saved stream label is {stream.get('label')!r} in the {theme} theme, "
            f"the page says {plan['label']!r}"
        )
    if stream.get("height") != plan["cssHeight"]:
        failures.append(
            f"saved stream is {stream.get('height')} px tall in the {theme} theme, "
            f"the page draws it {plan['cssHeight']} px tall"
        )
    grown = saved["height"] - baseline_height
    wanted = plan["cssHeight"] * _EXPORT_SCALE
    if abs(grown - wanted) > _HEIGHT_TOLERANCE:
        failures.append(
            f"saved image grows by {grown} px with the stream in the {theme} theme, "
            f"expected {wanted} px (within {_HEIGHT_TOLERANCE} px)"
        )
    for probe, pixel in zip(plan["probes"], saved["pixels"], strict=True):
        want = _rgb(probe["expected"])
        if any(
            abs(got - w) > _JPEG_TOLERANCE for got, w in zip(pixel, want, strict=True)
        ):
            failures.append(
                f"saved image pixel in {probe['name']} is "
                f"{tuple(round(c) for c in pixel)} in the {theme} theme, "
                f"expected {tuple(round(c) for c in want)}"
            )
    return failures


def _column_failures(theme, diff) -> list[str]:
    """The shown week's column must look the same as in a save at rest."""
    if diff is None:
        return [f"the saved images differ in size once a week is shown ({theme})"]
    return [
        f"the shown week's column differs from the resting save in the {part} "
        f"part of the {theme} theme by {diff[part]} (of 255)"
        for part in ("grid", "stream")
        if diff[part] > _JPEG_TOLERANCE
    ]


def check_stream_is_in_saved_image(page, base_url: str) -> list[str]:
    """Save image carries the stream, at rest, on the frame surface."""
    failures = []
    with_payload, _last_day = seed_stream_job()
    without_payload, _last_day = seed_stream_job(payload=False)
    # The expected layer colour comes from the page's own ramp, which the
    # test seam exposes only when the flag is set before the script runs.
    probe = page.context.new_page()
    probe.add_init_script("window.__scrobbleHeatmapTestMode = true")
    try:
        _open_heatmap(probe, base_url, without_payload, _GRID_DESKTOP)
        baseline_height = _decode(probe, _save_image(probe))["height"]
        for theme in ("dark", "light"):
            _open_heatmap(probe, base_url, with_payload, _GRID_DESKTOP)
            probe.evaluate(SET_THEME_EXPRESSION, theme)
            wait_for_settled(probe)
            for state in ("on", "off"):
                if state == "off":
                    probe.locator("#stream-context-toggle").click()
                plan = probe.evaluate(_PLAN_JS, [theme, _SAVED_WEEK])
                rest_bytes = _save_image(probe)
                # The live hover must not leak its ring, guide or dimming into the save.
                failures.extend(
                    _hover_failures(_hover(probe, _SAVED_WEEK), _SAVED_WEEK)
                )
                image_bytes = _save_image(probe)
                drawn = probe.evaluate("() => window.__scrobbleHeatmapDrawnHeader?.()")
                saved = _decode(
                    probe,
                    image_bytes,
                    plan,
                    ((drawn or {}).get("stream") or {}).get("height", 0),
                )
                label = f"{theme}, halo {state}"
                failures.extend(
                    _saved_image_failures(label, plan, drawn, saved, baseline_height)
                )
                diff = probe.evaluate(
                    _READ_COLUMN_DIFF_JS,
                    [
                        b64encode(rest_bytes).decode("ascii"),
                        b64encode(image_bytes).decode("ascii"),
                        plan,
                        _EXPORT_SCALE,
                        _EXPORT_PAD,
                        plan["cssHeight"],
                    ],
                )
                failures.extend(_column_failures(label, diff))
                probe.mouse.move(*_OUTSIDE)
                wait_for_settled(probe)
    finally:
        probe.close()
        jobs.delete(with_payload)
        jobs.delete(without_payload)
    return failures
