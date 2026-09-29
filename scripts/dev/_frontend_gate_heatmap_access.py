"""Heatmap grid cell keyboard accessibility check (F-B21-14).

A slice of the frontend gate (F-B21-51). Nothing but a mouse hover reached a
heatmap cell before this check existed: the ramp itself is sound, but a
sighted-but-mouseless reader, or a screen reader, got no equivalent of the
tooltip. This drives a real Tab key press and reads what actually receives
focus, because a class name on a `<rect>` says nothing about whether a
keyboard can reach it.

This check also proves four later fixes:

* the SVG carries `role="group"`, not `role="img"`, in the browser's own
  accessibility tree -- an ARIA `img` prunes every presentational child, so
  a screen reader would never hear a cell's own `role="img"` +
  `aria-label` if the SVG kept that role. Proven through
  `Locator.aria_snapshot()`, the browser's computed tree, never
  `getAttribute`.
* the grid uses a roving tabindex (exactly one cell reachable by Tab, the
  arrow keys move it, one more Tab leaves the grid), not every cell at
  once.
* the arrow keys move spatially, by the rendered layout: on the desktop
  grid (one column per week) ArrowRight is 7 days on and ArrowDown the next
  day; on the mobile strip (row-major) ArrowRight is the next day. At an
  edge, focus stays put. The expected cell is read off the rendered `x`/`y`
  attributes, not recomputed from the step arithmetic under test.
* focusing an off-screen cell -- the mobile strip's own scroll, or a page
  scroll a focus jump causes -- repositions the tooltip instead of hiding
  it. The check records that a scroll event actually fired, so it cannot
  pass on a focus that scrolled nothing.

And the second review's fixes:

* the keyboard focus ring is read off painted pixels, never computed
  outline values: a 2px outline 1px outside an SVG `<rect>` held every
  computed value while later cells covered it and the SVG's edge clipped
  it. A screenshot must show `--shell-accent` on all four sides of the
  first, the last and an interior cell, and on none after a mouse click.
  The grid must still span its frame, so room made for the ring cannot
  shrink the cells.
* with Alt, Ctrl, Meta or Shift held, a grid key is left alone: not
  cancelled, focus unmoved (Alt+ArrowLeft is the browser's Back).
* a scroll never brings back the tooltip of a clicked cell the pointer has
  left.

A second check, `check_heatmap_document_listeners_attach_once`, proves the
tooltip's document-level `scroll` and `touchend` listeners are attached once
per page, not once per render. A third,
`check_heatmap_focus_survives_breakpoint`, proves a re-render across the
breakpoint gives focus back to the same day.
"""

from __future__ import annotations

import base64
import datetime

from scripts.dev._frontend_gate_shared import MIGRATED_PAGES
from scrobblescope.repositories import (
    create_job,
    delete_job,
    set_job_progress,
    set_job_results,
)

#: The heatmap path this check drives. Looked up rather than hard-coded a
#: second time, so a path that stops being migrated is caught here too.
HEATMAP_PATH = next(path for path in MIGRATED_PAGES if path == "/heatmap")

#: Bounded, because a cell that is never reached should fail fast rather than
#: hang tabbing through hundreds of grid cells.
_MAX_TAB_PRESSES = 5

#: Mirrors static/js/heatmap.js's own arrays exactly, so the expected string
#: below is computed independently of the code under test rather than by
#: re-reading its output.
_WEEKDAYS = (
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
)
_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

#: Reads the currently-focused heatmap cell, or null if focus is elsewhere.
_ACTIVE_CELL_JS = """() => {
    const el = document.activeElement;
    if (!el || !el.classList || !el.classList.contains('heatmap-cell')) {
        return null;
    }
    return {
        ariaLabel: el.getAttribute('aria-label'),
        date: el.getAttribute('data-date'),
        count: el.getAttribute('data-count'),
        tabIndexAttr: el.getAttribute('tabindex'),
    };
}"""

#: Resolves --shell-accent through a throwaway probe element, so the ring
#: is compared with the colour the browser paints, not the property's text.
_ACCENT_COLOUR_JS = """() => {
    const probe = document.createElement('div');
    probe.style.position = 'absolute';
    probe.style.visibility = 'hidden';
    probe.style.color = 'var(--shell-accent)';
    document.body.appendChild(probe);
    const rgb = getComputedStyle(probe).color;
    probe.remove();
    return rgb;
}"""

#: The four sides of a cell, in the order a failure names them.
_SIDES = ("top", "right", "bottom", "left")

#: How far past a cell's edge, in CSS pixels, the ring's paint is looked for;
#: how many points along each side are sampled; and how close, per 0-255
#: channel, a pixel must be to the accent to count as the ring.
_RING_REACH_PX = 5
_RING_SAMPLES_PER_SIDE = 5
_RING_COLOUR_TOLERANCE = 24

#: Reads a viewport screenshot (base64 PNG) back in the page and reports, per
#: side of the cell for `a.date`, the share of sample points along the side's
#: middle 60% that have an accent-coloured pixel within `a.reach` CSS pixels
#: outside the edge. Pixels, not styles: a ring a later cell covers, or the
#: SVG clips, scores 0 on that side whatever its computed outline says.
_RING_PAINT_JS = """async (a) => {
    const el = document.querySelector(
        '.heatmap-cell[data-date="' + a.date + '"]');
    if (!el) return null;
    const img = new Image();
    img.src = 'data:image/png;base64,' + a.png;
    await img.decode();
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d', {willReadFrequently: true});
    ctx.drawImage(img, 0, 0);
    const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    const swatch = document.createElement('canvas');
    swatch.width = 1;
    swatch.height = 1;
    const sctx = swatch.getContext('2d');
    sctx.fillStyle = a.accent;
    sctx.fillRect(0, 0, 1, 1);
    const accent = sctx.getImageData(0, 0, 1, 1).data;
    const scale = canvas.width / window.innerWidth;
    const isAccent = (x, y) => {
        const px = Math.floor(x * scale);
        const py = Math.floor(y * scale);
        if (px < 0 || py < 0 || px >= canvas.width || py >= canvas.height) {
            return false;
        }
        const i = (py * canvas.width + px) * 4;
        return [0, 1, 2].every(
            (c) => Math.abs(pixels[i + c] - accent[c]) <= a.tolerance);
    };
    const box = el.getBoundingClientRect();
    const sides = {
        top: (t, d) => [t, box.top - d],
        bottom: (t, d) => [t, box.bottom + d],
        left: (t, d) => [box.left - d, t],
        right: (t, d) => [box.right + d, t],
    };
    const result = {};
    Object.keys(sides).forEach((side) => {
        const horizontal = side === 'top' || side === 'bottom';
        const lo = horizontal ? box.left : box.top;
        const hi = horizontal ? box.right : box.bottom;
        let painted = 0;
        for (let i = 0; i < a.samples; i++) {
            const t = lo + (hi - lo) * (0.2 + 0.6 * i / (a.samples - 1));
            for (let d = 0.5; d <= a.reach; d += 0.5) {
                const [x, y] = sides[side](t, d);
                if (isAccent(x, y)) {
                    painted++;
                    break;
                }
            }
        }
        result[side] = painted / a.samples;
    });
    return result;
}"""


def _ring_coverage(page, date: str, accent: str) -> dict[str, float] | None:
    """Per side of the cell for `date`, the share of its samples showing the
    accent just outside its edge, read off a screenshot of the viewport."""
    page.evaluate(
        "(date) => document.querySelector('.heatmap-cell[data-date=\"' + date"
        " + '\"]').scrollIntoView({block: 'center', inline: 'nearest'})",
        date,
    )
    page.evaluate(
        "() => new Promise((r) => requestAnimationFrame("
        "() => requestAnimationFrame(r)))"
    )
    png = base64.b64encode(page.screenshot()).decode("ascii")
    return page.evaluate(
        _RING_PAINT_JS,
        {
            "png": png,
            "date": date,
            "accent": accent,
            "reach": _RING_REACH_PX,
            "samples": _RING_SAMPLES_PER_SIDE,
            "tolerance": _RING_COLOUR_TOLERANCE,
        },
    )


def _check_ring_painted(page, layout, accent: str, which: str, date: str) -> list[str]:
    """The keyboard-focused cell for `date` shows the ring on all four sides."""
    coverage = _ring_coverage(page, date, accent)
    if coverage is None:
        return [f"no heatmap cell for {date!r} to read the {which} cell's ring from"]
    missing = [side for side in _SIDES if coverage[side] < 1]
    if not missing:
        return []
    shares = ", ".join(f"{side} {coverage[side]:.0%}" for side in _SIDES)
    return [
        f"the keyboard focus ring round the {which} cell ({date!r}) [{layout}] "
        f"paints no {accent} pixel within {_RING_REACH_PX}px of its "
        f"{', '.join(missing)} edge(s) (samples painted: {shares}); a later "
        "cell or the SVG's edge is hiding it"
    ]


def _expected_cell_label(iso_date: str, count: int) -> str:
    """The exact string `cellAccessibleLabel` produces for one date/count.

    A Python mirror of `static/js/heatmap.js`'s `formatDateLong` and
    `cellAccessibleLabel`, so a regression in either JS function is visible
    here rather than compared against its own (possibly also broken) output.
    """
    year, month, day = (int(part) for part in iso_date.split("-"))
    weekday = _WEEKDAYS[datetime.date(year, month, day).isoweekday() % 7]
    count_str = (
        "No scrobbles"
        if count == 0
        else f"{count} scrobble" + ("" if count == 1 else "s")
    )
    return f"{weekday} {day} {_MONTHS[month - 1]} {year} -- {count_str}"


def _snapshot_root_role(snapshot: str) -> str | None:
    """The role token of an `aria_snapshot()` string's top-level node.

    `Locator.aria_snapshot()` renders `- role "name":`, but wraps the whole
    `role "name"` pair in a single quote when the name needs YAML escaping
    (any heatmap label does, since it embeds a colon) -- `- 'group "...":'`.
    Reads the role out of either form rather than a fixed prefix, so the
    escaping choice is not part of what this check asserts.
    """
    first_line = next(iter(snapshot.strip().splitlines()), "")
    token = first_line[2:] if first_line.startswith("- ") else first_line
    token = token.lstrip("'\"")
    return token.split(" ", 1)[0] or None


def _truncate_snapshot(snapshot: str, limit: int = 300) -> str:
    """The snapshot's first `limit` characters, for a readable failure line.

    A 500-day grid's `aria_snapshot()` is one line per cell; a failure that
    quoted it whole would bury the one line that matters.
    """
    if len(snapshot) <= limit:
        return snapshot
    return snapshot[:limit] + "...(truncated)"


#: The cell an arrow key should reach from the cell for `a.date`, read off the
#: rendered geometry: the nearest cell in the same row (Left/Right) or the
#: same column (Up/Down) in the key's direction, or the same date when there
#: is none (an edge). Independent of heatmap.js's step arithmetic.
_SPATIAL_NEIGHBOUR_JS = """(a) => {
    const cells = Array.from(document.querySelectorAll('.heatmap-cell')).map(
        (el) => ({
            date: el.getAttribute('data-date'),
            x: parseFloat(el.getAttribute('x')),
            y: parseFloat(el.getAttribute('y')),
        })
    );
    const here = cells.find((c) => c.date === a.date);
    if (!here) return null;
    const horizontal = a.key === 'ArrowLeft' || a.key === 'ArrowRight';
    const sign = a.key === 'ArrowRight' || a.key === 'ArrowDown' ? 1 : -1;
    let best = null;
    let bestDistance = Infinity;
    cells.forEach((c) => {
        const inLine = horizontal ? c.y === here.y : c.x === here.x;
        const distance = sign * (horizontal ? c.x - here.x : c.y - here.y);
        if (inLine && distance > 0 && distance < bestDistance) {
            best = c;
            bestDistance = distance;
        }
    });
    return best ? best.date : here.date;
}"""

#: Each arrow key probed from the most recent day's cell, and the key that
#: should bring focus back (None: the probe is an edge, nothing to undo).
_ARROW_PROBES = (
    ("ArrowLeft", "ArrowRight"),
    ("ArrowUp", "ArrowDown"),
    ("ArrowRight", None),
    ("ArrowDown", None),
)

#: The day shift each arrow key makes on the desktop grid, one column per
#: week. Stated here, apart from the spatial read, so the desktop result is
#: also pinned to calendar days (the review's finding 2: ArrowRight used to
#: move one day, down the column).
_DESKTOP_ARROW_DAYS = {"ArrowLeft": -7, "ArrowRight": 7, "ArrowUp": -1, "ArrowDown": 1}


def _days_between(from_iso: str, to_iso: str) -> int:
    """Signed day count from `from_iso` to `to_iso`."""
    start = datetime.date.fromisoformat(from_iso)
    return (datetime.date.fromisoformat(to_iso) - start).days


def _shift_iso_date(iso_date: str, days: int) -> str:
    """`iso_date` plus `days` (negative shifts back), as `YYYY-MM-DD`."""
    year, month, day = (int(part) for part in iso_date.split("-"))
    shifted = datetime.date(year, month, day) + datetime.timedelta(days=days)
    return shifted.isoformat()


def check_heatmap_cells_are_keyboard_accessible(page, base_url: str) -> list[str]:
    """Tab reaches one cell; arrow keys rove it; scroll never hides its tip."""
    failures: list[str] = []
    job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    # A single-day range makes the "exactly one cell carries tabindex=0"
    # audit vacuous (1 of 1 always passes): seed a wide range instead, with
    # one non-zero day so the aria-label assertion still exercises a real
    # count. The mobile strip packs 10-28 columns into its container
    # (MOBILE_MIN_COLUMNS/MOBILE_MAX_COLUMNS in heatmap.js), so it takes a
    # wide range -- 500 days, measured against the MOBILE viewport -- before
    # the strip's own height passes the viewport's, which is what the A3
    # scroll/tooltip assertion below needs: on a shorter range every cell is
    # already on screen and that assertion is vacuous.
    from_date = "2025-01-01"
    to_date = _shift_iso_date(from_date, 499)
    seeded_date = "2025-01-01"
    seeded_count = 5
    set_job_results(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": from_date,
            "to_date": to_date,
            "total_scrobbles": seeded_count,
            "max_count": seeded_count,
            "daily_counts": {seeded_date: seeded_count},
        },
    )
    set_job_progress(job_id, progress=100, message="Done", error=False)
    try:
        page.goto(f"{base_url}{HEATMAP_PATH}?job_id={job_id}", wait_until="load")
        svg = page.locator("#heatmap-result-frame svg")
        svg.wait_for(state="visible")
        page.locator("#heatmap-save-image").focus()

        landed = None
        for _ in range(_MAX_TAB_PRESSES):
            page.keyboard.press("Tab")
            landed = page.evaluate(_ACTIVE_CELL_JS)
            if landed:
                break

        if not landed:
            failures.append(
                "Tab never reaches a focusable heatmap cell "
                f"(gave up after {_MAX_TAB_PRESSES} presses)"
            )
            return failures

        landed_date = landed["date"]
        expected_label = _expected_cell_label(landed_date, int(landed["count"]))
        if landed["ariaLabel"] != expected_label:
            failures.append(
                f"heatmap cell aria-label was {landed['ariaLabel']!r}, "
                f"expected {expected_label!r}"
            )
        if landed_date != to_date:
            failures.append(
                "Tab landed on the cell for "
                f"{landed_date!r}, expected the most recent day in range "
                f"({to_date!r}) to be the grid's one Tab stop"
            )

        # -- A1: the accessibility tree, not getAttribute. --------------
        # role="img" on the SVG would prune every presentational child, so
        # a screen reader would never hear a cell's own role="img" +
        # aria-label. Read what the browser actually computed. A Playwright
        # failure here is a check-level fault, not a result to report:
        # `_run_check` (frontend_gate.py) already reports an uncaught
        # exception as its own failure line.
        svg_snapshot = svg.aria_snapshot()
        svg_role = _snapshot_root_role(svg_snapshot)
        snapshot_head = _truncate_snapshot(svg_snapshot)
        if svg_role != "group":
            failures.append(
                "the heatmap SVG's computed accessibility role is "
                f"{svg_role!r}, expected 'group' (snapshot starts: "
                f"{snapshot_head!r})"
            )
        if f'img "{expected_label}"' not in svg_snapshot:
            failures.append(
                "the focused cell's own accessible name is missing from "
                "the SVG's accessibility tree (snapshot starts: "
                f"{snapshot_head!r}), expected an img node named "
                f"{expected_label!r}"
            )

        # -- A2: roving tabindex, not every cell at once. ----------------
        if landed["tabIndexAttr"] != "0":
            failures.append(
                'heatmap cell reached by Tab does not carry tabindex="0" '
                f"(was {landed['tabIndexAttr']!r})"
            )

        roving_audit = page.evaluate(
            """() => {
                const cells = Array.from(document.querySelectorAll('.heatmap-cell'));
                const zeroTabindex = cells.filter(
                    (c) => c.getAttribute('tabindex') === '0'
                ).length;
                return {total: cells.length, zeroTabindex: zeroTabindex};
            }"""
        )
        if roving_audit["total"] <= 1:
            failures.append(
                "heatmap grid rendered only "
                f"{roving_audit['total']} .heatmap-cell element(s); the "
                "roving-tabindex audit needs more than one cell to be "
                "meaningful (seed a wider date range)"
            )
        if roving_audit["zeroTabindex"] != 1:
            failures.append(
                f"{roving_audit['zeroTabindex']} of {roving_audit['total']} "
                '.heatmap-cell elements carry tabindex="0"; exactly one '
                "should (a roving tabindex, not every cell at once)"
            )

        layout = svg.get_attribute("data-layout")
        failures.extend(_check_arrow_keys(page, layout, landed_date))

        accent_color = page.evaluate(_ACCENT_COLOUR_JS)
        ring_failures, interior_date = _check_ring_on_three_cells(
            page, layout, accent_color, landed_date, from_date
        )
        failures.extend(ring_failures)
        failures.extend(_check_grid_fills_frame(page, layout))
        failures.extend(_check_modifier_keys_left_alone(page, layout))

        page.keyboard.press("Tab")
        left_grid = page.evaluate(
            "() => { const el = document.activeElement; "
            "return !(el && el.classList && el.classList.contains('heatmap-cell')); }"
        )
        if not left_grid:
            failures.append(
                "the next Tab from a heatmap cell stayed inside the grid "
                "(a roving tabindex should cost exactly one Tab to leave)"
            )

        # -- L1: a focus that did not come from Tab/arrow keys (a mouse
        # click, or this programmatic el.focus()) must move the roving Tab
        # stop too, else Tab-out-and-back lands on the stale stop instead of
        # the cell a user just focused. -----------------------------------
        first_cell_locator = page.locator(f'.heatmap-cell[data-date="{from_date}"]')
        first_cell_locator.evaluate("(el) => el.focus()")
        first_cell_tabindex = page.evaluate(
            "(date) => { const el = document.querySelector("
            "'.heatmap-cell[data-date=\"' + date + '\"]'); "
            "return el ? el.getAttribute('tabindex') : null; }",
            from_date,
        )
        if first_cell_tabindex != "0":
            failures.append(
                "focusing a non-stop heatmap cell (e.g. a mouse click) did "
                "not move the roving Tab stop to it "
                f"(tabindex was {first_cell_tabindex!r}, expected '0')"
            )
        else:
            page.keyboard.press("Tab")
            page.keyboard.press("Shift+Tab")
            returned = page.evaluate(_ACTIVE_CELL_JS)
            if not returned or returned["date"] != from_date:
                failures.append(
                    "Tab away and Shift+Tab back after focusing a non-stop "
                    f"cell did not return focus to {from_date!r} (landed on "
                    f"{returned['date'] if returned else None!r}); the "
                    "roving Tab stop was not updated by the programmatic "
                    "focus"
                )

        # -- A3: a scroll while a cell is focused repositions the tooltip,
        # rather than hiding it, on the profile where a focused cell can
        # need to scroll into view (the mobile strip). ------------------
        if layout == "mobile":
            page.evaluate(
                "() => { if (document.activeElement) document.activeElement.blur(); }"
            )
            # Scroll away from wherever the earlier Tab/arrow-key traffic
            # left the viewport, to the opposite end of the page, so
            # re-focusing the cell below is guaranteed to actually move the
            # scroll position (a same-position "scroll" never fires a
            # scroll event at all, which would make this assertion
            # vacuous).
            page.evaluate(_SCROLL_COUNTER_JS)
            page.evaluate("() => window.scrollTo(0, 0)")
            # Let scrollTo's own scroll event land before the count starts.
            page.evaluate(_TWO_FRAMES_JS)
            scroll_before = page.evaluate(_SCROLL_RESET_JS)
            cell_locator = page.locator(f'.heatmap-cell[data-date="{landed_date}"]')
            cell_locator.evaluate("(el) => el.focus()")
            # Give the browser's own scroll-into-view and the tooltip's
            # requestAnimationFrame reposition a turn to settle, then let
            # its 0.15s CSS opacity transition finish.
            page.evaluate("() => new Promise((r) => requestAnimationFrame(r))")
            page.wait_for_timeout(250)
            scroll_after = page.evaluate(_SCROLL_READ_JS)
            if scroll_after["events"] == 0:
                failures.append(
                    "focusing the off-screen cell scrolled nothing (no scroll "
                    f"event fired; page scrollY {scroll_before['y']} -> "
                    f"{scroll_after['y']}), so the tooltip assertion below "
                    "proves nothing; seed a range whose strip is taller than "
                    "the viewport"
                )
            tooltip_state = page.evaluate(
                """() => {
                    const tt = document.querySelector('.heatmap-tooltip');
                    if (!tt) return null;
                    return {
                        opacity: getComputedStyle(tt).opacity,
                        text: tt.textContent,
                    };
                }"""
            )
            if not tooltip_state:
                failures.append(
                    "no .heatmap-tooltip element exists after focusing an "
                    "off-screen cell"
                )
            else:
                if tooltip_state["opacity"] != "1":
                    failures.append(
                        "the tooltip was hidden (computed opacity "
                        f"{tooltip_state['opacity']!r}) after a scroll "
                        "brought the focused cell into view; a scroll "
                        "while a heatmap cell is focused should reposition "
                        "the tooltip, not hide it"
                    )
                if tooltip_state["text"] != expected_label:
                    failures.append(
                        "the tooltip visible after the scroll read "
                        f"{tooltip_state['text']!r}, expected "
                        f"{expected_label!r}"
                    )

        # Last, because a click ends :focus-visible for every scripted
        # focus after it (docs/agents/ui-accessibility.md item 4).
        if interior_date:
            failures.extend(
                _check_clicked_cell(page, layout, accent_color, interior_date)
            )
    finally:
        delete_job(job_id)
    return failures


#: Counts scroll events anywhere in the page (capture phase, so the mobile
#: strip's own scroll counts too). Installed once per page.
_SCROLL_COUNTER_JS = """() => {
    if (window.__heatmapScrollEvents === undefined) {
        document.addEventListener('scroll', () => {
            window.__heatmapScrollEvents += 1;
        }, true);
    }
    window.__heatmapScrollEvents = 0;
}"""
_SCROLL_RESET_JS = """() => {
    window.__heatmapScrollEvents = 0;
    return {y: window.scrollY};
}"""
_SCROLL_READ_JS = "() => ({events: window.__heatmapScrollEvents, y: window.scrollY})"
_TWO_FRAMES_JS = (
    "() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
)

#: The tooltip's state: shown (its `visible` class) and the focused cell's
#: date, or null when focus is not on a cell.
_TOOLTIP_AND_FOCUS_JS = """() => {
    const tt = document.querySelector('.heatmap-tooltip');
    const el = document.activeElement;
    return {
        shown: !!(tt && tt.classList.contains('visible')),
        focused: el && el.classList && el.classList.contains('heatmap-cell')
            ? el.getAttribute('data-date') : null,
    };
}"""

#: How far, in CSS pixels, the grid may sit inside the edges named below.
_GRID_EDGE_TOLERANCE_PX = 0.5

#: The rendered cells' outer edges against the frame's content box, and one
#: rendered gap between two neighbouring columns.
_GRID_EDGES_JS = """() => {
    const frame = document.querySelector('#heatmap-result-frame');
    const box = frame.getBoundingClientRect();
    const style = getComputedStyle(frame);
    const contentLeft = box.left + parseFloat(style.borderLeftWidth)
        + parseFloat(style.paddingLeft);
    const contentRight = box.right - parseFloat(style.borderRightWidth)
        - parseFloat(style.paddingRight);
    const cells = Array.from(document.querySelectorAll('.heatmap-cell'))
        .map((c) => c.getBoundingClientRect());
    const lefts = Array.from(new Set(cells.map((c) => c.left)))
        .sort((a, b) => a - b);
    return {
        leftInset: Math.min(...cells.map((c) => c.left)) - contentLeft,
        rightInset: contentRight - Math.max(...cells.map((c) => c.right)),
        gap: lefts.length > 1 ? lefts[1] - lefts[0] - cells[0].width : 0,
    };
}"""


def _check_grid_fills_frame(page, layout) -> list[str]:
    """The grid spans the frame: its last column ends one cell gap (the
    grid's own trailing gap) from the frame's content edge, and on the mobile
    strip its first column starts on that edge, level with the KPI text.

    A focus-ring given room inside the SVG's viewBox shrank every cell and
    pulled the grid 3-4px in from both edges; every ring check still passed.
    """
    edges = page.evaluate(_GRID_EDGES_JS)
    failures: list[str] = []
    right_limit = edges["gap"] + _GRID_EDGE_TOLERANCE_PX
    if edges["rightInset"] > right_limit:
        failures.append(
            f"the heatmap grid [{layout}] ends {edges['rightInset']:.1f}px short "
            "of the frame's content edge, expected at most one cell gap "
            f"({edges['gap']:.1f}px) + {_GRID_EDGE_TOLERANCE_PX}px: something "
            "shrank the grid inside its frame"
        )
    if layout == "mobile" and abs(edges["leftInset"]) > _GRID_EDGE_TOLERANCE_PX:
        failures.append(
            f"the heatmap strip [{layout}] starts {edges['leftInset']:.1f}px in "
            "from the frame's content edge, expected 0 (level with the KPI "
            "text above it): something shrank the grid inside its frame"
        )
    return failures


def _check_ring_on_three_cells(
    page, layout, accent: str, last_date: str, first_date: str
) -> tuple[list[str], str | None]:
    """The ring shows whole round the last cell (the Tab stop), the first
    cell and an interior one, each reached by keyboard. Returns the failures
    and the interior cell's date; leaves focus on the last cell."""
    failures = _check_ring_painted(page, layout, accent, "last", last_date)
    page.keyboard.press("Home")
    first = page.evaluate(_ACTIVE_CELL_JS)
    if not first or first["date"] != first_date:
        failures.append(
            f"Home [{layout}] moved focus to "
            f"{first['date'] if first else None!r}, expected the first "
            f"cell {first_date!r}"
        )
        return failures, None
    failures.extend(_check_ring_painted(page, layout, accent, "first", first_date))
    # One right and one down from the first cell has a neighbour on every
    # side in both layouts.
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowDown")
    interior = page.evaluate(_ACTIVE_CELL_JS)
    interior_date = interior["date"] if interior else None
    if interior_date in (None, first_date):
        failures.append(
            f"ArrowRight then ArrowDown [{layout}] from the first cell left "
            f"focus on {interior_date!r}; no interior cell to read a ring from"
        )
        interior_date = None
    else:
        failures.extend(
            _check_ring_painted(page, layout, accent, "interior", interior_date)
        )
    page.keyboard.press("End")
    return failures, interior_date


#: With a modifier held, each key is dispatched to the focused cell; reports
#: every one the grid cancelled or moved focus on, and puts focus back.
_MODIFIER_KEYS_JS = """() => {
    const el = document.activeElement;
    const taken = [];
    ['altKey', 'ctrlKey', 'metaKey', 'shiftKey'].forEach((modifier) => {
        ['ArrowLeft', 'ArrowUp', 'Home', 'End'].forEach((key) => {
            const init = {key: key, bubbles: true, cancelable: true};
            init[modifier] = true;
            const event = new KeyboardEvent('keydown', init);
            el.dispatchEvent(event);
            const now = document.activeElement;
            if (event.defaultPrevented || now !== el) {
                taken.push(modifier.replace('Key', '') + '+' + key
                    + (event.defaultPrevented ? ' cancelled' : '')
                    + (now !== el ? ' moved focus' : ''));
                el.focus();
            }
        });
    });
    return taken;
}"""


def _check_modifier_keys_left_alone(page, layout) -> list[str]:
    """With Alt, Ctrl, Meta or Shift held, a grid key is not cancelled and
    focus stays put: Alt+ArrowLeft is Back, Ctrl+Home the top of the page.

    Dispatched as synthetic events, which the browser never acts on, so an
    uncancelled Alt+ArrowLeft does not navigate the gate's page away.
    """
    taken = page.evaluate(_MODIFIER_KEYS_JS)
    if not taken:
        return []
    return [
        f"the heatmap grid [{layout}] took browser shortcuts it should leave "
        f"alone: {', '.join(taken)}"
    ]


def _check_clicked_cell(page, layout, accent: str, date: str) -> list[str]:
    """A mouse click focuses a cell but draws no ring, and once the pointer
    leaves, a scroll does not bring its tooltip back."""
    failures: list[str] = []
    page.locator(f'.heatmap-cell[data-date="{date}"]').click()
    coverage = _ring_coverage(page, date, accent)
    painted = [side for side in _SIDES if coverage and coverage[side] > 0]
    if painted:
        failures.append(
            f"a mouse click on the cell {date!r} [{layout}] drew the focus "
            f"ring on its {', '.join(painted)} edge(s); the ring is for "
            "keyboard focus only (:focus-visible)"
        )
    page.mouse.move(0, 0)
    page.wait_for_timeout(250)
    before = page.evaluate(_TOOLTIP_AND_FOCUS_JS)
    if before["focused"] != date or before["shown"]:
        failures.append(
            f"after clicking {date!r} and moving the pointer away [{layout}], "
            f"focus was on {before['focused']!r} and the tooltip "
            f"{'shown' if before['shown'] else 'hidden'}; expected the cell "
            "focused and its tooltip hidden, so the scroll probe cannot run"
        )
        return failures
    page.evaluate("() => document.dispatchEvent(new Event('scroll'))")
    page.evaluate(_TWO_FRAMES_JS)
    after = page.evaluate(_TOOLTIP_AND_FOCUS_JS)
    if after["shown"]:
        failures.append(
            f"a scroll brought back the tooltip of the clicked cell {date!r} "
            f"[{layout}] after the pointer had left and hidden it; a scroll "
            "only repositions a tooltip already on show"
        )
    return failures


def _check_arrow_keys(page, layout: str | None, landed_date: str) -> list[str]:
    """Each arrow key from the most recent day's cell reaches its spatial
    neighbour (or stays put at an edge), moves the roving Tab stop with it,
    and its opposite key brings focus back. Leaves focus on `landed_date`."""
    failures: list[str] = []
    landed_cell = page.locator(f'.heatmap-cell[data-date="{landed_date}"]')
    for key, back_key in _ARROW_PROBES:
        expected = page.evaluate(
            _SPATIAL_NEIGHBOUR_JS, {"date": landed_date, "key": key}
        )
        if layout == "desktop" and expected != landed_date:
            days = _days_between(landed_date, expected)
            if days != _DESKTOP_ARROW_DAYS[key]:
                failures.append(
                    f"the desktop grid's rendered {key} neighbour of "
                    f"{landed_date!r} is {days} day(s) away, expected "
                    f"{_DESKTOP_ARROW_DAYS[key]} (one column per week)"
                )
        page.keyboard.press(key)
        moved = page.evaluate(_ACTIVE_CELL_JS)
        moved_date = moved["date"] if moved else None
        if moved_date != expected:
            edge = " (an edge: stay put)" if expected == landed_date else ""
            failures.append(
                f"{key} [{layout}] from {landed_date!r} moved focus to "
                f"{moved_date!r}, expected its spatial neighbour "
                f"{expected!r}{edge}"
            )
            landed_cell.evaluate("(el) => el.focus()")
            continue
        if expected == landed_date:
            continue
        if moved["tabIndexAttr"] != "0":
            failures.append(
                f"{key} moved focus but the new cell does not carry "
                f'tabindex="0" (was {moved["tabIndexAttr"]!r})'
            )
        previous_tabindex = landed_cell.get_attribute("tabindex")
        if previous_tabindex != "-1":
            failures.append(
                f"{key} moved focus but the previously-focused cell still "
                f'carries tabindex={previous_tabindex!r} instead of "-1"'
            )
        page.keyboard.press(back_key)
        back = page.evaluate(_ACTIVE_CELL_JS)
        if not back or back["date"] != landed_date:
            failures.append(
                f"{back_key} [{layout}] from {expected!r} did not move focus "
                f"back to {landed_date!r}; landed on "
                f"{back['date'] if back else None!r}"
            )
            landed_cell.evaluate("(el) => el.focus()")
    return failures


#: Installed before heatmap.js runs: counts the `scroll` and `touchend`
#: listeners heatmap.js itself keeps on `document` (added minus removed,
#: matched by listener and capture flag, as the DOM matches them). A stack
#: that names heatmap.js tells its listeners from any other script's.
_DOCUMENT_LISTENER_SPY_JS = """(() => {
    const live = [];
    const capture = (opts) =>
        typeof opts === 'boolean' ? opts : !!(opts && opts.capture);
    const add = document.addEventListener;
    const remove = document.removeEventListener;
    document.addEventListener = function (type, fn, opts) {
        const stack = new Error().stack || '';
        if ((type === 'scroll' || type === 'touchend')
                && /heatmap\\.js/.test(stack)) {
            const c = capture(opts);
            if (!live.some((e) => e.type === type && e.fn === fn && e.c === c)) {
                live.push({type: type, fn: fn, c: c});
            }
        }
        return add.call(this, type, fn, opts);
    };
    document.removeEventListener = function (type, fn, opts) {
        const c = capture(opts);
        const i = live.findIndex((e) => e.type === type && e.fn === fn && e.c === c);
        if (i >= 0) live.splice(i, 1);
        return remove.call(this, type, fn, opts);
    };
    window.__heatmapDocumentListenerCounts = () => ({
        scroll: live.filter((e) => e.type === 'scroll').length,
        touchend: live.filter((e) => e.type === 'touchend').length,
    });
})();"""

#: Either side of heatmap.js's MOBILE_MAX_WIDTH (860px) breakpoint; each
#: crossing re-renders the grid, as each new search does.
_WIDE_VIEWPORT = {"width": 1280, "height": 720}
_NARROW_VIEWPORT = {"width": 390, "height": 844}


def check_heatmap_document_listeners_attach_once(page, base_url: str) -> list[str]:
    """Three renders leave one `scroll` and one `touchend` listener on
    `document` from heatmap.js, not one pair per render (the review's
    finding 4: each pair also held its render's cells and detached SVG).

    Runs on its own page in the check's context, so the listener spy it
    installs, and the viewport it resizes, end with this check.
    """
    failures: list[str] = []
    job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    set_job_results(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": "2025-01-01",
            "to_date": "2025-03-01",
            "total_scrobbles": 3,
            "max_count": 3,
            "daily_counts": {"2025-01-01": 3},
        },
    )
    set_job_progress(job_id, progress=100, message="Done", error=False)
    probe = page.context.new_page()
    try:
        probe.set_viewport_size(_WIDE_VIEWPORT)
        probe.add_init_script(_DOCUMENT_LISTENER_SPY_JS)
        probe.goto(f"{base_url}{HEATMAP_PATH}?job_id={job_id}", wait_until="load")
        frame_svg = "#heatmap-result-frame svg"
        for viewport, layout in (
            (_WIDE_VIEWPORT, "desktop"),
            (_NARROW_VIEWPORT, "mobile"),
            (_WIDE_VIEWPORT, "desktop"),
        ):
            probe.set_viewport_size(viewport)
            probe.locator(f'{frame_svg}[data-layout="{layout}"]').wait_for(
                state="visible"
            )
        counts = probe.evaluate("() => window.__heatmapDocumentListenerCounts()")
        for event_type in ("scroll", "touchend"):
            if counts[event_type] != 1:
                failures.append(
                    f"after three heatmap renders, heatmap.js holds "
                    f"{counts[event_type]} document {event_type!r} "
                    "listener(s), expected exactly 1 (attach once, not once "
                    "per render)"
                )
    finally:
        probe.close()
        delete_job(job_id)
    return failures


#: The focused cell's date, how many cells are Tab stops, and that date's
#: own tabindex.
_FOCUS_AND_TAB_STOP_JS = """() => {
    const el = document.activeElement;
    const cells = Array.from(document.querySelectorAll('.heatmap-cell'));
    return {
        focused: el && el.classList && el.classList.contains('heatmap-cell')
            ? el.getAttribute('data-date') : null,
        stops: cells.filter((c) => c.getAttribute('tabindex') === '0')
            .map((c) => c.getAttribute('data-date')),
    };
}"""


def check_heatmap_focus_survives_breakpoint(page, base_url: str) -> list[str]:
    """A re-render across the breakpoint gives focus back to the same day.

    The re-render replaces every cell, so a focused cell was destroyed, focus
    fell to `<body>` and the Tab stop reset to the last day. The cell for the
    same date must hold focus afterwards, be the one Tab stop, and still show
    the keyboard ring; with no cell focused, no cell may take focus.

    Runs on its own page, as the listener check does, so the viewport it
    resizes ends with this check.
    """
    failures: list[str] = []
    job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    # The window the app really renders (WINDOW_DAYS in heatmap.js): a short
    # range scales the desktop grid up several times over, and the ring's
    # paint with it, past where _check_ring_painted looks.
    set_job_results(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": "2025-01-01",
            "to_date": _shift_iso_date("2025-01-01", 364),
            "total_scrobbles": 3,
            "max_count": 3,
            "daily_counts": {"2025-01-01": 3},
        },
    )
    set_job_progress(job_id, progress=100, message="Done", error=False)
    probe = page.context.new_page()
    try:
        probe.set_viewport_size(_WIDE_VIEWPORT)
        probe.goto(f"{base_url}{HEATMAP_PATH}?job_id={job_id}", wait_until="load")
        frame_svg = "#heatmap-result-frame svg"
        probe.locator(f'{frame_svg}[data-layout="desktop"]').wait_for(state="visible")
        probe.locator("#heatmap-save-image").focus()
        landed = None
        for _ in range(_MAX_TAB_PRESSES):
            probe.keyboard.press("Tab")
            landed = probe.evaluate(_ACTIVE_CELL_JS)
            if landed:
                break
        if not landed:
            return [
                "Tab never reaches a heatmap cell, so the breakpoint probe cannot run"
            ]
        # Off the default Tab stop, so a reset to the last day shows.
        probe.keyboard.press("ArrowLeft")
        chosen = probe.evaluate(_ACTIVE_CELL_JS)
        if not chosen or chosen["date"] == landed["date"]:
            return ["ArrowLeft did not move off the last day; no probe cell"]
        date = chosen["date"]
        accent = probe.evaluate(_ACCENT_COLOUR_JS)

        for viewport, layout in (
            (_NARROW_VIEWPORT, "mobile"),
            (_WIDE_VIEWPORT, "desktop"),
        ):
            probe.set_viewport_size(viewport)
            probe.locator(f'{frame_svg}[data-layout="{layout}"]').wait_for(
                state="visible"
            )
            probe.evaluate(_TWO_FRAMES_JS)
            state = probe.evaluate(_FOCUS_AND_TAB_STOP_JS)
            if state["focused"] != date:
                failures.append(
                    f"after the re-render into the {layout} layout, focus was "
                    f"on {state['focused']!r}, expected the cell for {date!r}"
                )
                continue
            if state["stops"] != [date]:
                failures.append(
                    f"after the re-render into the {layout} layout, the Tab "
                    f"stop(s) were {state['stops']!r}, expected [{date!r}]"
                )
            failures.extend(
                _check_ring_painted(probe, layout, accent, "re-rendered", date)
            )

        probe.locator("#heatmap-save-image").focus()
        probe.set_viewport_size(_NARROW_VIEWPORT)
        probe.locator(f'{frame_svg}[data-layout="mobile"]').wait_for(state="visible")
        probe.evaluate(_TWO_FRAMES_JS)
        idle = probe.evaluate(_FOCUS_AND_TAB_STOP_JS)
        if idle["focused"] is not None:
            failures.append(
                "with no cell focused, the re-render put focus on the cell for "
                f"{idle['focused']!r}; nothing should take focus"
            )
    finally:
        probe.close()
        delete_job(job_id)
    return failures
