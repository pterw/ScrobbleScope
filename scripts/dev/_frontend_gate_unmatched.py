"""The unmatched report check: populated contract, disclosure, and width sweep.

A slice of the frontend gate (F-B21-51). The sweep exists because none of the
gate's viewport profiles lands between 1024px and the two-panel breakpoint,
which is how a 20-36px album title shipped at 1024px (owner ruling
2026-09-13).
"""

from __future__ import annotations

import json

from scrobblescope.repositories import add_job_unmatched, create_job, delete_job

#: Narrowest window at which two unmatched panels share a row. Below it each
#: panel takes the full width. Owner ruling, 2026-09-13: at 1024px two panels
#: left the album title 20-36px beside a Results-sized cover.
UNMATCHED_TWO_PANEL_MIN = 1280

#: Widths either side of the two-panel breakpoint, and the old breakpoint. None
#: of the gate's profiles lands here, which is how the 1024px defect shipped.
UNMATCHED_SWEEP_WIDTHS = (1024, UNMATCHED_TWO_PANEL_MIN - 1, UNMATCHED_TWO_PANEL_MIN)

#: Least width an album title may get beside its cover. At 1280px two panels
#: give 103-119px; the defect gave 20-36px.
UNMATCHED_MIN_TITLE_WIDTH = 96


def _unmatched_panel_width_sweep(page) -> list[str]:
    """Resize across the two-panel breakpoint and check the album title's room.

    Restores the original viewport before returning, so later checks on the
    same page are unaffected.
    """
    failures = []
    original = page.viewport_size
    try:
        for width in UNMATCHED_SWEEP_WIDTHS:
            page.set_viewport_size({"width": width, "height": original["height"]})
            # Two frames: one for layout, one for the scale ResizeObserver.
            page.evaluate(
                "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
            )
            sweep = page.evaluate(
                """() => ({
                    columns: getComputedStyle(document.querySelector('.unmatched-groups'))
                        .gridTemplateColumns.split(' ').length,
                    titles: [...document.querySelectorAll('.unmatched-group')].map(group =>
                        group.querySelector('tbody tr .album-info').getBoundingClientRect().width),
                })"""
            )
            expected_columns = 2 if width >= UNMATCHED_TWO_PANEL_MIN else 1
            if sweep["columns"] != expected_columns:
                failures.append(
                    f"unmatched report at {width}px has {sweep['columns']} panel "
                    f"columns, expected {expected_columns}"
                )
            narrowest = min(sweep["titles"])
            if narrowest < UNMATCHED_MIN_TITLE_WIDTH:
                failures.append(
                    f"unmatched album title at {width}px is {narrowest:.0f}px wide, "
                    f"expected at least {UNMATCHED_MIN_TITLE_WIDTH}px"
                )
    finally:
        page.set_viewport_size(original)
    return failures


def check_unmatched_report(page, base_url: str) -> list[str]:
    """Exercise the populated report contract and its ten-row disclosure."""
    job_id = create_job(
        {
            "username": "frontend-gate",
            "year": 2025,
            "sort_mode": "playcount",
            "release_scope": "same",
            "min_plays": 10,
            "min_tracks": 3,
            "limit_results": "all",
            "mode": "album",
        }
    )
    failures = []
    spotlight_requests = []

    def fulfill_spotlight(route):
        """Return deterministic portrait data without contacting Spotify."""
        spotlight_requests.append(route.request.url)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "name": "Missing Spotify Artist",
                    "artist_id": "artist-1",
                    "image_url": (
                        "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>"
                    ),
                    "spotify_url": "https://open.spotify.com/artist/artist-1",
                }
            ),
        )

    spotlight_pattern = "**/api/artist_spotlight?*"
    page.route(spotlight_pattern, fulfill_spotlight)
    try:
        add_job_unmatched(
            job_id,
            "below-threshold",
            {
                "album": "Older",
                "artist": "Lizzy McAlpine",
                "reason": (
                    "Played 7 times across 2 unique tracks; minimum is 10 plays "
                    "and 3 unique tracks"
                ),
                "reason_code": "below_threshold",
                "album_image": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>",
                "spotify_id": None,
                "play_count": 7,
                "track_count": 2,
                "failed_thresholds": ["plays", "tracks"],
                "min_plays": 10,
                "min_tracks": 3,
            },
        )
        play_counts = (5, 29, 11, 23, 7, 17, 13, 19, 3, 2, 27, 9)
        for index in range(1, 13):
            add_job_unmatched(
                job_id,
                f"scope-{index}",
                {
                    "album": f"Scope Album {index}",
                    "artist": f"Scope Artist {index}",
                    "reason": "Outside selected release scope",
                    "reason_code": "release_scope",
                    "album_image": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'/>",
                    "spotify_id": f"scope-album-{index}",
                    "provider": "spotify",
                    "album_url": f"https://open.spotify.com/album/scope-album-{index}",
                    "play_count": play_counts[index - 1],
                },
            )
        add_job_unmatched(
            job_id,
            "missing-spotify",
            {
                "album": "Missing Spotify Album",
                "artist": "Missing Spotify Artist",
                "reason": "No Spotify match",
                "reason_code": "no_spotify_match",
                "album_image": None,
                "spotify_id": None,
                "play_count": 7,
            },
        )

        page.goto(f"{base_url}/unmatched?job_id={job_id}", wait_until="load")
        groups = page.locator(".unmatched-group")
        if groups.count() != 3:
            failures.append(
                f"unmatched report rendered {groups.count()} reason groups instead of 3"
            )
            return failures

        scope_group = page.locator('[data-reason="release_scope"]')
        state = scope_group.evaluate(
            """node => {
                const rows = [...node.querySelectorAll('tbody tr')];
                const overflow = rows.filter(row => row.classList.contains('unmatched-overflow'));
                const button = node.querySelector('.unmatched-expander-btn');
                const count = node.querySelector('.unmatched-count');
                const page = document.querySelector('.unmatched-page');
                const grid = node.parentElement;
                const fixHint = node.querySelector('.unmatched-fix-hint');
                const root = getComputedStyle(document.documentElement);
                const headline = page.querySelector('h1');
                const username = page.querySelector('.unmatched-headline__user');
                const normalizeFont = value => value.replaceAll('"', '').replaceAll(' ', '');
                return {
                    rows: rows.length,
                    visibleRows: rows.filter(row => getComputedStyle(row).display !== 'none').length,
                    hiddenOverflow: overflow.filter(row => getComputedStyle(row).display === 'none').length,
                    buttonText: button?.textContent.trim(),
                    expanded: button?.getAttribute('aria-expanded'),
                    spotifyHref: node.querySelector('a[href*="open.spotify.com/album/"]')?.href,
                    plays: rows[0]?.querySelector('td:nth-child(3)')?.textContent.trim(),
                    countFont: normalizeFont(getComputedStyle(count).fontFamily),
                    figureFont: normalizeFont(root.getPropertyValue('--font-figure').trim()),
                    pageMaxWidth: getComputedStyle(page).maxWidth,
                    gridColumns: getComputedStyle(grid).gridTemplateColumns.split(' ').length,
                    scale: Number.parseFloat(getComputedStyle(page).getPropertyValue('--results-scale')),
                    reportOverflow: grid.scrollWidth - grid.clientWidth,
                    headingFirstTag: headline.parentElement.firstElementChild?.tagName,
                    usernameFontStyle: username ? getComputedStyle(username).fontStyle : null,
                    usernameMatchesHeadlineColor: username
                        ? getComputedStyle(username).color === getComputedStyle(headline).color
                        : false,
                    resultsStylesheet: [...document.styleSheets].some(sheet =>
                        sheet.href?.endsWith('/static/css/results.css')),
                    fixHint: fixHint?.textContent.trim(),
                    fixHintSize: getComputedStyle(fixHint).fontSize,
                    countLabelSize: getComputedStyle(node.querySelector('span.unmatched-label')).fontSize,
                    coarsePointer: matchMedia('(any-pointer: coarse)').matches,
                    controlShortSides: [...document.querySelectorAll(
                        '.results-toolbar-action, .unmatched-expander-btn, .unmatched-back-to-top-btn')]
                        .map(el => {
                            const r = el.getBoundingClientRect();
                            return Math.min(r.width, r.height);
                        }),
                    rowPadTop: Number.parseFloat(
                        getComputedStyle(rows[0].querySelector('td')).paddingTop),
                    rowPadBottom: Number.parseFloat(
                        getComputedStyle(rows[0].querySelector('td')).paddingBottom),
                    thWidths: [...node.querySelectorAll('thead th')]
                        .map(th => Number.parseFloat(getComputedStyle(th).width)),
                    // Compare the rendered extent of a cell's contents with the
                    // cell's own box. scrollWidth is not usable here: Chromium
                    // counts end padding into it, so content that is fully
                    // visible inside the padding would be reported as clipped.
                    clippedCells: [...document.querySelectorAll(
                        '.unmatched-table th, .unmatched-table td')]
                        .filter(cell => {
                            if (getComputedStyle(cell).display === 'none') return false;
                            const range = document.createRange();
                            range.selectNodeContents(cell);
                            const inner = range.getBoundingClientRect();
                            const outer = cell.getBoundingClientRect();
                            return inner.width > 0
                                && (inner.left < outer.left - 1 || inner.right > outer.right + 1);
                        })
                        .map(cell => cell.textContent.replaceAll(/\\s+/g, ' ').trim()
                            .slice(0, 40)),
                    docOverflow: document.documentElement.scrollWidth
                        - document.documentElement.clientWidth,
                    unsupportedWeights: [...node.querySelectorAll('*')]
                        .map(element => getComputedStyle(element).fontWeight)
                        .filter(weight => weight === '500' || weight === '600'),
                };
            }"""
        )
        expected = {
            "rows": 12,
            "visibleRows": 10,
            "hiddenOverflow": 2,
            "buttonText": "Show all 12 albums",
            "expanded": "false",
            "plays": "29",
            "pageMaxWidth": "1440px",
            # Two panels share a row from 1280px, never three: the 90rem page
            # cap holds a third track to about 448px, the width that made
            # three-up unreadable in the first place.
            "gridColumns": 2
            if page.viewport_size["width"] >= UNMATCHED_TWO_PANEL_MIN
            else 1,
            "headingFirstTag": "H1",
            "usernameFontStyle": "normal",
            "usernameMatchesHeadlineColor": True,
            "resultsStylesheet": True,
            "fixHint": 'Choose "All years (no filter)" on a new search to include these releases.',
            # Owner ruling, 2026-09-13 (F-B21-4 item 4): 12px, not the
            # README's 9px, for the fix hint and the per-panel count label.
            "fixHintSize": "12px",
            "countLabelSize": "12px",
        }
        for claim, wanted in expected.items():
            if state[claim] != wanted:
                failures.append(
                    f"unmatched report {claim} is {state[claim]!r}, expected {wanted!r}"
                )
        group_covers = page.locator(".unmatched-group").evaluate_all(
            """groups => groups.map(group => {
                const cover = group.querySelector('.unmatched-artwork');
                if (!cover) return null;
                const style = getComputedStyle(cover);
                return { width: style.width, height: style.height };
            })"""
        )
        # Geometry is compared numerically rather than as strings: row padding
        # follows the width-derived --results-scale, so an exact pixel string
        # would only hold at one window. Tolerance covers subpixel rounding.
        width = page.viewport_size["width"]
        scale = state["scale"] if width >= 768 else 1
        # The cover matches the Results row, and scales at every width.
        expected_cover = (64.0 if width < 768 else 72.0) * state["scale"]
        for index, cover in enumerate(group_covers):
            if cover is None:
                failures.append(f"unmatched group {index} renders no artwork container")
                continue
            cover_w = float(cover["width"].removesuffix("px"))
            cover_h = float(cover["height"].removesuffix("px"))
            if (
                abs(cover_w - expected_cover) > 0.75
                or abs(cover_h - expected_cover) > 0.75
            ):
                failures.append(
                    f"unmatched group {index} artwork is {cover_w:.1f}x{cover_h:.1f}px, "
                    f"expected {expected_cover:.1f}px"
                )

        # Row padding. It compiled to nothing once (`py-2.5`), leaving every row
        # with zero vertical padding above 768px while presence checks passed.
        expected_pad = 12.0 * scale
        for side in ("rowPadTop", "rowPadBottom"):
            if abs(state[side] - expected_pad) > 0.75:
                failures.append(
                    f"unmatched report {side} is {state[side]:.2f}px, "
                    f"expected {expected_pad:.2f}px"
                )

        # Column budget. Lost widths fall back to four equal columns under
        # `table-layout: fixed` and truncate silently, so assert the shape: the
        # album column leads and has room for a cover plus a title.
        th_widths = state["thWidths"]
        if len(th_widths) != 4:
            failures.append(
                f"unmatched table has {len(th_widths)} header cells, expected 4"
            )
        else:
            if max(th_widths) - min(th_widths) < 1:
                failures.append(
                    f"unmatched table columns are equal widths {th_widths!r}; "
                    "the column budget did not apply"
                )
            if th_widths[1] != max(th_widths) or th_widths[1] < 150:
                failures.append(
                    f"unmatched album column is {th_widths[1]:.1f}px of {th_widths!r}; "
                    "expected it to be the widest and at least 150px"
                )

        # Document-level overflow. The grid check below cannot see it: a header
        # row that refused to shrink scrolled the whole page at 768px and 1024px.
        if state["docOverflow"] > 1:
            failures.append(
                f"unmatched page scrolls horizontally by {state['docOverflow']!r}px"
            )

        # Cells keep `overflow: hidden`, so text that cannot wrap is cut without
        # an ellipsis or an error. The metric header shipped as "PLAYS / TRA" and
        # the threshold metric as "7 plays ..." while every other check passed.
        if state["clippedCells"]:
            failures.append(
                f"unmatched table clips cell content: {state['clippedCells']!r}"
            )

        if state["coarsePointer"]:
            small = [round(side, 1) for side in state["controlShortSides"] if side < 44]
            if small:
                failures.append(
                    f"unmatched report controls under 44px on a coarse pointer: {small!r}"
                )

        group_tops = page.locator(".unmatched-group").evaluate_all(
            "groups => groups.map(g => Math.round(g.getBoundingClientRect().top))"
        )
        if page.viewport_size["width"] >= UNMATCHED_TWO_PANEL_MIN:
            if len(group_tops) >= 2 and group_tops[0] != group_tops[1]:
                failures.append(
                    "unmatched reports are not arranged side-by-side on desktop"
                )
        else:
            if len(group_tops) >= 2 and group_tops[0] == group_tops[1]:
                failures.append(
                    "unmatched reports should wrap to single column on mobile"
                )

        if state["reportOverflow"] > 1:
            failures.append(
                f"unmatched report overflows horizontally by {state['reportOverflow']!r}px"
            )
        if state["scale"] < 1:
            failures.append(
                f"unmatched report has invalid Results scale {state['scale']!r}"
            )

        threshold_state = page.locator('[data-reason="below_threshold"]').evaluate(
            r"""node => ({
                rows: node.querySelectorAll('tbody tr').length,
                metric: node.querySelector('.unmatched-thresholds')?.textContent
                    .replaceAll(/\s+/g, ' ').trim(),
            })"""
        )
        if threshold_state != {"rows": 1, "metric": "7 plays / 2 tracks"}:
            failures.append(
                f"unmatched threshold row is incorrect: {threshold_state!r}"
            )
        if not (state["spotifyHref"] or "").endswith("/scope-album-2"):
            failures.append("unmatched report did not render the Spotify album link")
        if state["countFont"] != state["figureFont"]:
            failures.append(
                "unmatched report count does not use the figure typeface token"
            )
        if state["unsupportedWeights"]:
            failures.append("unmatched report renders unsupported 500/600 font weights")

        unmatched_portrait = page.locator(
            '[data-reason="no_spotify_match"] [data-artist-image]'
        )
        unmatched_portrait.scroll_into_view_if_needed()
        artist_image = unmatched_portrait.locator(".unmatched-artist-image")
        artist_image.wait_for(state="visible")
        portrait_state = unmatched_portrait.evaluate(
            """node => ({
                alt: node.querySelector('.unmatched-artist-image')?.alt,
                imageDisplay: getComputedStyle(node.querySelector('.unmatched-artist-image')).display,
                fallbackDisplay: getComputedStyle(node.querySelector('.unmatched-artwork-fallback')).display,
            })"""
        )
        if portrait_state != {
            "alt": "Missing Spotify Artist artist portrait",
            "imageDisplay": "block",
            "fallbackDisplay": "none",
        }:
            failures.append(
                "unmatched report artist portrait fallback is incorrect: "
                f"{portrait_state!r}"
            )
        if len(spotlight_requests) != 1 or "Missing%20Spotify%20Artist" not in (
            spotlight_requests[0] if spotlight_requests else ""
        ):
            failures.append(
                "unmatched report did not hydrate missing artwork once through "
                "/api/artist_spotlight"
            )

        button = scope_group.locator(".unmatched-expander-btn")
        button.click()
        expanded = scope_group.evaluate(
            """node => ({
                visibleRows: [...node.querySelectorAll('tbody tr')]
                    .filter(row => getComputedStyle(row).display !== 'none').length,
                buttonText: node.querySelector('.unmatched-expander-btn')?.textContent.trim(),
                expanded: node.querySelector('.unmatched-expander-btn')?.getAttribute('aria-expanded'),
            })"""
        )
        if expanded != {
            "visibleRows": 12,
            "buttonText": "Show fewer",
            "expanded": "true",
        }:
            failures.append(
                f"unmatched report expanded state is incorrect: {expanded!r}"
            )

        button.click()
        collapsed = scope_group.evaluate(
            """node => ({
                visibleRows: [...node.querySelectorAll('tbody tr')]
                    .filter(row => getComputedStyle(row).display !== 'none').length,
                expanded: node.querySelector('.unmatched-expander-btn')?.getAttribute('aria-expanded'),
            })"""
        )
        if collapsed != {"visibleRows": 10, "expanded": "false"}:
            failures.append(
                f"unmatched report collapsed state is incorrect: {collapsed!r}"
            )

        # Owner ruling, 2026-09-11: a 50-row reveal is too much, so the step is
        # 25. The route test pins the rendered attribute; this pins the value the
        # running script actually reads.
        step = button.get_attribute("data-step")
        if step != "25":
            failures.append(
                f"unmatched report expander step is {step!r}, expected '25'"
            )

        # Owner ruling, 2026-09-11: returning to the top must also collapse the
        # report, so the reader is not left under a table they had just padded
        # with rows. Expand first, so the collapse has something to undo.
        if scope_group.locator(".unmatched-back-to-top-btn").count():
            button.click()
            scope_group.locator(".unmatched-back-to-top-btn").click()
            collapsed_by_top = scope_group.evaluate(
                """node => ({
                    visibleRows: [...node.querySelectorAll('tbody tr')]
                        .filter(row => getComputedStyle(row).display !== 'none').length,
                    expanded: node.querySelector('.unmatched-expander-btn')?.getAttribute('aria-expanded'),
                })"""
            )
            if collapsed_by_top != {"visibleRows": 10, "expanded": "false"}:
                failures.append(
                    "unmatched report back-to-top did not collapse the panel: "
                    f"{collapsed_by_top!r}"
                )

        failures.extend(_unmatched_panel_width_sweep(page))
    finally:
        page.unroute(spotlight_pattern, fulfill_spotlight)
        delete_job(job_id)
    return failures
