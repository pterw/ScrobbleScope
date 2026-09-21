"""Theme checks: tokens, divider contrast, persistence, motion, and the mark.

A slice of the frontend gate (F-B21-51). Every check here reads computed
values -- a resolved token, a composited contrast ratio, a stored preference
after reload -- because a class name or a declared value passes against a
stylesheet the browser never applied.
"""

from __future__ import annotations

from scripts.dev._frontend_gate_colour import (
    _divider_contrast_failure,
    _is_forbidden_surface,
    _worst_divider_contrast,
)
from scripts.dev._frontend_gate_shared import MIGRATED_PAGES, TOGGLE_TIMEOUT_MS
from scrobblescope.repositories import (
    create_job,
    delete_job,
    set_job_progress,
    set_job_results,
)

THEME_EXPRESSION = "() => document.documentElement.dataset.theme"
SET_THEME_EXPRESSION = (
    "(theme) => document.documentElement.setAttribute('data-theme', theme)"
)

#: Cool-grey surfaces the warm themes replaced. Batch criterion 2 forbids them.
FORBIDDEN_SURFACES = ("rgb(248, 249, 250)", "rgb(18, 18, 18)")


def _computed_colour(page, value: str) -> str:
    """Resolve a CSS value through a probe element to a computed rgb() string.

    getPropertyValue on a custom property can return the unresolved
    var(--other) text rather than a colour, so comparing raw token text is
    unreliable. Painting a probe forces the cascade to resolve it.
    """
    return page.evaluate(
        """(value) => {
            const probe = document.createElement('div');
            document.body.appendChild(probe);
            probe.style.backgroundColor = value;
            const computed = getComputedStyle(probe).backgroundColor;
            probe.remove();
            return computed;
        }""",
        value,
    )


def check_divider_contrast(page, base_url: str) -> list[str]:
    """Every divider token must clear 3:1 against every surface it sits beside.

    The tokens carry alpha or a fixed hue -- either way, alpha is not the
    only way contrast drifts, so the composite (or, for an opaque token, the
    colour itself) is what is measured, not the token string. F-B21-24 found
    ``--shell-border`` under 3:1; F-B21-40 found the index page's own well
    divider under 3:1 too, on a *different* token (``--ss-border-default``,
    since renamed for this purpose to ``--ss-border-divider``) that this
    check did not previously read at all. Both are measured here so the gate
    cannot go green while either divider is unreadable.
    """
    failures = []
    for theme in ("light", "dark"):
        page.goto(f"{base_url}/", wait_until="load")
        page.evaluate(
            SET_THEME_EXPRESSION,
            theme,
        )
        border = _computed_colour(page, "var(--shell-border)")
        bg = _computed_colour(page, "var(--shell-bg)")
        surface = _computed_colour(page, "var(--shell-surface)")
        ratio = _worst_divider_contrast(border, bg, surface)
        failure = _divider_contrast_failure(theme, ratio)
        if failure:
            failures.append(failure)

        # The index well divider sits between the page (the hero column,
        # which paints no background of its own) and the sunken form well.
        # Read the rendered border directly off .index-form rather than
        # only the token, so a selector that stopped applying the token
        # would also be caught.
        index_border = page.evaluate(
            """() => {
                const form = document.querySelector('.index-form');
                return form ? getComputedStyle(form).borderLeftColor : null;
            }"""
        )
        if index_border is None:
            failures.append(f"/ index divider {theme}: .index-form could not be found")
            continue
        page_surface = _computed_colour(page, "var(--color-base-100)")
        well_surface = _computed_colour(page, "var(--ss-surface-sunken)")
        index_ratio = _worst_divider_contrast(index_border, page_surface, well_surface)
        index_failure = _divider_contrast_failure(
            f"index divider {theme}", index_ratio, token="--ss-border-divider"
        )
        if index_failure:
            failures.append(index_failure)
    return failures


def check_theme_tokens(page, base_url: str) -> list[str]:
    """--bars-color aliases the theme primary, and no cool-grey survives."""
    failures = []
    for path in MIGRATED_PAGES:
        for theme in ("light", "dark"):
            page.goto(f"{base_url}{path}", wait_until="load")
            page.evaluate(
                SET_THEME_EXPRESSION,
                theme,
            )
            bars = _computed_colour(page, "var(--bars-color)")
            primary = _computed_colour(page, "var(--color-primary)")
            if bars != primary:
                failures.append(
                    f"{path} {theme}: --bars-color is {bars}, "
                    f"theme primary is {primary}"
                )
            surfaces = page.evaluate(
                """() => {
                    const seen = new Set();
                    for (const node of document.querySelectorAll('*')) {
                        seen.add(getComputedStyle(node).backgroundColor);
                    }
                    return [...seen];
                }"""
            )
            # Compared as colours, not strings: the same grey arriving
            # through a color-mix() serializes as color(srgb 0.97 0.98 0.98),
            # which no string comparison against rgb(248, 249, 250) matches,
            # and the check would stay green with the surface on screen.
            for surface in surfaces:
                if _is_forbidden_surface(surface, FORBIDDEN_SURFACES):
                    failures.append(
                        f"{path} {theme}: forbidden cool-grey surface {surface}"
                    )
    return failures


def check_index_design_tokens(page, base_url: str) -> list[str]:
    """Rendered index states use the canonical status and radius tokens."""
    expected = {
        "light": {
            "good": "#2f7a4a",
            "chip": "0 1px 3px rgb(0 0 0 / 0.06)",
            "float": "0 2px 8px rgb(0 0 0 / 0.15)",
        },
        "dark": {
            "good": "#6fcf97",
            "chip": "0 1px 3px rgb(0 0 0 / 0.4)",
            "float": "0 2px 8px rgb(0 0 0 / 0.4)",
        },
    }
    failures = []
    for theme, wanted in expected.items():
        page.goto(f"{base_url}/", wait_until="load")
        page.evaluate(
            SET_THEME_EXPRESSION,
            theme,
        )
        page.evaluate("document.querySelector('#username').classList.add('is-valid')")
        # Border colour transitions for 200ms. Read the settled state a user
        # sees, not the first animation frame after the class changes.
        page.wait_for_timeout(250)
        state = page.evaluate(
            """() => {
                const username = document.querySelector('#username');
                return {
                    good: getComputedStyle(document.documentElement)
                        .getPropertyValue('--ss-good').trim(),
                    fieldBorder: getComputedStyle(username).borderColor,
                    chipToken: getComputedStyle(document.documentElement)
                        .getPropertyValue('--ss-shadow-chip').trim(),
                    floatToken: getComputedStyle(document.documentElement)
                        .getPropertyValue('--ss-shadow-float').trim(),
                    modeShadow: getComputedStyle(
                        document.querySelector('.mode-pill.active')
                    ).boxShadow,
                    segmentShadow: getComputedStyle(
                        document.querySelector('.seg__radio:checked + .seg__option')
                    ).boxShadow,
                    segmentRadius: getComputedStyle(
                        document.querySelector('.seg__option')
                    ).borderRadius,
                    descriptorOrder: [...document.querySelectorAll('[data-mode-hero]')]
                        .every(hero => hero.querySelector('h1 + .eyebrow')),
                };
            }"""
        )
        good = _computed_colour(page, wanted["good"])
        if state["good"] != wanted["good"]:
            failures.append(
                f"/ {theme}: --ss-good is {state['good']!r}, expected {wanted['good']}"
            )
        if state["fieldBorder"] != good:
            failures.append(
                f"/ {theme}: a valid username border is {state['fieldBorder']}, "
                f"expected {good}"
            )

        if state["chipToken"] != wanted["chip"]:
            failures.append(
                f"/ {theme}: --ss-shadow-chip is {state['chipToken']!r}, "
                f"expected {wanted['chip']}"
            )
        for selector, actual in (
            (".mode-pill.active", state["modeShadow"]),
            (".seg__option", state["segmentShadow"]),
        ):
            if actual != "none":
                failures.append(
                    f"/ {theme} {selector}: shadow is {actual}, expected none"
                )

        if state["floatToken"] != wanted["float"]:
            failures.append(
                f"/ {theme}: --ss-shadow-float is {state['floatToken']!r}, "
                f"expected {wanted['float']}"
            )
        if state["segmentRadius"] != "8px":
            failures.append(
                f"/ {theme} .seg__option: radius is {state['segmentRadius']}, "
                f"expected the 8px design step"
            )
        if not state["descriptorOrder"]:
            failures.append(f"/ {theme}: a mode descriptor appears above its heading")
    return failures


def check_theme_persistence(page, base_url: str) -> list[str]:
    """Toggling then reloading keeps the theme without changing shared state.

    The check drives [data-theme-toggle], the visible control, rather than the
    hidden checkbox behind it. A hidden input is not clickable, so targeting it
    costs a 30-second actionability timeout instead of an answer.

    It runs on every migrated page. It used to skip the index deliberately:
    index.html opened a welcome modal on load, and Bootstrap's .modal-backdrop
    sits at z-index 1050, above the 1030 header, so the toggle was genuinely
    unclickable there. WP-3 deleted that modal, which closes F-B21-11, so the
    reason is gone and the index is covered like any other page.
    """
    failures = []
    saved_preference = None
    preference_read = False
    try:
        for path in MIGRATED_PAGES:
            page.goto(f"{base_url}{path}", wait_until="load")
            if not preference_read:
                saved_preference = page.evaluate(
                    "() => localStorage.getItem('darkMode')"
                )
                preference_read = True
            toggle = page.locator("[data-theme-toggle]")
            if toggle.count() == 0:
                failures.append(f"{path}: no [data-theme-toggle] control found")
                continue

            before = page.evaluate(THEME_EXPRESSION)
            try:
                toggle.first.click(timeout=TOGGLE_TIMEOUT_MS)
            except Exception as exc:  # noqa: BLE001 - any click fault is a failure
                failures.append(
                    f"{path}: the theme toggle could not be clicked: "
                    f"{type(exc).__name__}"
                )
                continue

            toggled = page.evaluate(THEME_EXPRESSION)
            if toggled == before:
                failures.append(
                    f"{path}: toggling did not change data-theme (stayed {before!r})"
                )
                continue

            page.reload(wait_until="load")
            after = page.evaluate(THEME_EXPRESSION)
            if after != toggled:
                failures.append(
                    f"{path}: theme did not survive reload: "
                    f"{toggled!r} became {after!r}"
                )
    finally:
        if preference_read:
            page.evaluate(
                """(saved) => {
                    if (saved === null) localStorage.removeItem('darkMode');
                    else localStorage.setItem('darkMode', saved);
                }""",
                saved_preference,
            )
            page.reload(wait_until="load")
    return failures


def check_index_entrance_motion(page, base_url: str) -> list[str]:
    """The index composition enters once, while reduced motion stays visible."""
    failures = []
    try:
        page.emulate_media(reduced_motion="no-preference")
        page.goto(f"{base_url}/", wait_until="load")
        standard = page.locator(".index-page").evaluate(
            """element => {
                const style = getComputedStyle(element);
                return {
                    name: style.animationName,
                    duration: style.animationDuration,
                    delay: style.animationDelay,
                };
            }"""
        )
        if standard != {
            "name": "ss-page-enter",
            "duration": "0.22s",
            "delay": "0s",
        }:
            failures.append(f"index entrance motion is {standard!r}")

        before_ready = page.locator(".index-page").evaluate(
            """element => {
                document.body.classList.remove('is-ready');
                const name = getComputedStyle(element).animationName;
                document.body.classList.add('is-ready');
                return name;
            }"""
        )
        if before_ready != "ss-page-enter":
            failures.append(
                "page entrance waits for JavaScript and can flash before readiness"
            )

        # Sample the actual animation timeline: a declared duration alone can
        # pass while another rule pins opacity to its endpoint.
        motion = page.locator(".index-page").evaluate(
            """element => {
                const enter = element.getAnimations().find(a => a.animationName === 'ss-page-enter');
                if (!enter) return {enter: null, exit: null};
                enter.pause();
                enter.currentTime = 110;
                const arrival = Number(getComputedStyle(element).opacity);
                enter.finish();
                document.body.classList.add('is-leaving');
                getComputedStyle(element).animationName;
                const exit = element.getAnimations().find(a => a.animationName === 'ss-page-exit');
                if (!exit) {
                    document.body.classList.remove('is-leaving');
                    return {enter: arrival, exit: null};
                }
                exit.pause();
                exit.currentTime = 70;
                const departure = Number(getComputedStyle(element).opacity);
                document.body.classList.remove('is-leaving');
                element.getAnimations().forEach(a => a.finish());
                return {enter: arrival, exit: departure};
            }"""
        )
        if any(value is None or not 0 < value < 1 for value in motion.values()):
            failures.append(f"page motion does not interpolate opacity: {motion!r}")

        initial_hero = page.evaluate(
            """() => {
                const copy = document.querySelector('.index-hero__copy');
                const album = document.querySelector('[data-mode-hero="album"]');
                const heatmap = document.querySelector('[data-mode-hero="heatmap"]');
                const read = node => {
                    const style = getComputedStyle(node);
                    return {
                        active: node.classList.contains('is-active'),
                        ariaHidden: node.getAttribute('aria-hidden'),
                        opacity: style.opacity,
                        visibility: style.visibility,
                        duration: style.transitionDuration,
                    };
                };
                return {
                    height: copy && copy.getBoundingClientRect().height,
                    album: album && read(album),
                    heatmap: heatmap && read(heatmap),
                };
            }"""
        )
        page.locator("#mode-tab-heatmap").click()
        page.wait_for_timeout(220)
        switched_hero = page.evaluate(
            """() => {
                const copy = document.querySelector('.index-hero__copy');
                const album = document.querySelector('[data-mode-hero="album"]');
                const heatmap = document.querySelector('[data-mode-hero="heatmap"]');
                const read = node => {
                    const style = getComputedStyle(node);
                    return {
                        active: node.classList.contains('is-active'),
                        ariaHidden: node.getAttribute('aria-hidden'),
                        opacity: style.opacity,
                        visibility: style.visibility,
                        duration: style.transitionDuration,
                    };
                };
                return {
                    height: copy && copy.getBoundingClientRect().height,
                    album: album && read(album),
                    heatmap: heatmap && read(heatmap),
                };
            }"""
        )
        expected_initial = {
            "active": True,
            "ariaHidden": "false",
            "opacity": "1",
            "visibility": "visible",
            "duration": "0.18s, 0s",
        }
        expected_inactive = {
            "active": False,
            "ariaHidden": "true",
            "opacity": "0",
            "visibility": "hidden",
            "duration": "0.18s, 0s",
        }
        if initial_hero["album"] != expected_initial:
            failures.append(
                f"initial album hero transition is {initial_hero['album']!r}"
            )
        if initial_hero["heatmap"] != expected_inactive:
            failures.append(
                f"initial heatmap hero transition is {initial_hero['heatmap']!r}"
            )
        if switched_hero["album"] != expected_inactive:
            failures.append(
                f"switched album hero transition is {switched_hero['album']!r}"
            )
        if switched_hero["heatmap"] != expected_initial:
            failures.append(
                f"switched heatmap hero transition is {switched_hero['heatmap']!r}"
            )
        if abs(switched_hero["height"] - initial_hero["height"]) > 0.5:
            failures.append("mode hero crossfade changes the reserved copy height")

        page.emulate_media(reduced_motion="reduce")
        page.goto(f"{base_url}/", wait_until="load")
        reduced = page.locator(".index-page").evaluate(
            """element => {
                const style = getComputedStyle(element);
                return {name: style.animationName, opacity: style.opacity};
            }"""
        )
        if reduced != {"name": "none", "opacity": "1"}:
            failures.append(f"reduced-motion index entrance is {reduced!r}")
        reduced_hero_duration = page.locator('[data-mode-hero="album"]').evaluate(
            "element => getComputedStyle(element).transitionDuration"
        )
        if reduced_hero_duration != "0s":
            failures.append(
                f"reduced-motion hero transition lasts {reduced_hero_duration!r}"
            )
    finally:
        page.emulate_media(reduced_motion="no-preference")
    return failures


def check_mark_follows_theme(page, base_url: str) -> list[str]:
    """Every ScrobbleScope mark on a migrated page recolours with the theme.

    The wordmark asset carries its own <style> pinning stroke: #6a4baf, and
    its letterforms have no fill rule, so a wrapper shell.css does not name
    renders fixed-purple bars and user-agent black text. The index hero
    shipped that way: pure black letterforms on the #0e0c12 dark page.

    No other check reads a colour off an inline SVG, which is why the whole
    gate stayed green through it.

    It compares each mark against the resolved `--shell-ink` and
    `--shell-accent` for the theme, not merely light against dark. Two holes
    in the first version made that necessary, both raised on PR #220. A part
    whose selector stopped matching read as null and was skipped, so re-cutting
    the asset would retire the check silently. And a wrapper wired to the wrong
    but theme-varying token passed, because differing between themes was the
    whole test. Reading the tokens through a probe element lets the browser
    normalise them, so `#1a1820` and `rgb(26, 24, 32)` compare equal.
    """
    failures = []
    for path in MIGRATED_PAGES:
        page.goto(f"{base_url}{path}", wait_until="load")
        seen = page.evaluate(
            """() => {
                const probe = document.createElement('span');
                probe.style.display = 'none';
                document.body.appendChild(probe);
                const token = name => {
                    probe.style.color = `var(${name})`;
                    return getComputedStyle(probe).color;
                };
                const read = () => ({
                    ink: token('--shell-ink'),
                    accent: token('--shell-accent'),
                    marks: [...document.querySelectorAll('.ss-mark')].map(node => {
                        const bar = node.querySelector('svg .cls-1');
                        const text = node.querySelector('svg #logo-text path');
                        return {
                            name: node.getAttribute('class'),
                            bar: bar ? getComputedStyle(bar).stroke : null,
                            text: text ? getComputedStyle(text).fill : null,
                        };
                    }),
                });
                const root = document.documentElement;
                const before = root.getAttribute('data-theme');
                root.setAttribute('data-theme', 'light');
                const light = read();
                root.setAttribute('data-theme', 'dark');
                const dark = read();
                root.setAttribute('data-theme', before || 'light');
                probe.remove();
                return {light, dark};
            }"""
        )
        light, dark = seen["light"], seen["dark"]
        if not light["marks"]:
            failures.append(
                f"{path}: no .ss-mark found -- the header mark is on every page, "
                f"so this check is measuring nothing"
            )
            continue
        for index, mark in enumerate(light["marks"]):
            name = mark["name"]
            for part, key in (("letterforms", "text"), ("bars", "bar")):
                want_key = "ink" if key == "text" else "accent"
                for theme, side in (("light", light), ("dark", dark)):
                    got = side["marks"][index][key]
                    if got is None:
                        failures.append(
                            f"{path} .{name}: {part} not found in {theme} -- the "
                            f"selector no longer matches, so nothing is checked"
                        )
                        continue
                    want = side[want_key]
                    if got != want:
                        failures.append(
                            f"{path} .{name}: {part} are {got} in {theme}, expected "
                            f"{want} from var(--shell-{want_key}) -- shell.css does "
                            f"not name this wrapper, or names the wrong token"
                        )
    return failures


#: Make every localStorage access throw the way a browser does when site data
#: is blocked -- a private window, tracking protection, a per-origin block.
#: Installed before any page script runs.
_BLOCK_STORAGE = """
(() => {
  const boom = () => { throw new DOMException('denied', 'SecurityError'); };
  Object.defineProperty(window, 'localStorage', {
    configurable: true,
    get() { return { getItem: boom, setItem: boom, removeItem: boom }; },
  });
})();
"""


def check_theme_survives_blocked_storage(page, base_url: str) -> list[str]:
    """The system preference still decides the theme when storage throws.

    `base.html` sets `data-theme` before first paint so the page does not
    render light and flip. Reading `localStorage` is the first thing it does,
    and that read throws outright where a browser blocks site data. While the
    read, the media query and the write shared one `try`, a thrown read
    skipped all three and left the hardcoded `light` on the root -- so a
    reader whose system says dark got a light page, and the toggle could not
    help, because the matching `setItem` throws too.

    The system preference needs no storage, so it has to stay reachable when
    storage is not.

    This opens its own context. Blocked storage is installed as an init
    script, which cannot be removed afterwards, so running it on the shared
    page would poison every later check.
    """
    browser = page.context.browser
    if browser is None:  # pragma: no cover - only for a browserless context
        return ["blocked-storage check needs a browser-backed context"]

    cases = (
        ("dark", "dark"),
        ("light", "light"),
    )
    failures = []
    for scheme, expected in cases:
        context = browser.new_context(color_scheme=scheme)
        try:
            context.add_init_script(_BLOCK_STORAGE)
            probe = context.new_page()
            probe.goto(base_url, wait_until="load")
            got = probe.get_attribute("html", "data-theme")
            if got != expected:
                failures.append(
                    f"/ storage blocked, system {scheme}: data-theme is {got!r}, "
                    f"expected {expected!r} -- the pre-paint script let a thrown "
                    f"storage read skip the media query"
                )
        finally:
            context.close()
    return failures


def check_heatmap_zero_cells_follow_theme(page, base_url: str) -> list[str]:
    """A theme change repaints the heatmap's zero-count cells.

    The cells carry a `fill` presentation attribute, and an SVG presentation
    attribute does not resolve a custom property, so the repaint is JavaScript:
    `heatmap.js` watches for the theme change and rewrites every zero cell.
    It watched `<body>` for the `.dark-mode` class until WP-8 retired that
    write, and nothing here noticed, because every other theme check reads CSS.
    """
    failures = []
    job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    set_job_results(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": "2025-01-01",
            "to_date": "2025-01-05",
            "total_scrobbles": 3,
            "max_count": 3,
            "daily_counts": {
                "2025-01-01": 3,
                "2025-01-02": 0,
                "2025-01-03": 0,
                "2025-01-04": 1,
                "2025-01-05": 0,
            },
        },
    )
    set_job_progress(job_id, progress=100, message="Done", error=False)
    try:
        page.goto(f"{base_url}/heatmap?job_id={job_id}", wait_until="load")
        page.locator("#heatmap-result-frame svg").wait_for(state="visible")
        page.locator('.heatmap-cell[data-count="0"]').first.wait_for(state="attached")
        readings = {}
        for theme in ("light", "dark"):
            page.evaluate(SET_THEME_EXPRESSION, theme)
            page.wait_for_timeout(120)
            readings[theme] = page.evaluate(
                """() => {
                    const cell = document.querySelector('.heatmap-cell[data-count="0"]');
                    const probe = getComputedStyle(document.documentElement)
                        .getPropertyValue('--heatmap-empty').trim();
                    return { fill: cell?.getAttribute('fill'), token: probe };
                }"""
            )
    finally:
        delete_job(job_id)

    for theme, reading in readings.items():
        if not reading["fill"]:
            failures.append(f"/heatmap renders no zero-count cell in the {theme} theme")
        elif reading["fill"] != reading["token"]:
            failures.append(
                f"/heatmap zero cells are {reading['fill']!r} in the {theme} theme, "
                f"expected the --heatmap-empty token {reading['token']!r}"
            )
    if len(readings) == 2 and readings["light"]["fill"] == readings["dark"]["fill"]:
        failures.append(
            "/heatmap zero cells did not repaint across a theme change: "
            f"{readings['light']['fill']!r} in both"
        )
    return failures


def check_heatmap_export_header_matches_page(page, base_url: str) -> list[str]:
    """The saved heatmap image states what the page states.

    The export draws its header on a canvas by hand, so its wording can drift
    from the page and nothing shows it: a saved file is only seen after it is
    saved. It drew "LISTENING HEATMAP . LAST 365 DAYS" over "A year of <name>"
    long after the page had moved to the possessive headline with the source
    named underneath.
    """
    failures = []
    job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    set_job_results(
        job_id,
        {
            "username": "frontend-gate",
            "from_date": "2025-01-01",
            "to_date": "2025-01-05",
            "total_scrobbles": 4,
            "max_count": 4,
            "daily_counts": {"2025-01-01": 4, "2025-01-02": 0},
        },
    )
    set_job_progress(job_id, progress=100, message="Done", error=False)
    try:
        page.goto(f"{base_url}/heatmap?job_id={job_id}", wait_until="load")
        page.locator("#heatmap-result-frame svg").wait_for(state="visible")
        # Save for real: the record read below is what the canvas drew, so a
        # line that stops being drawn cannot pass by matching the page.
        with page.expect_download():
            page.click("#heatmap-save-image")
        state = page.evaluate(
            """() => {
                const model = window.__scrobbleHeatmapDrawnHeader?.();
                const headline = document.querySelector('#heatmap-result-headline');
                const eyebrow = document.querySelector('.heatmap-head__titles .eyebrow');
                return {
                    model,
                    pageHeadline: headline?.textContent.trim(),
                    pageEyebrow: eyebrow?.textContent.trim(),
                    username: document.querySelector('.heatmap-headline-username')
                        ?.textContent.trim(),
                    pageCaps: [...document.querySelectorAll('.heatmap-legend__cap')]
                        .map(node => getComputedStyle(node).textTransform === 'uppercase'
                            ? node.textContent.trim().toUpperCase()
                            : node.textContent.trim()),
                };
            }"""
        )
    finally:
        delete_job(job_id)

    model = state["model"]
    if not model:
        failures.append("/heatmap exposes no export header for the saved image")
        return failures
    if model["headline"] != state["pageHeadline"]:
        failures.append(
            f"saved heatmap headline is {model['headline']!r}, "
            f"the page says {state['pageHeadline']!r}"
        )
    if model["eyebrow"].lower() != (state["pageEyebrow"] or "").lower():
        failures.append(
            f"saved heatmap eyebrow is {model['eyebrow']!r}, "
            f"the page says {state['pageEyebrow']!r}"
        )
    if state["username"] and state["username"] not in model["headline"]:
        failures.append(
            f"saved heatmap headline drops the username {state['username']!r}"
        )
    # The saved legend is a bare gradient without its captions: nothing in the
    # image then says which end of the ramp means more listening.
    caps = model.get("legend") or {}
    if [caps.get("less"), caps.get("more")] != state["pageCaps"]:
        failures.append(
            f"saved heatmap legend captions are {[caps.get('less'), caps.get('more')]!r}, "
            f"the page shows {state['pageCaps']!r}"
        )
    return failures
