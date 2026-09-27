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
    seeded_date = "2025-01-01"
    seeded_count = 5
    set_job_results(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": seeded_date,
            "to_date": seeded_date,
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
                    return {
                        ariaLabel: el.getAttribute('aria-label'),
                        date: el.getAttribute('data-date'),
                        count: el.getAttribute('data-count'),
                        outlineStyle: getComputedStyle(el).outlineStyle,
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
        if landed["outlineStyle"] == "none":
            failures.append(
                "heatmap cell reaches keyboard focus with no visible outline"
            )
    finally:
        delete_job(job_id)
    return failures
