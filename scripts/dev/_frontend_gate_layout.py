"""Layout checks: fonts, text scaling, touch targets, and large-display parity.

A slice of the frontend gate (F-B21-51). The scale-parity check measures in
separate helpers and judges in pure `*_failures` functions, so the judgements
can be unit-tested without a browser and the measurements stay thin.
Composition must reach its proportions through layout, never CSS `zoom` or
`transform`, which would satisfy a pixel check while breaking the type scale.
"""

from __future__ import annotations

import sys

from scripts.dev._frontend_gate_colour import _clamp_px
from scripts.dev._frontend_gate_shared import (
    ALL_PAGES,
    MIGRATED_PAGES,
    _reach_state,
)

FONTS_READY_EXPRESSION = "document.fonts.ready"

#: Every family in the configured Adobe Fonts kit that the design system uses.
REQUIRED_FONT_FAMILIES = (
    "akzidenz-grotesk-next-pro",
    "instrument-serif",
    "gotham",
    "input-mono",
    "input-mono-narrow",
)

#: Smallest side the design allows an interactive element to have, in CSS
#: pixels. docs/design/README.md calls this non-negotiable on touch.
MIN_TOUCH_TARGET_PX = 44

#: Everything a person can tap. [tabindex="-1"] is excluded: it is focusable
#: by script only and is not a target.
#:
#: label[for] is in the list and has to be. The theme toggle, the decade pills
#: and the sort segments are all a clipped 1x1 input driven by a styled label,
#: so the label is the only thing a finger can land on. Skipping the input
#: without measuring the label would measure none of them.
INTERACTIVE_SELECTOR = (
    "a[href], button, input, select, textarea, summary, label[for], "
    '[tabindex]:not([tabindex="-1"])'
)

#: States the touch-target check drives before measuring, per page.
#:
#: Measuring only what is on screen at load measures almost nothing: the
#: decade pills, the release-year field and the whole heatmap form all start
#: hidden, and a control a person has not reached yet is still a control.
#: Every state here is one click or one select away. The heatmap result needs
#: live API data and is out of reach from here -- owner review still owns it.
#:
#: "thresholds open" is insurance, not a fix. Chromium lays out the contents
#: of a closed <details>: the steppers measure 44x44 with the disclosure shut,
#: and deleting their sizing turns this check red in the "as loaded" state.
#: Measured, because a PR #218 review said the opposite. But the same probe
#: shows checkVisibility() returning false for those controls, so the layout
#: is a quirk rather than a promise, and a browser that stops laying them out
#: would silently stop measuring them. Opening the disclosure costs one click
#: and removes the dependency.
TOUCH_TARGET_STATES = {
    "/": (
        ("as loaded", ()),
        ("heatmap mode", (("click", "#mode-tab-heatmap"),)),
        ("decade filter", (("select", "#release_scope", "decade"),)),
        ("release year", (("select", "#release_scope", "custom"),)),
        ("thresholds open", (("click", ".disclosure__summary"),)),
    ),
}

#: Used for a page with nothing to drive.
DEFAULT_STATES = (("as loaded", ()),)


def check_touch_targets(page, base_url: str) -> list[str]:
    """Every tappable element reaches the design minimum on its smaller side.

    The design calls this non-negotiable and batch criterion 8 names it, but
    F-AUDIT-1 was closed against the theme toggle alone and nothing held the
    rest. This check runs at the mobile viewport only, where a finger is the
    pointer.

    An element with no box is not rendered, so there is nothing to hit and it
    is skipped.

    A label and its input are one target, and the check measures whichever of
    the pair a finger actually lands on. Where the input is visible -- a text
    field with a caption above it -- the input is the target and the caption is
    skipped. Where the input is clipped to 1x1 and styled through its label --
    the theme toggle, the decade pills, the sort segments -- the label is the
    target and the input is skipped. Measuring both would fail correct markup
    every time; measuring neither is what let six small targets ship.
    """
    failures = []
    for path in MIGRATED_PAGES:
        for state, actions in TOUCH_TARGET_STATES.get(path, DEFAULT_STATES):
            page.goto(f"{base_url}{path}", wait_until="load")
            try:
                _reach_state(page, actions)
            except Exception as exc:  # noqa: BLE001 - unreachable is a failure
                failures.append(
                    f"{path}: could not reach the {state!r} state: {type(exc).__name__}"
                )
                continue
            failures.extend(_small_targets(page, path, state))
    return failures


def _small_targets(page, path: str, state: str) -> list[str]:
    """Return one failure line per distinct undersized target in this state."""
    small = page.evaluate(
        """([selector, minimum]) => {
            const describe = (node) => {
                const name = node.tagName.toLowerCase();
                if (node.id) return `${name}#${node.id}`;
                const cls = (node.getAttribute('class') || '')
                    .trim().split(/\\s+/)[0];
                return cls ? `${name}.${cls}` : name;
            };
            // Clipped to 1x1 by the visually-hidden pattern, so a finger
            // cannot land on it and its partner is the real target.
            const CLIPPED_PX = 2;
            const side = (node) => {
                const rect = node.getBoundingClientRect();
                return Math.min(rect.width, rect.height);
            };
            const found = [];
            for (const node of document.querySelectorAll(selector)) {
                // Impeccable Live injects its own developer-only controls.
                // They are not part of the application touch surface.
                if (node.closest('[id^="impeccable-live-"]')) continue;
                const rect = node.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) continue;
                const smaller = Math.min(rect.width, rect.height);
                // An input styled through its label: the label is hit.
                if (smaller <= CLIPPED_PX && node.labels
                    && node.labels.length) {
                    continue;
                }
                // A label whose input is visible: the input is hit.
                if (node.tagName === 'LABEL') {
                    if (!node.control) continue;
                    if (side(node.control) > CLIPPED_PX) continue;
                }
                if (smaller < minimum) {
                    found.push({
                        what: describe(node),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                    });
                }
            }
            return found;
        }""",
        [INTERACTIVE_SELECTOR, MIN_TOUCH_TARGET_PX],
    )
    # Four identical stepper buttons are one defect, not four. Collapse them
    # so the count reads as how many places to fix.
    counted: dict[tuple[str, int, int], int] = {}
    for item in small:
        key = (item["what"], item["width"], item["height"])
        counted[key] = counted.get(key, 0) + 1
    return [
        f"{path} [{state}]: {what} is {width}x{height}"
        + (f" ({count} of them)" if count > 1 else "")
        + f", smaller side under {MIN_TOUCH_TARGET_PX}px"
        for (what, width, height), count in counted.items()
    ]


def check_fonts(page, base_url: str) -> list[str]:
    """Every kit family resolves to a real downloaded face.

    A browser fetches a face only when something asks for it, and at this
    point in the migration no page uses all five. So the check asks for each
    family deliberately rather than reading what the page happened to load.

    Asserting that the kit stylesheet was requested proves nothing: a
    domain-locked kit returns a stylesheet that loads no faces at all, and the
    page then falls back silently with no error anywhere.

    Owner ruling 2026-09-07: a missing face is advisory, not blocking. The
    page's own fallback stacks (corporate-a, orator-std, ...) are acceptable
    rendering, and a hard gate here made the whole run red whenever the
    fixture or the kit served no face -- which is a font-supply problem, not
    a UI defect. The failures still print so font-supply regressions stay
    visible; they just do not fail the run.
    """
    warnings = []
    for path in MIGRATED_PAGES:
        page.goto(f"{base_url}{path}", wait_until="load")
        # Await readiness and return nothing. Returning document.fonts.ready
        # hands Playwright a FontFaceSet, which it cannot serialize back.
        page.evaluate("async () => { await document.fonts.ready; }")
        loaded = page.evaluate(
            """async (families) => {
                const results = {};
                for (const family of families) {
                    try {
                        const faces = await document.fonts.load(
                            `16px "${family}"`
                        );
                        results[family] = faces.length;
                    } catch (error) {
                        results[family] = 0;
                    }
                }
                return results;
            }""",
            list(REQUIRED_FONT_FAMILIES),
        )
        warnings.extend(
            f"{path}: font family {family} loaded no faces from the kit "
            "(advisory; page falls back to its own stack)"
            for family, count in loaded.items()
            if not count
        )
    # Owner ruling 2026-09-07: print as WARN, return no gate failures.
    for warning in warnings:
        print(f"[frontend_gate] WARN {warning}", file=sys.stderr)
    return []


def check_body_font(page, base_url: str) -> list[str]:
    """Body takes the kit UI family on every page, migrated or not.

    check_fonts proves the kit serves a face. It does not prove anything on
    the page asks for it. Both were true at once for four pages: they
    downloaded the kit and then rendered in the Bootstrap system stack,
    because nothing set font-family on body.

    Computed style rather than the stylesheet text, because the failure is a
    cascade one. shell.css loads after Bootstrap and global.css, and the
    check has to see which declaration actually wins.
    """
    expected = REQUIRED_FONT_FAMILIES[0]
    failures = []
    for path in ALL_PAGES:
        page.goto(f"{base_url}{path}", wait_until="load")
        family = page.evaluate("() => getComputedStyle(document.body).fontFamily")
        if expected not in family:
            failures.append(f"{path}: body renders in {family}, not {expected}")
    return failures


def check_shell_scales_with_text(page, base_url: str) -> list[str]:
    """The desktop header leaves readable air around its global controls."""
    page.goto(f"{base_url}/", wait_until="load")
    previous_font_size = page.evaluate("() => document.documentElement.style.fontSize")
    try:
        state = page.evaluate(
            """() => {
                document.documentElement.style.fontSize = '20px';
                const mobile = matchMedia('(max-width: 859.98px)').matches;
                return {
                    height: document.querySelector('.site-header')
                        .getBoundingClientRect().height,
                    navGap: parseFloat(getComputedStyle(document.querySelector('.site-header__nav')).gap),
                    navTarget: document.querySelector('.site-header__nav-link')
                        .getBoundingClientRect().height,
                    // The desktop bar and nav-link clamp on viewport width
                    // (2.96875vw / 1.875vw) as well as the root font, so
                    // this DESKTOP profile's 1280px width matters: both
                    // preferred terms (38.0px / 24.0px) stay below their rem
                    // Both desktop and mobile use a 4.25rem floor bar;
                    // their 2.75rem nav-link floor matches, so both branches
                    // converge on the same 55px nav target.
                    expected: 4.25 * 20,
                    expectedTarget: 55,
                    expectedGap: mobile ? 5 : 15,
                };
            }"""
        )
    finally:
        page.evaluate(
            "(fontSize) => { document.documentElement.style.fontSize = fontSize; }",
            previous_font_size,
        )
    if abs(state["height"] - state["expected"]) > 0.1:
        return [
            f"/ .site-header: 20px root text produced {state['height']}px height, "
            f"expected {state['expected']}px"
        ]
    if state["navTarget"] < state["expectedTarget"] - 0.1:
        return [
            f"/ .site-header nav target is {state['navTarget']}px, "
            f"expected at least {state['expectedTarget']}px"
        ]
    if state["navGap"] < state["expectedGap"] - 0.1:
        return [
            f"/ .site-header nav gap is {state['navGap']}px, "
            f"expected at least {state['expectedGap']}px"
        ]
    return []


def _measure_scale_dimensions(page, base_url, selectors, width: int, height: int):
    """Read real rectangles and computed authored dimensions after fonts load."""
    page.set_viewport_size({"width": width, "height": height})
    page.goto(f"{base_url}/", wait_until="load")
    page.evaluate(FONTS_READY_EXPRESSION)
    return page.evaluate(
        """(targets) => Object.fromEntries(
            Object.entries(targets).map(([name, selector]) => {
                const node = document.querySelector(selector);
                if (!node) return [name, null];
                const rect = node.getBoundingClientRect();
                const style = getComputedStyle(node);
                return [name, {
                    width: rect.width,
                    height: rect.height,
                    fontSize: parseFloat(style.fontSize),
                    lineHeight: parseFloat(style.lineHeight),
                    marginTop: parseFloat(style.marginTop),
                    marginBottom: parseFloat(style.marginBottom),
                    paddingTop: parseFloat(style.paddingTop),
                    borderTopWidth: parseFloat(style.borderTopWidth),
                    borderTopLeftRadius: parseFloat(style.borderTopLeftRadius),
                }];
            })
        )""",
        selectors,
    )


def _measure_wide_layout(page):
    """Read the independent columns, centred card and fixed shell."""
    return page.evaluate(
        """() => {
            const hero = document.querySelector('.index-hero');
            const heroInner = document.querySelector('.index-hero__inner');
            const heroMark = document.querySelector('.index-hero__mark');
            const application = document.querySelector('.index-form');
            const form = document.querySelector('.index-form__inner');
            const card = document.querySelector('.ss-card');
            const style = getComputedStyle(application);
            const heroStyle = getComputedStyle(hero);
            const formRect = form.getBoundingClientRect();
            const header = document.querySelector('.site-header');
            const nav = document.querySelector('.site-header__nav');
            const rowNodes = [
                ...document.querySelectorAll(
                    '.site-header__nav-link, .site-header__theme-toggle'
                ),
            ];
            const tops = rowNodes.map(
                (node) => node.getBoundingClientRect().top
            );
            return {
                heroWidth: hero.getBoundingClientRect().width,
                heroPaddingLeft: parseFloat(heroStyle.paddingLeft),
                heroPaddingRight: parseFloat(heroStyle.paddingRight),
                heroInnerWidth: heroInner.getBoundingClientRect().width,
                heroMarkWidth: heroMark.getBoundingClientRect().width,
                applicationWidth: application.getBoundingClientRect().width,
                formLeft: application.getBoundingClientRect().left,
                formRight: application.getBoundingClientRect().right,
                formInnerLeft: formRect.left,
                formInnerRight: formRect.right,
                formInnerWidth: formRect.width,
                formInnerTop: formRect.top,
                formInnerBottom: formRect.bottom,
                cardLeft: card.getBoundingClientRect().left,
                cardRight: card.getBoundingClientRect().right,
                wellTop: application.getBoundingClientRect().top,
                wellBottom: application.getBoundingClientRect().bottom,
                viewportHeight: innerHeight,
                headerHeight: header.getBoundingClientRect().height,
                rootFontSize: parseFloat(getComputedStyle(document.documentElement).fontSize),
                paddingLeft: parseFloat(style.paddingLeft),
                paddingRight: parseFloat(style.paddingRight),
                headerGap: parseFloat(getComputedStyle(header).gap),
                navGap: parseFloat(getComputedStyle(nav).gap),
                rowSpread: Math.max(...tops) - Math.min(...tops),
            };
        }"""
    )


def _measure_zoom_and_transform(page):
    """Confirm the scale mechanism never resolves to zoom or a transform.

    Both `.ss-card` mode panels are already present in the DOM on a
    single page load -- only one is toggled `hidden` per the active
    mode, the other is never removed. This reads both without switching
    modes: computed `zoom` and `transform` still resolve on a hidden
    element (owner ruling 2026-09-05 #5), unlike a bounding rectangle,
    which would not.
    """
    return page.evaluate(
        """() => {
            const targets = [
                ['.index-hero__inner', document.querySelector('.index-hero__inner')],
                ['.index-form__inner', document.querySelector('.index-form__inner')],
                ['.mode-pill', document.querySelector('.mode-pill')],
                ['.ss-input', document.querySelector('.ss-input')],
                ['.ss-submit', document.querySelector('.ss-submit')],
            ];
            [...document.querySelectorAll('.ss-card')].forEach((node, index) => {
                targets.push([`.ss-card[${index}]`, node]);
            });
            return targets
                .filter(([, node]) => node)
                .map(([label, node]) => {
                    const style = getComputedStyle(node);
                    return { label, zoom: style.zoom, transform: style.transform };
                });
        }"""
    )


def _measure_fixed_state(page, base_url, actions):
    """Measure scale-controlled dimensions after one reachable state change."""
    page.set_viewport_size({"width": 1920, "height": 945})
    page.goto(f"{base_url}/", wait_until="load")
    _reach_state(page, actions)
    page.evaluate(FONTS_READY_EXPRESSION)
    page.wait_for_timeout(350)
    return page.evaluate(
        """() => {
            const visible = selector => [...document.querySelectorAll(selector)]
                .find(node => node.getClientRects().length > 0);
            const activeHero = document.querySelector('[data-mode-hero].is-active')
                || [...document.querySelectorAll('[data-mode-hero]')]
                    .find(node => !node.classList.contains('hidden'));
            const formColumn = document.querySelector('.index-form');
            const hero = document.querySelector('.index-hero');
            const heroInner = document.querySelector('.index-hero__inner');
            const heroMark = document.querySelector('.index-hero__mark');
            const formInner = document.querySelector('.index-form__inner');
            const card = visible('.ss-card');
            const input = visible('.ss-input');
            const headline = activeHero && activeHero.querySelector('.index-hero__headline');
            const formStyle = getComputedStyle(formColumn);
            const heroStyle = getComputedStyle(hero);
            const cardStyle = getComputedStyle(card);
            const inputStyle = getComputedStyle(input);
            const headlineStyle = getComputedStyle(headline);
            const modeStyle = getComputedStyle(document.querySelector('.mode-pill'));
            return {
                dimensions: {
                    formWidth: formInner.getBoundingClientRect().width,
                    formPaddingTop: parseFloat(formStyle.paddingTop),
                    heroPaddingLeft: parseFloat(heroStyle.paddingLeft),
                    heroInnerWidth: heroInner.getBoundingClientRect().width,
                    heroMarkWidth: heroMark.getBoundingClientRect().width,
                    headlineFont: parseFloat(headlineStyle.fontSize),
                    headlineLineHeight: parseFloat(headlineStyle.lineHeight),
                    cardPaddingTop: parseFloat(cardStyle.paddingTop),
                    inputHeight: input.getBoundingClientRect().height,
                    inputFont: parseFloat(inputStyle.fontSize),
                    modeHeight: document.querySelector('.mode-pill')
                        .getBoundingClientRect().height,
                    modeFont: parseFloat(modeStyle.fontSize),
                },
                viewportHeight: window.innerHeight,
                documentHeight: document.documentElement.scrollHeight,
                heroWidth: hero.getBoundingClientRect().width,
                heroPaddingLeft: parseFloat(heroStyle.paddingLeft),
                heroPaddingRight: parseFloat(heroStyle.paddingRight),
                heroInnerWidth: heroInner.getBoundingClientRect().width,
                heroMarkWidth: heroMark.getBoundingClientRect().width,
            };
        }"""
    )


def _measure_mobile_headers(page, base_url) -> dict:
    """Measure navigation containment and relocated theme controls at both widths."""
    mobile_headers = {}
    for width in (390, 320):
        page.set_viewport_size({"width": width, "height": 844})
        page.goto(f"{base_url}/", wait_until="load")
        mobile_headers[width] = page.evaluate(
            """() => {
                const header = document.querySelector('.site-header');
                const nav = document.querySelector('.site-header__nav');
                const navRect = nav.getBoundingClientRect();
                const actions = document.querySelector('.site-header__actions');
                const actionsRect = actions.getBoundingClientRect();
                const mainRect = document.querySelector('main').getBoundingClientRect();
                const links = [...nav.querySelectorAll('.site-header__nav-link')];
                return {
                    headerHeight: header.getBoundingClientRect().height,
                    headerPosition: getComputedStyle(header).position,
                    bodyPaddingTop: parseFloat(
                        getComputedStyle(document.body).paddingTop
                    ),
                    clientWidth: nav.clientWidth,
                    scrollWidth: nav.scrollWidth,
                    rows: new Set(links.map(link => Math.round(
                        link.getBoundingClientRect().top
                    ))).size,
                    actionsInHeader: header.contains(actions),
                    actionsInMobileSlot: Boolean(
                        actions.closest('.site-theme-mobile-slot')
                    ),
                    actionsTop: actionsRect.top,
                    contentBottom: mainRect.bottom,
                    themeHeight: document.querySelector('.site-header__theme-toggle')
                        .getBoundingClientRect().height,
                    linksInside: links.every(link => {
                        const rect = link.getBoundingClientRect();
                        return rect.left >= navRect.left - 0.5
                            && rect.right <= navRect.right + 0.5;
                    }),
                };
            }"""
        )
    return mobile_headers


def _measure_enlarged_root(page, base_url) -> float:
    """Measure the form's font-relative guard and restore root sizing on failure."""
    # Reset the expanded state: this probe exercises the initial form's
    # font-relative height denominator, with the root enlarged to 20px.
    page.set_viewport_size({"width": 1920, "height": 900})
    page.goto(f"{base_url}/", wait_until="load")
    page.evaluate(FONTS_READY_EXPRESSION)
    old_root = page.evaluate("document.documentElement.style.fontSize")
    try:
        root_measurement = page.evaluate(
            """() => {
            document.documentElement.style.fontSize = '20px';
            return document.querySelector('.index-form__inner')
                .getBoundingClientRect().width;
        }"""
        )
    finally:
        page.evaluate(
            "fontSize => { document.documentElement.style.fontSize = fontSize; }",
            old_root,
        )
    return root_measurement


def check_large_display_scale_parity(page, base_url: str) -> list[str]:
    """Prove the shared wide-desktop scale, capped form, and equal gutters.

    The CSS viewport determines the proportional scale. Browser and operating
    system zoom therefore reflow the page instead of receiving a second page
    scale. Navigation remains shell-sized while the hero and form grow as one
    composition, with a cap that scales in proportion and remains centred in
    the application well.
    """
    original_viewport = page.viewport_size
    selectors = {
        "hero composition": ".index-hero__inner",
        "form composition": ".index-form__inner",
        "wordmark": ".index-hero__mark",
        "headline": ".index-hero__headline",
        "form": ".ss-card",
        "submit": ".ss-submit",
        "field": ".field",
        "label": ".field__label",
        "theme control": ".site-header__theme-toggle",
        "input": ".ss-input",
        "mode tab": ".mode-pill",
        "page navigation": ".site-header__nav-link",
        "header bar": ".site-header",
    }
    scalable_dimensions = {
        # Width fills the 3fr column and is checked against its rendered
        # padding below; it does not follow the authored scale ratio.
        "hero composition": ("height",),
        "form composition": ("width", "height"),
        "wordmark": ("height", "marginBottom"),
        "headline": ("fontSize", "lineHeight", "marginBottom"),
        "form": ("width", "height", "paddingTop"),
        "input": ("height", "fontSize"),
        "mode tab": ("height", "fontSize"),
        "submit": ("height", "fontSize", "marginTop"),
        "field": ("marginBottom",),
        "label": ("fontSize",),
    }
    fixed_dimensions = {
        # Width and height now follow the ruled header clamps (Step 5) and
        # vary by window profile; only the font size stays a fixed rem.
        "page navigation": ("fontSize",),
        "theme control": ("width", "fontSize"),
        "form": ("borderTopWidth", "borderTopLeftRadius"),
        "input": ("borderTopWidth", "borderTopLeftRadius"),
    }
    # Fresh installed Chrome, temporary profile, maximised, no_viewport=True,
    # 100% page/OS scaling; measured 2026-09-04 on both owner panels:
    # 1920x1200 -> inner 1920x1065 (outer 1920x1152),
    # 2560x1440 -> inner 2560x1305 (outer 2560x1392).
    # The 135px panel-to-content difference includes desktop chrome. 1080p
    # and 4K below are DERIVED using that overhead, not measured panels.
    # set_viewport_size consumes these content boxes in both renderers.
    windows = {
        "1080p": (1920, 945),
        "1200p measured": (1920, 1065),
        "1440p": (2560, 1305),
        "4K": (3840, 2025),
    }

    try:
        measured_sizes = {}
        layouts = {}
        for label, (width, height) in windows.items():
            measured_sizes[label] = _measure_scale_dimensions(
                page, base_url, selectors, width, height
            )
            layouts[label] = _measure_wide_layout(page)
        zoom_transform = _measure_zoom_and_transform(page)
        at_mobile = _measure_scale_dimensions(page, base_url, selectors, 390, 844)
        mobile_layout = page.evaluate(
            """() => ({
            factor: getComputedStyle(document.querySelector('.index-grid'))
                .getPropertyValue('--index-scale').trim(),
            columns: getComputedStyle(document.querySelector('.index-grid'))
                .gridTemplateColumns.split(' ').length,
        })"""
        )
        mobile_headers = _measure_mobile_headers(page, base_url)
        fixed_states = {
            "as loaded": (),
            "heatmap mode": (("click", "#mode-tab-heatmap"),),
            "decade filter": (("select", "#release_scope", "decade"),),
            "release year": (("select", "#release_scope", "custom"),),
            "thresholds open": (("click", ".disclosure__summary"),),
            "decade + thresholds": (
                ("select", "#release_scope", "decade"),
                ("click", ".disclosure__summary"),
            ),
        }
        state_measurements = {
            state: _measure_fixed_state(page, base_url, actions)
            for state, actions in fixed_states.items()
        }
        root_measurement = _measure_enlarged_root(page, base_url)
    finally:
        if original_viewport:
            page.set_viewport_size(original_viewport)

    failures = []
    expected_scales = {
        # The outer cap mirrors --index-scale-cap in static/css/index.css
        # (1.75 since the owner's 2026-09-07 "1.75" ruling; it was 2.15).
        # A stale cap here made the gate expect a scale the CSS can no
        # longer reach at 4K, which produced ~1.4 percent proportional
        # failures on every width/height at that profile only.
        # The old literal 76 was the fixed --shell-height in px; Step 5
        # replaces it with clamp(4.25rem, 2.96875vw, 4.75rem), so the bar
        # height that a real window subtracts from is now width-dependent
        # too. This does not change any of the four resulting scales below:
        # the width term already wins at 1080p/1200p-measured (1.075 <
        # height term either way), and the bar clamps to its 76px ceiling
        # by 2560px width regardless (1440p, 4K), matching the old literal.
        label: min(
            1.75,
            max(
                0.70,
                min(
                    1.075
                    * (width / 1920 if width <= 1920 else (0.35 + 0.65 * width / 1920)),
                    (height - _clamp_px(4.25, 2.96875, 4.75, width)) / (673 + 108),
                ),
            ),
        )
        for label, (width, height) in windows.items()
    }
    for label, measurements in measured_sizes.items():
        for name in selectors:
            if measurements.get(name) is None:
                failures.append(f"/: {name} could not be measured at {label}")
    if failures:
        return failures
    # This probe forces the root font to 20px at a 1920px-wide viewport, so
    # the bar clamps to its 4.25rem floor (85px = clamp(85, 57, 95)): the
    # 57px vw term stays below the floor at this width even with the
    # enlarged root, since vw does not scale with the root font.
    header_height_at_enlarged_root = _clamp_px(4.25, 2.96875, 4.75, 1920, root_px=20)
    expected_root_width = (
        27.5 * 20 * ((900 - header_height_at_enlarged_root) / ((42.0625 + 4) * 20))
    )
    if abs(root_measurement - expected_root_width) > 1:
        failures.append(
            f"/: enlarged-root form width is {root_measurement:.1f}px, "
            f"expected font-relative height guard {expected_root_width:.1f}px"
        )
    failures.extend(
        _scale_dimension_failures(
            measured_sizes,
            layouts,
            expected_scales,
            scalable_dimensions,
            fixed_dimensions,
        )
    )
    failures.extend(
        _composition_bounds_failures(
            measured_sizes, layouts, expected_scales, mobile_layout, at_mobile
        )
    )
    failures.extend(_wide_layout_failures(layouts))
    for width, header in mobile_headers.items():
        failures.extend(_mobile_header_failures(width, header))
    # The ruled header clamps (Step 5): bar clamp(4.25rem, 2.96875vw, 4.75rem),
    # nav-link height clamp(2.75rem, 1.875vw, 3.5rem), nav-link width
    # clamp(5.75rem, 4.53vw, 7.25rem), theme-choice height
    # clamp(2.25rem, 1.5625vw, 2.5rem). At 1920px width (1080p) every
    # preferred vw term stays below its rem floor, so the floor wins; at
    # 2560px width (1440p) each preferred term lands at or above its rem
    # ceiling, so the ceiling wins (the bar exactly reproduces its current
    # 76px reference there). The theme toggle's own rendered height is the
    # choice clamp plus the toggle's fixed chrome (0.2rem padding x2 +
    # 1px border x2 = 8.4px), so it is asserted as a tolerance-bound curve,
    # not exact equality (owner ruling 2026-09-05 #4).
    failures.extend(_header_geometry_failures(measured_sizes, layouts))
    failures.extend(_scale_mechanism_failures(zoom_transform))
    baseline_state = state_measurements["as loaded"]
    failures.extend(
        _state_dimension_failures(
            baseline_state["dimensions"],
            {
                state: measurement["dimensions"]
                for state, measurement in state_measurements.items()
                if state != "as loaded"
            },
        )
    )
    expanded_state = state_measurements["decade + thresholds"]
    if expanded_state["documentHeight"] <= expanded_state["viewportHeight"] + 1:
        failures.append(
            "/: expanded decade + thresholds state shrinks to avoid document scrolling"
        )
    failures.extend(_check_desktop_scale_bounds(page, base_url))
    return failures


def _composition_bounds_failures(
    measured_sizes, layouts, expected_scales, mobile_layout, at_mobile
) -> list[str]:
    """Validate minimum growth, mobile sizing, column ratio and the ruled form cap."""
    failures = []
    at_1080p = measured_sizes["1080p"]
    layout_1080p = layouts["1080p"]
    for name in ("hero composition", "form composition"):
        growth = measured_sizes["1440p"][name]["width"] / at_1080p[name]["width"]
        if growth < 1.20:
            failures.append(
                f"/: {name} grows only {growth:.3f}x from a real 1080p "
                "window to a real 1440p window; expected at least 1.20x"
            )
    if mobile_layout["factor"] or mobile_layout["columns"] != 1:
        failures.append("/: desktop factor leaked into the mobile one-column layout")
    if at_mobile["input"]["height"] < 44 or at_mobile["input"]["fontSize"] < 16:
        failures.append("/: mobile input lost its touch or text minimum")

    # Was 5 / 3. Task 3 narrows the application column to 3fr 4fr.
    split_ratio = layout_1080p["applicationWidth"] / layout_1080p["heroWidth"]
    if abs(split_ratio - (4 / 3)) > 0.02:
        failures.append(
            f"/: wide desktop split is {split_ratio:.3f}, expected 4:3 application-to-hero"
        )
    # 27.5rem is the owner-refined base cap. The rendered card expands by
    # the same layout factor as the rest of the composition.
    expected_base_cap = 27.5 * 16
    for label in ("1080p", "1440p", "4K"):
        expected = expected_base_cap * expected_scales[label]
        actual = measured_sizes[label]["form composition"]["width"]
        if abs(actual - expected) > 2:
            failures.append(
                f"/: form cap is {actual:.0f}px at a real {label} window, "
                f"expected proportional {expected:.0f}px"
            )
    return failures


def _expected_scaled_dimension(
    name, dimension, at_1080p, ratio, hero_width, baseline_hero_width
):
    """Keep fixed border chrome and column-filling marks out of content scaling."""
    hero_width_ratio = hero_width / baseline_hero_width
    if name == "wordmark" and dimension == "height":
        expected = at_1080p["wordmark"]["height"] * hero_width_ratio
    elif name == "hero composition" and dimension == "height":
        expected_mark = at_1080p["wordmark"]["height"] * hero_width_ratio
        expected = (
            expected_mark
            + (at_1080p["hero composition"]["height"] - at_1080p["wordmark"]["height"])
            * ratio
        )
    else:
        fixed_height = {"form": 5, "form composition": 7}.get(name, 0)
        fixed = fixed_height if dimension == "height" else 0
        expected = (at_1080p[name][dimension] - fixed) * ratio + fixed
    return expected


def _scale_dimension_failures(
    measured_sizes, layouts, expected_scales, scalable_dimensions, fixed_dimensions
) -> list[str]:
    """Report scale dimension failures from rendered measurements."""
    failures = []
    at_1080p = measured_sizes["1080p"]
    baseline_scale = expected_scales["1080p"]
    for label in ("1200p measured", "1440p", "4K"):
        ratio = expected_scales[label] / baseline_scale
        for name, dimensions in scalable_dimensions.items():
            for dimension in dimensions:
                expected = _expected_scaled_dimension(
                    name,
                    dimension,
                    at_1080p,
                    ratio,
                    layouts[label]["heroInnerWidth"],
                    layouts["1080p"]["heroInnerWidth"],
                )
                actual = measured_sizes[label][name][dimension]
                # Fine borders stay 1px: stacked border boxes can differ by
                # a few pixels even when every content dimension scales.
                tolerance = 4 if dimension == "height" else 1
                if abs(actual - expected) > tolerance:
                    failures.append(
                        f"/: {name} {dimension} is {actual:.1f}px at {label}, "
                        f"expected proportional {expected:.1f}px"
                    )
        for name, dimensions in fixed_dimensions.items():
            for dimension in dimensions:
                if (
                    abs(
                        at_1080p[name][dimension]
                        - measured_sizes[label][name][dimension]
                    )
                    > 0.5
                ):
                    failures.append(
                        f"/: {name} {dimension} changes outside the shared composition"
                    )
    return failures


def _wide_layout_failures(layouts) -> list[str]:
    """Report wide layout failures from rendered measurements."""
    failures = []
    for label, layout in layouts.items():
        left_gutter = layout["formInnerLeft"] - layout["formLeft"]
        right_gutter = layout["formRight"] - layout["formInnerRight"]
        if abs(layout["paddingLeft"] - layout["paddingRight"]) > 0.1:
            failures.append(f"/: form well has asymmetric inline padding at {label}")
        if abs(left_gutter - right_gutter) > 1.5:
            failures.append(f"/: form has unequal side gutters at {label}")
        if min(left_gutter, right_gutter) < layout["paddingLeft"] - 1:
            failures.append(f"/: form intrudes into its well padding at {label}")
        top_gutter = layout["formInnerTop"] - layout["wellTop"]
        form_height = layout["formInnerBottom"] - layout["formInnerTop"]
        available = layout["viewportHeight"] - layout["headerHeight"]
        expected_top = max(
            0.25 * layout["rootFontSize"],
            (available - form_height) / 2 - 2.5 * layout["rootFontSize"],
        )
        if abs(top_gutter - expected_top) > 2:
            failures.append(
                f"/: form composition has the wrong upward offset at {label}: "
                f"{top_gutter:.1f}px top, expected {expected_top:.1f}px"
            )
        if (
            abs(layout["cardLeft"] - layout["formInnerLeft"]) > 1
            or abs(layout["cardRight"] - layout["formInnerRight"]) > 1
        ):
            failures.append(
                f"/: form card does not fill the composed form width at {label}"
            )
        hero_column_fill = (
            layout["heroWidth"] - layout["heroPaddingLeft"] - layout["heroPaddingRight"]
        )
        if abs(layout["heroInnerWidth"] - hero_column_fill) > 1:
            failures.append(
                f"/: hero inner is {layout['heroInnerWidth']:.1f}px at {label}, "
                f"expected to fill its padded column at {hero_column_fill:.1f}px"
            )
        if abs(layout["heroMarkWidth"] - layout["heroInnerWidth"]) > 1:
            failures.append(
                f"/: wordmark is {layout['heroMarkWidth']:.1f}px at {label}, "
                f"expected to track the hero inner at {layout['heroInnerWidth']:.1f}px"
            )

    return failures


def _header_geometry_failures(measured_sizes, layouts) -> list[str]:
    """Report header geometry failures from rendered measurements."""
    failures = []
    header_geometry = {
        label: {
            "bar": _clamp_px(4.25, 2.96875, 4.75, width),
            "nav height": _clamp_px(2.75, 1.875, 3.5, width),
            "nav width": _clamp_px(5.75, 4.53, 7.25, width),
            "toggle height": _clamp_px(2.25, 1.5625, 2.5, width) + 8.4,
        }
        for label, width in (("1080p", 1920), ("1440p", 2560))
    }
    for label, expected_geometry in header_geometry.items():
        bar = measured_sizes[label]["header bar"]["height"]
        nav = measured_sizes[label]["page navigation"]
        toggle = measured_sizes[label]["theme control"]["height"]
        if abs(bar - expected_geometry["bar"]) > 0.5:
            failures.append(
                f"/: header bar is {bar:.1f}px at {label}, "
                f"expected ruled {expected_geometry['bar']:.1f}px"
            )
        if abs(nav["height"] - expected_geometry["nav height"]) > 0.5:
            failures.append(
                f"/: page navigation height is {nav['height']:.1f}px at {label}, "
                f"expected ruled {expected_geometry['nav height']:.1f}px"
            )
        if abs(nav["width"] - expected_geometry["nav width"]) > 0.5:
            failures.append(
                f"/: page navigation width is {nav['width']:.1f}px at {label}, "
                f"expected ruled {expected_geometry['nav width']:.1f}px"
            )
        if abs(toggle - expected_geometry["toggle height"]) > 1:
            failures.append(
                f"/: theme control height is {toggle:.1f}px at {label}, "
                f"expected the ruled ~{expected_geometry['toggle height']:.1f}px curve"
            )
        layout = layouts[label]
        if abs(layout["headerGap"] - layout["navGap"]) > 0.1:
            failures.append(
                f"/: header and nav use different sibling-gap tokens at {label}"
            )
        if layout["rowSpread"] > 1:
            failures.append(
                f"/: nav links and the theme control wrap onto more than one "
                f"row at {label}"
            )

    return failures


def _scale_mechanism_failures(zoom_transform) -> list[str]:
    """Report scale mechanism failures from rendered measurements."""
    failures = []
    for entry in zoom_transform:
        if entry["zoom"] not in ("1", "normal"):
            failures.append(
                f"/: {entry['label']} sets zoom to {entry['zoom']!r}, expected 1"
            )
        if entry["transform"] != "none":
            failures.append(
                f"/: {entry['label']} sets transform to {entry['transform']!r}, "
                "expected none"
            )

    return failures


def _touch_minimum_failures(
    width: int, rectangles: dict[str, dict[str, float]]
) -> list[str]:
    """Name every control whose rendered box falls below the touch minimum."""
    return [
        f"/: {selector} loses its touch minimum at {width}px"
        for selector, rectangle in rectangles.items()
        if min(rectangle.values()) < 43.9
    ]


def _mobile_header_failures(width: int, header: dict) -> list[str]:
    """Assert the mobile header contract for one viewport width.

    The header stays in document flow and scrolls away (owner screenshot
    clarification, 2026-09-10). Extra body padding would duplicate its height.
    """
    failures = []
    if header["scrollWidth"] > header["clientWidth"] + 1 or not header["linksInside"]:
        failures.append(
            f"/: mobile navigation requires horizontal scrolling at {width}px"
        )
    if header["rows"] != 1:
        failures.append(
            f"/: mobile navigation uses {header['rows']} row(s) at {width}px, "
            "expected one directly visible row"
        )
    if header["actionsInHeader"] or not header["actionsInMobileSlot"]:
        failures.append(f"/: mobile theme control remains in the header at {width}px")
    if header["actionsTop"] < header["contentBottom"] - 0.5:
        failures.append(
            f"/: mobile theme control is not below the page content at {width}px"
        )
    if header["themeHeight"] < 44:
        failures.append(
            f"/: mobile theme control is only {header['themeHeight']:.1f}px high "
            f"at {width}px, expected at least 44px"
        )
    # In flow on mobile too: reserve the actual header height exactly once.
    if (
        header["headerPosition"] not in {"relative", "static"}
        or abs(header["bodyPaddingTop"]) > 0.5
    ):
        failures.append(
            f"/: mobile header must scroll away without a body offset at {width}px"
        )
    return failures


def _state_dimension_failures(
    baseline: dict[str, float],
    states: dict[str, dict[str, float]],
    *,
    tolerance: float = 0.5,
) -> list[str]:
    """Report authored dimensions that move while the viewport stays fixed."""
    failures = []
    for state, measurements in states.items():
        for dimension, expected in baseline.items():
            actual = measurements.get(dimension)
            if actual is None:
                failures.append(f"/: {state} did not measure {dimension}")
            elif abs(actual - expected) > tolerance:
                failures.append(
                    f"/: {dimension} changes from {expected:.1f}px to "
                    f"{actual:.1f}px in {state} at a fixed viewport"
                )
    return failures


def _headline_wrap_failures(probe, width: int) -> list[str]:
    """Name each desktop mode whose headline wraps at the given width."""
    failures = []
    for mode in ("album", "heatmap"):
        probe.locator(f"#mode-tab-{mode}").click()
        headline = probe.locator(f'[data-mode-hero="{mode}"] h1')
        headline.wait_for(state="visible")
        dimensions = headline.evaluate(
            """node => ({
            height: node.getBoundingClientRect().height,
            lineHeight: parseFloat(getComputedStyle(node).lineHeight),
        })"""
        )
        if dimensions["height"] > dimensions["lineHeight"] * 1.2:
            failures.append(f"/: {mode} headline wraps at {width}px")
    return failures


def _check_desktop_scale_bounds(page, base_url: str) -> list[str]:
    """Exercise readable narrow headlines, expanded states and wide touch growth.

    These use an isolated context because touch capability is immutable per
    context, and no diagnostic may leave its mode or viewport on the caller.
    """
    failures = []
    context = page.context.browser.new_context(has_touch=True)
    try:
        probe = context.new_page()
        # The H1 must hold one line across the whole desktop range, not only
        # when maximised (owner report 2026-09-02): the 1200px breakpoint, an
        # intermediate windowed width, and both real profiles above it.
        # F-B21-38's --index-scale-min floor is what buys this; a failure
        # here means the floor is too high, not that the H1 needs its own
        # rule.
        for width in (1200, 1500, 1920, 2560):
            probe.set_viewport_size({"width": width, "height": 900})
            probe.goto(f"{base_url}/", wait_until="load")
            probe.evaluate(FONTS_READY_EXPRESSION)
            failures.extend(_headline_wrap_failures(probe, width))
        widths = {}
        for width, height in ((1920, 945), (2560, 1305)):
            probe.set_viewport_size({"width": width, "height": height})
            probe.goto(f"{base_url}/", wait_until="load")
            probe.locator("#release_scope").select_option("decade")
            probe.locator(".disclosure__summary").click()
            probe.evaluate(FONTS_READY_EXPRESSION)
            widths[width] = probe.evaluate(
                """() => Object.fromEntries(
                ['.mode-pill', '.seg__option', '.decade-pill', '.disclosure__summary',
                 '.stepper__value', '.ss-input'].map(selector => {
                    const rect = document.querySelector(selector).getBoundingClientRect();
                    return [selector, {width: rect.width, height: rect.height}];
                }))"""
            )
            failures.extend(_touch_minimum_failures(width, widths[width]))
        # The open form may contract to fit its state. Compare controls at a
        # tall window so that this check tests proportional touch dimensions.
        for width in (1920, 2560):
            probe.set_viewport_size({"width": width, "height": 2025})
            probe.goto(f"{base_url}/", wait_until="load")
            probe.locator("#release_scope").select_option("decade")
            probe.locator(".disclosure__summary").click()
            widths[width] = probe.evaluate(
                """() => Object.fromEntries(
                ['.mode-pill', '.seg__option', '.decade-pill', '.disclosure__summary'].map(selector =>
                    [selector, document.querySelector(selector).getBoundingClientRect().height]))"""
            )
        authored_heights = {
            ".mode-pill": 44,
            ".seg__option": 38,
            ".decade-pill": 30,
            ".disclosure__summary": 32,
        }
        for width, controls in widths.items():
            scale = (
                1.075 * (width / 1920)
                if width <= 1920
                else 1.075 * (0.35 + 0.65 * (width / 1920))
            )
            for selector, actual in controls.items():
                expected = max(44, authored_heights[selector] * scale)
                if abs(actual - expected) > 1:
                    failures.append(
                        f"/: {selector} touch height is {actual:.1f}px at {width}px, "
                        f"expected authored size with touch floor {expected:.1f}px"
                    )
    finally:
        context.close()
    return failures


def check_destination_empty_states(page, base_url: str) -> list[str]:
    """Clean destinations explain the next action without changing saved work."""
    failures = []
    page.context.clear_cookies()
    expected = {
        "/results": ("results", "/"),
        "/heatmap": ("heatmap", "/?mode=heatmap"),
        "/unmatched": ("unmatched", "/"),
    }
    for path, (kind, action) in expected.items():
        page.goto(f"{base_url}{path}", wait_until="load")
        state = page.locator(f'[data-empty-state="{kind}"]')
        if state.count() != 1:
            failures.append(f"{path}: dedicated {kind} empty state is missing")
            continue
        href = state.locator("a").first.get_attribute("href")
        if href != action:
            failures.append(
                f"{path}: empty-state action is {href!r}, expected {action!r}"
            )
        details = state.evaluate(
            """node => {
                const card = document.querySelector('.card');
                const emptySection = node.matches('.empty-state') ? node : node.querySelector('.empty-state');
                const style = emptySection ? getComputedStyle(emptySection) : null;
                const actionLink = node.querySelector('a');
                const actionRect = actionLink ? actionLink.getBoundingClientRect() : null;
                return {
                    hasCard: card !== null && getComputedStyle(card).display !== 'none',
                    hasSection: emptySection !== null,
                    boxShadow: style ? style.boxShadow : 'none',
                    actionUsable: actionRect !== null && actionRect.width > 0 && actionRect.height > 0,
                };
            }"""
        )
        if details["hasCard"]:
            failures.append(f"{path}: empty state contains an unexpected visible .card")
        if not details["hasSection"]:
            failures.append(f"{path}: .empty-state section element is missing")
        if details["boxShadow"] not in ("none", "", "rgba(0, 0, 0, 0) 0px 0px 0px 0px"):
            failures.append(
                f"{path}: .empty-state has unexpected box shadow: {details['boxShadow']!r}"
            )
        if not details["actionUsable"]:
            failures.append(f"{path}: empty-state action link is not usable/visible")

    page.goto(f"{base_url}/?mode=heatmap", wait_until="load")
    fresh_state = page.evaluate(
        """() => ({
            formVisible: getComputedStyle(
                document.querySelector('#heatmap-form-section')
            ).display !== 'none',
            heatmapSelected: document.querySelector('#mode-tab-heatmap')
                .classList.contains('active'),
            homeCurrent: document.querySelector('.site-header__nav-link[href="/"]')
                .getAttribute('aria-current') === 'page',
        })"""
    )
    for claim, passed in fresh_state.items():
        if not passed:
            failures.append(f"/?mode=heatmap: fresh-start claim {claim!r} failed")
    return failures
