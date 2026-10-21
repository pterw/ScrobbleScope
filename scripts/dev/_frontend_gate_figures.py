"""The Results play count wears the heatmap's figure face.

A slice of the frontend gate (F-B21-51). The design gives numbers to Gotham,
the figure face (`--font-figure`), at Book weight and never bold, and the
heatmap's KPI values wear it. The Results table set its play count in the
serif beside them, and nothing could say so. This check reads what the browser
computed for a play count and for a KPI value, at every gate profile, and
requires the same family and weight. It also reads the KPI value against the
`--font-figure` token, so the pair cannot drift to the wrong face together.
At the mobile profile it also requires a four-digit count to stay inside its
cell, the guard for the narrow-screen sizing in results.css
(docs/design/RECONCILIATION.md section 26).

Computed `font-family` is the declared stack, not the face drawn. A kit family
that served no face is `check_fonts`' advisory, not this check's concern.
"""

from __future__ import annotations

from scrobblescope import jobs

#: The token the heatmap KPI value and the play count both resolve through.
FIGURE_FONT_PROPERTY = "--font-figure"

#: Book. The kit serves 300, 400 and 700; the KPI rule records why not 700.
FIGURE_WEIGHT = "400"

PLAYS_SELECTOR = "#results-table tbody tr .metric-val-plays"
KPI_SELECTOR = ".heatmap-kpi-value"

#: The seeded four-digit count's element, found by the row's own play count so
#: the check does not depend on the `data-digits` hook it guards.
FOUR_DIGIT_SELECTOR = (
    '#results-table tbody tr[data-play-count="8080"] .metric-val-plays'
)

#: Below this window width the Results page is on its narrow-screen layout.
MOBILE_BELOW_PX = 768

#: Sub-pixel rounding in a text box's edge is not an overflow.
FIT_TOLERANCE_PX = 0.5

#: Takes [selector, token]. Quotes and spaces are stripped from the family so
#: a stack compares however the engine spells it.
FACE_JS = """([selector, token]) => {
    const plain = value => value.replaceAll('"', '').replaceAll(' ', '');
    return {
        token: plain(getComputedStyle(document.documentElement)
            .getPropertyValue(token).trim()),
        faces: [...document.querySelectorAll(selector)].map(node => {
            const style = getComputedStyle(node);
            return {family: plain(style.fontFamily), weight: style.fontWeight};
        }),
    };
}"""

#: Play counts to seed: one four-digit count (the edge case the narrow-screen
#: sizing exists for), then shorter ones.
PLAY_COUNTS = (8080, 407, 12)

#: The smallest result the heatmap page renders KPI values from.
_HEATMAP_RESULT = {
    "username": "frontend-gate",
    "from_date": "2025-01-01",
    "to_date": "2025-01-05",
    "total_scrobbles": 4,
    "max_count": 4,
    "daily_counts": {"2025-01-01": 4, "2025-01-02": 0},
}


def figure_face_failures(plays: dict, kpi: dict, when: str) -> list[str]:
    """Judge a play-count reading against a KPI reading, both from `FACE_JS`.

    `when` names the state the play count was read in ("on load", "after
    switching sort"). The KPI value is the reference, so it must itself be the
    figure face at the figure weight.
    """
    if not kpi["faces"]:
        return ["heatmap renders no KPI value to compare the play count with"]
    if not plays["faces"]:
        return [f"results table renders no play count {when}"]
    reference = kpi["faces"][0]
    if reference["family"] != kpi["token"] or reference["weight"] != FIGURE_WEIGHT:
        return [
            f"heatmap KPI value is set in {reference['family']!r} at weight "
            f"{reference['weight']}, expected the figure face {kpi['token']!r} "
            f"at weight {FIGURE_WEIGHT}"
        ]
    failures = []
    seen = set()
    for face in plays["faces"]:
        key = (face["family"], face["weight"])
        if key in seen:
            continue
        seen.add(key)
        if face["family"] != reference["family"]:
            failures.append(
                f"play count {when} is set in {face['family']!r}, "
                f"the heatmap KPI value in {reference['family']!r}"
            )
        if face["weight"] != reference["weight"]:
            failures.append(
                f"play count {when} has font weight {face['weight']}, "
                f"the heatmap KPI value {reference['weight']}"
            )
    return failures


#: Takes a selector; reads the first match's right edge against the right
#: edge of its cell's content box (the cell's padding is room the text may not
#: use).
FIT_JS = """selector => {
    const node = document.querySelector(selector);
    if (!node) return null;
    const cell = node.closest('td');
    const style = getComputedStyle(cell);
    return {
        text: node.textContent.trim(),
        right: node.getBoundingClientRect().right,
        limit: cell.getBoundingClientRect().right
            - Number.parseFloat(style.paddingRight),
    };
}"""


def count_fit_failures(reading: dict | None, when: str) -> list[str]:
    """Judge a `FIT_JS` reading: the count's right edge stays in its cell."""
    if reading is None:
        return [f"results table renders no four-digit play count {when}"]
    overshoot = reading["right"] - reading["limit"]
    if overshoot > FIT_TOLERANCE_PX:
        return [
            f"play count {reading['text']} {when} ends {overshoot:.1f}px past "
            "the cell it sits in"
        ]
    return []


def _results_row(index: int, plays: int) -> dict:
    return {
        "artist": f"Artist {index}",
        "album": f"Album {index}",
        "play_count": plays,
        "play_time_seconds": 60,
        "play_time": "1m",
        "release_date": "2025-01-02",
    }


def check_results_play_count_uses_the_figure_face(page, base_url: str) -> list[str]:
    """A Results play count is set like a heatmap KPI value.

    At the mobile profile the four-digit count must also stay inside its cell.

    Reads the heatmap's KPI value first, then the Results page on load and
    again after the sort is switched to listening time and back, which makes
    results.js rebuild the cell (docs/agents/ui-accessibility.md item 6).
    """
    spotlight = "**/api/artist_spotlight?*"
    results_job = jobs.create(
        {"username": "gate", "year": 2025, "sort_mode": "playcount"}
    )
    heatmap_job = jobs.create({"username": "frontend-gate", "mode": "heatmap"})
    try:
        jobs.succeed(
            results_job,
            [_results_row(i, plays) for i, plays in enumerate(PLAY_COUNTS, 1)],
            "Done",
        )
        jobs.succeed(heatmap_job, _HEATMAP_RESULT, "Done")
        page.route(spotlight, lambda route: route.fulfill(json={}))

        page.goto(f"{base_url}/heatmap?job_id={heatmap_job}", wait_until="load")
        page.wait_for_selector(KPI_SELECTOR, state="visible")
        kpi = page.evaluate(FACE_JS, [KPI_SELECTOR, FIGURE_FONT_PROPERTY])

        page.goto(f"{base_url}/results?job_id={results_job}", wait_until="load")
        page.evaluate("async () => { await document.fonts.ready; }")
        narrow = page.viewport_size["width"] < MOBILE_BELOW_PX
        failures = figure_face_failures(
            page.evaluate(FACE_JS, [PLAYS_SELECTOR, FIGURE_FONT_PROPERTY]),
            kpi,
            "on load",
        )
        if narrow:
            failures.extend(
                count_fit_failures(
                    page.evaluate(FIT_JS, FOUR_DIGIT_SELECTOR), "on load"
                )
            )

        page.locator("#toggle-sort-playtime").click()
        page.locator("#toggle-sort-plays").click()
        failures.extend(
            figure_face_failures(
                page.evaluate(FACE_JS, [PLAYS_SELECTOR, FIGURE_FONT_PROPERTY]),
                kpi,
                "after switching sort",
            )
        )
        if narrow:
            failures.extend(
                count_fit_failures(
                    page.evaluate(FIT_JS, FOUR_DIGIT_SELECTOR), "after switching sort"
                )
            )
        return failures
    finally:
        try:
            page.unroute(spotlight)
        finally:
            jobs.delete(results_job)
            jobs.delete(heatmap_job)
