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
  it.

A second check, `check_heatmap_document_listeners_attach_once`, proves the
tooltip's document-level `scroll` and `touchend` listeners are attached once
per page, not once per render.
"""

from __future__ import annotations

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
    const style = getComputedStyle(el);
    return {
        ariaLabel: el.getAttribute('aria-label'),
        date: el.getAttribute('data-date'),
        count: el.getAttribute('data-count'),
        tabIndexAttr: el.getAttribute('tabindex'),
        outlineWidth: style.outlineWidth,
        outlineStyle: style.outlineStyle,
        outlineOffset: style.outlineOffset,
        outlineColor: style.outlineColor,
    };
}"""


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

        # Resolve --shell-accent's computed colour via a throwaway probe
        # element, so the assertion below compares computed rgb strings
        # (what the browser actually paints) rather than the raw custom
        # property text.
        accent_color = page.evaluate(
            """() => {
                const probe = document.createElement('div');
                probe.style.position = 'absolute';
                probe.style.visibility = 'hidden';
                probe.style.color = 'var(--shell-accent)';
                document.body.appendChild(probe);
                const rgb = getComputedStyle(probe).color;
                probe.remove();
                return rgb;
            }"""
        )

        if landed["outlineWidth"] != "2px":
            failures.append(
                "heatmap cell focus outline-width was "
                f"{landed['outlineWidth']!r}, expected '2px'"
            )
        if landed["outlineStyle"] != "solid":
            failures.append(
                "heatmap cell focus outline-style was "
                f"{landed['outlineStyle']!r}, expected 'solid'"
            )
        if landed["outlineOffset"] != "1px":
            failures.append(
                "heatmap cell focus outline-offset was "
                f"{landed['outlineOffset']!r}, expected '1px'"
            )
        if landed["outlineColor"] != accent_color:
            failures.append(
                "heatmap cell focus outline-color was "
                f"{landed['outlineColor']!r}, expected {accent_color!r} "
                "(computed --shell-accent)"
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
            page.evaluate("() => window.scrollTo(0, 0)")
            cell_locator = page.locator(f'.heatmap-cell[data-date="{landed_date}"]')
            cell_locator.evaluate("(el) => el.focus()")
            # Give the browser's own scroll-into-view and the tooltip's
            # requestAnimationFrame reposition a turn to settle, then let
            # its 0.15s CSS opacity transition finish.
            page.evaluate("() => new Promise((r) => requestAnimationFrame(r))")
            page.wait_for_timeout(250)
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
    finally:
        delete_job(job_id)
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
