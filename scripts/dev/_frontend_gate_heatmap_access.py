"""Heatmap grid cell keyboard accessibility check (F-B21-14).

A slice of the frontend gate (F-B21-51). Nothing but a mouse hover reached a
heatmap cell before this check existed: the ramp itself is sound, but a
sighted-but-mouseless reader, or a screen reader, got no equivalent of the
tooltip. This drives a real Tab key press and reads what actually receives
focus, because a class name on a `<rect>` says nothing about whether a
keyboard can reach it.
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


def check_heatmap_cells_are_keyboard_accessible(page, base_url: str) -> list[str]:
    """Tab reaches a heatmap cell whose aria-label and focus ring are real."""
    failures: list[str] = []
    job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    # A single-day range makes the "every .heatmap-cell carries tabindex=0"
    # audit vacuous (1 of 1 always passes): seed a 14-day range instead, with
    # one non-zero day so the aria-label assertion still exercises a real
    # count.
    from_date = "2025-01-01"
    to_date = "2025-01-14"
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
        page.locator("#heatmap-result-frame svg").wait_for(state="visible")
        page.locator("#heatmap-save-image").focus()

        landed = None
        for _ in range(_MAX_TAB_PRESSES):
            page.keyboard.press("Tab")
            landed = page.evaluate(
                """() => {
                    const el = document.activeElement;
                    if (!el || !el.classList.contains('heatmap-cell')) return null;
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
            )
            if landed:
                break

        if not landed:
            failures.append(
                "Tab never reaches a focusable heatmap cell "
                f"(gave up after {_MAX_TAB_PRESSES} presses)"
            )
            return failures

        expected_label = _expected_cell_label(landed["date"], int(landed["count"]))
        if landed["ariaLabel"] != expected_label:
            failures.append(
                f"heatmap cell aria-label was {landed['ariaLabel']!r}, "
                f"expected {expected_label!r}"
            )

        if landed["tabIndexAttr"] != "0":
            failures.append(
                'heatmap cell reached by Tab does not carry tabindex="0" '
                f"(was {landed['tabIndexAttr']!r})"
            )

        cell_tabindex_audit = page.evaluate(
            """() => {
                const cells = Array.from(document.querySelectorAll('.heatmap-cell'));
                const missing = cells.filter(
                    (c) => c.getAttribute('tabindex') !== '0'
                ).length;
                return {total: cells.length, missing};
            }"""
        )
        if cell_tabindex_audit["total"] <= 1:
            failures.append(
                "heatmap grid rendered only "
                f"{cell_tabindex_audit['total']} .heatmap-cell element(s); "
                "the tabindex audit needs more than one cell to be "
                "meaningful (seed a wider date range)"
            )
        if cell_tabindex_audit["missing"]:
            failures.append(
                f"{cell_tabindex_audit['missing']} of "
                f"{cell_tabindex_audit['total']} .heatmap-cell elements lack "
                'tabindex="0"'
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
    finally:
        delete_job(job_id)
    return failures
