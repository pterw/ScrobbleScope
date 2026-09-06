"""Repository-owned frontend gate for the Batch 21 Tailwind migration.

`pytest` sees Python and `pre-commit` sees text. Neither can see what a browser
computes, so the deliverables that matter most in a CSS migration -- which
stylesheet a page loads, what a token resolves to, whether the theme survives a
reload, whether a font actually arrives -- have nothing enforcing them.

This script closes that gap. It starts the real Flask app on a loopback port it
owns, drives Chromium and Firefox, and asserts those properties. It needs no
separately running server and no MCP service, so it runs the same way locally
and in CI.

Every check runs in the real viewport profiles it declares, and every failure
says which one it came from. The matrix includes both sides of the layout
breakpoint plus a wide coarse-pointer device. The gate grows with the
migration: each work package adds its page to MIGRATED_PAGES, and adds a check
when it ships something the existing ones cannot see.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from werkzeug.serving import make_server

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Throwaway key so the app boots under the gate. It signs nothing that
#: outlives the run, and the server listens on loopback only.
GATE_SECRET_KEY = "frontend-gate-local-only-not-a-production-secret"

# Run as a script, the repository root is not on sys.path, so the app factory
# is unimportable. pytest finds it through rootdir; a direct CLI run does not.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# app.py builds a module-level app instance, so importing it boots the whole
# application. The key therefore has to be set before the import, not before
# create_app.
#
# Not setdefault: GitHub Actions sets SECRET_KEY to an empty string when the
# repository secret is missing, and empty is present. create_app would then
# read "", call it weak, and raise at import -- a traceback instead of a FAIL
# line. The workflow sets FLASK_ENV, which nothing reads; the guard reads
# DEBUG_MODE, so CI is never in dev mode.
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = GATE_SECRET_KEY

from app import create_app  # noqa: E402
from scrobblescope.repositories import (  # noqa: E402
    create_job,
    delete_job,
    get_job_context,
    get_job_progress,
    reset_job_state,
    set_job_error,
    set_job_progress,
    set_job_results,
    set_job_stat,
)

BROWSER_NAMES = ("chromium", "firefox")
SETUP_COMMAND = "python -m playwright install chromium firefox"
FONTS_READY_EXPRESSION = "document.fonts.ready"

#: Cool-grey surfaces the warm themes replaced. Batch criterion 2 forbids them.
FORBIDDEN_SURFACES = ("rgb(248, 249, 250)", "rgb(18, 18, 18)")

#: Every family in the configured Adobe Fonts kit that the design system uses.
REQUIRED_FONT_FAMILIES = (
    "akzidenz-grotesk-next-pro",
    "instrument-serif",
    "gotham",
    "input-mono",
    "input-mono-narrow",
)

#: Clicking budget for the theme toggle. Short, because a miss means the
#: control is absent or unclickable, and waiting 30s does not change that.
TOGGLE_TIMEOUT_MS = 5000

#: Marker that identifies a Bootstrap stylesheet in a link href.
BOOTSTRAP_MARKER = "bootstrap"

#: Marker that identifies the compiled Tailwind stylesheet in a link href.
TAILWIND_MARKER = "tailwind.css"

#: Any unknown URL renders error.html through the app_errorhandler(404) in
#: scrobblescope/routes.py. There is no direct route to the error page.
ERROR_PAGE_PATH = "/no-such-page-for-the-gate"

#: Consumed by check_theme_tokens and check_fonts. Pages already migrated to
#: Tailwind. Each work package adds its page here, one line.
#:
#: Only migrated pages belong here. A Bootstrap page has no --color-primary
#: and loads no kit faces, so pointing those two checks at every page would
#: park four permanent failures in the output until WP-7 -- and a gate with
#: expected failures in it stops being read.
MIGRATED_PAGES = ["/", "/results", "/heatmap", ERROR_PAGE_PATH]

#: Throwaway jobs owned by serve_app and driven by pipeline checks.
GATE_JOB_IDS: dict[str, str] = {}

#: ``serve_app`` temporarily extends module-level page inventories for the
#: loading fixture. Serialising that context keeps two in-process gate runs
#: from clearing each other's job IDs or removing each other's route.
_SERVE_APP_LOCK = threading.Lock()

#: Pages still served by Bootstrap. Move each one into MIGRATED_PAGES in the
#: work package that migrates it.
#:
#: The job-backed Results and Unmatched templates remain on Bootstrap until
#: their work packages. The dedicated no-job Results route is migrated, but it
#: does not claim that results.html is migrated. Unmatched still renders the
#: shared migrated error surface when no album job exists.
LEGACY_PAGES = []

#: Consumed by check_stylesheet_isolation. Exactly one framework stylesheet is
#: a claim about every page, migrated or not, so this check takes both lists.
ALL_PAGES = [*LEGACY_PAGES, *MIGRATED_PAGES]

#: The device profiles available to visual checks.
#:
#: Every check this batch built ran at Playwright's 1280x720 default, so
#: mobile was verified by owner review and nothing else. The design has one
#: breakpoint, so a width each side of it covers layout. 390x844 is the
#: design's mobile reference canvas.
#:
#: Width is not the whole story, which a PR #218 review found. A tablet in
#: landscape and a touch laptop are both wide and both touched, so a
#: touch-target rule written against a width misses them entirely. The third
#: profile is a wide screen with a coarse pointer. Chromium's has_touch
#: emulation drives (pointer: coarse) and (any-pointer: coarse), measured,
#: which is what makes the rule testable at all.
#:
#: is_mobile is deliberately off. It changes device scale and scrollbars,
#: which would move every measurement this gate has taken so far.
DESKTOP = "desktop"
MOBILE = "mobile"
TOUCH_WIDE = "wide touch"
VIEWPORTS = {
    DESKTOP: {"viewport": {"width": 1280, "height": 720}},
    MOBILE: {"viewport": {"width": 390, "height": 844}, "has_touch": True},
    TOUCH_WIDE: {"viewport": {"width": 1280, "height": 800}, "has_touch": True},
}

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

#: What must be invisible when a migrated page first loads. The scripts reveal
#: each one later.
#:
#: A class name is not evidence. `.index-grid` set display:grid and outranked
#: Tailwind's `.hidden`, so the heatmap rendered under a hero that never left,
#: and a probe asserting className passed anyway. Assert the computed value.
HIDDEN_ON_LOAD = {
    "/": (
        "#heatmap-form-section",
        "#heatmap-loading",
        "#heatmap-result",
        "#heatmap-result-headline",
        "#heatmap-result-frame",
        "#heatmap-error",
        "#decade_dropdown",
        "#release_year_group",
    ),
}


class FrontendGateError(RuntimeError):
    """A gate prerequisite is missing, so no check could run."""


def _load_playwright():
    """Return sync_playwright, or explain exactly how to install it.

    The gate never downloads tooling on its own. Implicit installs turn a
    two-second failure into a silent multi-hundred-megabyte download.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FrontendGateError(
            f"Playwright is not installed. Run: {SETUP_COMMAND}"
        ) from exc
    return sync_playwright


def _launch_browser(playwright, browser_name: str, *, headless: bool = True):
    """Launch the named engine, translating a missing build into guidance.

    Pinning the package does not fetch the browser. The two failures look
    completely different but have the same remedy.
    """
    try:
        return getattr(playwright, browser_name).launch(headless=headless)
    except Exception as exc:
        raise FrontendGateError(
            f"{browser_name} is not available to Playwright. Run: {SETUP_COMMAND}"
        ) from exc


@contextmanager
def serve_app() -> Iterator[str]:
    """Serve the real app on a loopback port for the duration of the block.

    Port 0 asks the OS for a free port, so parallel runs cannot collide. The
    shutdown sits in a finally block: a failing check must never leave a
    listening socket behind.
    """
    with _SERVE_APP_LOCK:
        loading_job_id = None
        heatmap_job_id = None
        loading_path = None
        server = None
        thread = None
        thread_started = False
        previous_job_ids = dict(GATE_JOB_IDS)
        try:
            app = create_app()
            loading_job_id = create_job(
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
            set_job_progress(
                loading_job_id,
                progress=42,
                message="Fetching scrobbles - page 21 / 50",
                error=False,
            )
            loading_path = f"/loading?job_id={loading_job_id}"
            heatmap_job_id = create_job(
                {
                    "username": "frontend-gate",
                    "mode": "heatmap",
                }
            )
            GATE_JOB_IDS.update(album=loading_job_id, heatmap=heatmap_job_id)
            MIGRATED_PAGES.append(loading_path)
            ALL_PAGES.append(loading_path)

            server = make_server("127.0.0.1", 0, app)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            thread_started = True
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            if server is not None:
                if thread_started:
                    server.shutdown()
                if thread is not None:
                    thread.join(timeout=5)
                server.server_close()
            if loading_path is not None:
                if loading_path in MIGRATED_PAGES:
                    MIGRATED_PAGES.remove(loading_path)
                if loading_path in ALL_PAGES:
                    ALL_PAGES.remove(loading_path)
            if loading_job_id is not None:
                delete_job(loading_job_id)
            if heatmap_job_id is not None:
                delete_job(heatmap_job_id)
            GATE_JOB_IDS.clear()
            GATE_JOB_IDS.update(previous_job_ids)


def _stylesheet_hrefs(page) -> list[str]:
    """Return the href of every stylesheet link the page loads."""
    return page.eval_on_selector_all(
        "link[rel=stylesheet]", "nodes => nodes.map(node => node.href)"
    )


def check_stylesheet_isolation(page, base_url: str) -> list[str]:
    """Each page loads exactly one framework stylesheet.

    Bootstrap and daisyUI both claim .btn, .card and .modal, and Tailwind's
    preflight would reset a Bootstrap page. Loading both is the collision the
    strangler migration exists to avoid.
    """
    failures = []
    for path in ALL_PAGES:
        page.goto(f"{base_url}{path}", wait_until="load")
        hrefs = _stylesheet_hrefs(page)
        framework = [
            href
            for href in hrefs
            if BOOTSTRAP_MARKER in href.lower() or TAILWIND_MARKER in href.lower()
        ]
        # Exactly one, not merely "not both". Two Bootstrap links is the
        # cdnjs/jsdelivr split this batch tracks as F-B20-3, and it fails here.
        if len(framework) != 1:
            failures.append(
                f"{path} loads {len(framework)} framework stylesheets, "
                f"expected exactly 1: {framework}"
            )
    return failures


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


def _computed_shadow(page, value: str) -> str:
    """Resolve a box-shadow value through the browser's CSS parser."""
    return page.evaluate(
        """(value) => {
            const probe = document.createElement('div');
            document.body.appendChild(probe);
            probe.style.boxShadow = value;
            const computed = getComputedStyle(probe).boxShadow;
            probe.remove();
            return computed;
        }""",
        value,
    )


def _parse_rgb_string(value: str) -> tuple[float, float, float, float]:
    """Parse a computed ``rgb()``/``rgba()`` string into an (r, g, b, a) tuple."""
    numbers = [float(part) for part in re.findall(r"[\d.]+", value)]
    red, green, blue = numbers[:3]
    alpha = numbers[3] if len(numbers) > 3 else 1.0
    return red, green, blue, alpha


def _composite_over(
    foreground: tuple[float, float, float, float],
    background: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Alpha-composite a translucent foreground colour over an opaque one."""
    fg_red, fg_green, fg_blue, alpha = foreground
    bg_red, bg_green, bg_blue = background
    return (
        fg_red * alpha + bg_red * (1 - alpha),
        fg_green * alpha + bg_green * (1 - alpha),
        fg_blue * alpha + bg_blue * (1 - alpha),
    )


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG relative luminance of an sRGB colour given as 0-255 channels."""

    def channel(value: float) -> float:
        normalised = value / 255
        if normalised <= 0.03928:
            return normalised / 12.92
        return ((normalised + 0.055) / 1.055) ** 2.4

    red, green, blue = rgb
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast_ratio(
    rgb_a: tuple[float, float, float], rgb_b: tuple[float, float, float]
) -> float:
    """WCAG contrast ratio between two opaque sRGB colours."""
    luminance_a = _relative_luminance(rgb_a) + 0.05
    luminance_b = _relative_luminance(rgb_b) + 0.05
    return max(luminance_a, luminance_b) / min(luminance_a, luminance_b)


def _clamp_px(
    min_rem: float,
    vw_percent: float,
    max_rem: float,
    width_px: float,
    root_px: float = 16,
) -> float:
    """Mirror a CSS ``clamp(<min_rem>rem, <vw_percent>vw, <max_rem>rem)``.

    ``vw`` is a percentage of the viewport width in CSS pixels; it never
    scales with the root font size, only the rem bounds do. Python has to
    keep those two independent to reproduce the browser's resolved value.
    """
    preferred = vw_percent * width_px / 100
    return min(max_rem * root_px, max(min_rem * root_px, preferred))


def _worst_divider_contrast(border: str, *surfaces: str) -> float:
    """The lowest contrast a translucent divider reaches against its surfaces.

    A divider is painted over whatever sits beside it, not over one known
    background, so an alpha that clears 3:1 against one surface can still
    fail against another. Compositing every candidate surface and keeping
    the minimum is what "adjacent surface" has to mean for a token shared
    across the header and the rest of the shell.
    """
    border_rgba = _parse_rgb_string(border)
    ratios = []
    for surface in surfaces:
        surface_rgb = _parse_rgb_string(surface)[:3]
        composited = _composite_over(border_rgba, surface_rgb)
        ratios.append(_contrast_ratio(composited, surface_rgb))
    return min(ratios)


def _divider_contrast_failure(
    label: str, ratio: float, token: str = "--shell-border"
) -> str | None:
    """Name a divider-contrast failure, or None once the ratio clears 3:1.

    ``token`` names which custom property the message blames. F-B21-40 made
    this a parameter rather than a literal: the same helper now checks both
    the shared ``--shell-border`` and the index page's own
    ``--ss-border-divider``, and a message that always said "--shell-border"
    would misattribute a failing index divider to the wrong token.
    """
    if ratio >= 3.0:
        return None
    return (
        f"/ {label}: {token} composites to {ratio:.2f}:1 against its "
        "adjacent surface, expected at least 3:1"
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
            "(theme) => document.documentElement.setAttribute('data-theme', theme)",
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
                "(theme) => document.documentElement"
                ".setAttribute('data-theme', theme)",
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
            for forbidden in FORBIDDEN_SURFACES:
                if forbidden in surfaces:
                    failures.append(
                        f"{path} {theme}: forbidden cool-grey surface {forbidden}"
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
            "(theme) => document.documentElement.setAttribute('data-theme', theme)",
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

            before = page.evaluate("() => document.documentElement.dataset.theme")
            try:
                toggle.first.click(timeout=TOGGLE_TIMEOUT_MS)
            except Exception as exc:  # noqa: BLE001 - any click fault is a failure
                failures.append(
                    f"{path}: the theme toggle could not be clicked: "
                    f"{type(exc).__name__}"
                )
                continue

            toggled = page.evaluate("() => document.documentElement.dataset.theme")
            if toggled == before:
                failures.append(
                    f"{path}: toggling did not change data-theme "
                    f"(stayed {before!r})"
                )
                continue

            page.reload(wait_until="load")
            after = page.evaluate("() => document.documentElement.dataset.theme")
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
                    f"{path}: could not reach the {state!r} state: "
                    f"{type(exc).__name__}"
                )
                continue
            failures.extend(_small_targets(page, path, state))
    return failures


def _reach_state(page, actions) -> None:
    """Drive the page into one state, using real clicks and selections.

    Real interactions rather than dispatched events: a synthetic event can
    reach a listener that a genuine click could never trigger, and the check
    is about what a finger can do.
    """
    for action in actions:
        kind, selector = action[0], action[1]
        target = page.locator(selector).first
        if kind == "click":
            target.click(timeout=TOGGLE_TIMEOUT_MS)
        elif kind == "select":
            target.select_option(action[2], timeout=TOGGLE_TIMEOUT_MS)
        else:  # pragma: no cover - a typo in the table, not a page fault
            raise ValueError(f"unknown touch-target action {kind!r}")


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


def check_validation_feedback(page, base_url: str) -> list[str]:
    """Typing clears a validation message that is already on screen.

    Bootstrap's .invalid-feedback was hidden unless a sibling carried
    .is-invalid, so dropping that class hid stale text for free. The
    replacement .field__error hides only while it is empty, so every script
    that writes into one has to empty it again. Both did not, and a rejected
    username stayed on screen while the reader typed a new one and after a
    valid one resolved -- a green field and a red error at once.

    No network call. The check writes a message into the node itself, which is
    exactly the state a rejection leaves behind, then types one real character
    and asks whether the handler cleared it. /validate_user needs a live
    Last.fm key, and a gate that needs a secret does not run in CI.
    """
    # The heatmap field lives in a panel that starts hidden, so its tab has to
    # be clicked before anything can be typed into it.
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    failures = []
    for path, selector, actions in fields:
        page.goto(f"{base_url}{path}", wait_until="load")
        _reach_state(page, actions)
        node = page.evaluate(
            """(selector) => {
                const input = document.querySelector(selector);
                if (!input) return 'no such input';
                const error = input.parentNode.querySelector('.field__error');
                if (!error) return 'no .field__error beside it';
                error.textContent = 'Username not found on Last.fm.';
                return null;
            }""",
            selector,
        )
        if node:
            failures.append(f"{path} {selector}: {node}")
            continue

        # A real keystroke. A dispatched event can reach a listener that a
        # person never could, which is the opposite of what this proves.
        page.locator(selector).type("a")
        left = page.evaluate(
            """(selector) => document.querySelector(selector)
                .parentNode.querySelector('.field__error').textContent""",
            selector,
        )
        if left:
            failures.append(
                f"{path} {selector}: typing left the message {left!r} on screen"
            )
    return failures


def check_private_profile_is_blocked(page, base_url: str) -> list[str]:
    """A private-profile verdict blocks both forms on the index before submit.

    The backend owns the Last.fm error-17 classification. This browser check
    supplies that result at the network boundary and proves the shared index
    validation UI turns it into an actionable message and native form block.
    """
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    message = (
        "This Last.fm profile is private. Make recent listening public and try again."
    )
    failures = []
    page.route(
        "**/validate_user*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=f'{{"valid": false, "message": "{message}"}}',
        ),
    )
    try:
        for path, selector, actions in fields:
            page.goto(f"{base_url}{path}", wait_until="load")
            _reach_state(page, actions)
            page.locator(selector).type("private_profile")
            page.locator(selector).blur()
            page.wait_for_function(
                """(selector) => {
                    const input = document.querySelector(selector);
                    return input && !input.checkValidity();
                }""",
                arg=selector,
            )
            state = page.evaluate(
                """(selector) => {
                    const input = document.querySelector(selector);
                    const error = input.parentNode.querySelector('.field__error');
                    return {
                        blocked: !input.checkValidity(),
                        message: error ? error.textContent.trim() : '',
                    };
                }""",
                selector,
            )
            if not state["blocked"]:
                failures.append(f"{path} {selector}: private profile can submit")
            if state["message"] != message:
                failures.append(
                    f"{path} {selector}: private-profile message is {state['message']!r}"
                )
    finally:
        page.unroute("**/validate_user*")
    return failures


def check_index_entrance_motion(page, base_url: str) -> list[str]:
    """The index composition enters once, while reduced motion stays visible."""
    failures = []
    try:
        page.emulate_media(reduced_motion="no-preference")
        page.goto(f"{base_url}/", wait_until="load")
        standard = page.locator("#index-grid").evaluate(
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
            "name": "ss-index-page-enter",
            "duration": "0.18s",
            "delay": "0s",
        }:
            failures.append(f"index entrance motion is {standard!r}")

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
        reduced = page.locator("#index-grid").evaluate(
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


def check_validator_outage_is_recoverable(page, base_url: str) -> list[str]:
    """A failing validator does not lock the form it was meant to help.

    /validate_user answers a Last.fm outage with 503 and {"valid": false,
    "Validation service unavailable. Try again."}. Read as a verdict about the
    username, that sets a custom validity error, and then trying again is the
    one thing the message asks for that cannot work -- the heatmap form
    refuses at its own submit guard and the index form refuses at native
    validation, since only the heatmap form carries novalidate.

    The route is stubbed rather than called. A real 503 needs Last.fm to be
    down, and a gate that needs a secret does not run in CI.
    """
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    failures = []
    page.route(
        "**/validate_user*",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"valid": false, "message": "Validation service unavailable."}',
        ),
    )
    try:
        for path, selector, actions in fields:
            page.goto(f"{base_url}{path}", wait_until="load")
            _reach_state(page, actions)
            page.locator(selector).type("someone")
            page.locator(selector).blur()
            page.wait_for_timeout(600)
            state = page.evaluate(
                """(selector) => {
                    const input = document.querySelector(selector);
                    const error = input.parentNode.querySelector('.field__error');
                    return {
                        blocked: !input.checkValidity(),
                        told: error ? error.textContent.trim() : '',
                    };
                }""",
                selector,
            )
            if state["blocked"]:
                failures.append(
                    f"{path} {selector}: a 503 left the field refusing to submit, "
                    f"so the reader cannot do what it tells them"
                )
            if not state["told"]:
                failures.append(f"{path} {selector}: a 503 said nothing to the reader")
    finally:
        page.unroute("**/validate_user*")
    return failures


def check_stale_validator_failure_is_discarded(page, base_url: str) -> list[str]:
    """An older failed request cannot clear a newer same-name verdict.

    Two blur validations can overlap because an earlier fetch stays in flight;
    the album form's debounce cancels only work that has not started. A value
    comparison handles A then B, but not A then B then A: both requests name
    A. If the newer A is rejected first and the older A then fails, only
    request identity can keep the older catch from clearing current validity.
    """
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    failures = []
    for path, selector, actions in fields:
        pending = []
        handled = []
        page.route("**/validate_user*", lambda route: pending.append(route))
        try:
            page.goto(f"{base_url}{path}", wait_until="load")
            _reach_state(page, actions)
            field = page.locator(selector)

            field.fill("repeated-request")
            field.blur()
            page.wait_for_timeout(400)
            field.fill("temporary-request")
            field.fill("repeated-request")
            field.blur()
            page.wait_for_timeout(400)
            if len(pending) != 2:
                failures.append(
                    f"{path} {selector}: expected two overlapping validations, "
                    f"held {len(pending)}"
                )
                continue

            pending[1].fulfill(
                status=404,
                content_type="application/json",
                body='{"valid": false, "message": "Newer username is invalid."}',
            )
            handled.append(pending[1])
            page.wait_for_function(
                "(selector) => !document.querySelector(selector).checkValidity()",
                arg=selector,
            )

            pending[0].abort("failed")
            handled.append(pending[0])
            page.wait_for_timeout(100)
            if page.locator(selector).evaluate("input => input.checkValidity()"):
                failures.append(
                    f"{path} {selector}: the older same-name failure cleared "
                    f"the newer invalid verdict"
                )
        finally:
            for route in pending:
                if route not in handled:
                    route.abort("failed")
            page.unroute("**/validate_user*")
    return failures


def check_current_validator_failure_replaces_old_verdict(
    page, base_url: str
) -> list[str]:
    """A current network failure cannot leave an older invalid verdict visible."""
    fields = (
        ("/", "#username", ()),
        ("/", "#heatmap-username", (("click", "#mode-tab-heatmap"),)),
    )
    failures = []
    for path, selector, actions in fields:
        pending = []
        handled = []
        page.route("**/validate_user*", lambda route: pending.append(route))
        try:
            page.goto(f"{base_url}{path}", wait_until="load")
            _reach_state(page, actions)
            field = page.locator(selector)

            field.fill("same-request")
            field.blur()
            page.wait_for_timeout(400)
            if len(pending) != 1:
                failures.append(
                    f"{path} {selector}: expected the first validation, held "
                    f"{len(pending)}"
                )
                continue
            pending[0].fulfill(
                status=404,
                content_type="application/json",
                body='{"valid": false, "message": "Initial username is invalid."}',
            )
            handled.append(pending[0])
            page.wait_for_function(
                "(selector) => !document.querySelector(selector).checkValidity()",
                arg=selector,
            )

            field.focus()
            field.blur()
            page.wait_for_timeout(400)
            if len(pending) != 2:
                failures.append(
                    f"{path} {selector}: expected a same-name retry, held "
                    f"{len(pending)} validations"
                )
                continue
            pending[1].abort("failed")
            handled.append(pending[1])
            page.wait_for_timeout(100)
            state = field.evaluate(
                """input => ({
                    blocked: !input.checkValidity(),
                    invalidClass: input.classList.contains('is-invalid'),
                    told: input.parentNode.querySelector('.field__error')
                        .textContent.trim(),
                })"""
            )
            if state["blocked"]:
                failures.append(
                    f"{path} {selector}: a network failure blocked submission"
                )
            if state["invalidClass"]:
                failures.append(
                    f"{path} {selector}: a network failure left the old invalid style"
                )
            if "unavailable" not in state["told"].lower():
                failures.append(
                    f"{path} {selector}: a network failure left stale feedback "
                    f"{state['told']!r}"
                )
        finally:
            for route in pending:
                if route not in handled:
                    route.abort("failed")
            page.unroute("**/validate_user*")
    return failures


def check_true_warning_survives(page, base_url: str) -> list[str]:
    """Editing the username does not wipe a year warning that is still true.

    The complement of the check above, and the harder half to keep right.
    Clearing the last account's state has to take its error message with it:
    "This user joined Last.fm in 2015" is a claim about an account nobody is
    asking about any more. The obvious fix is to clear the year message
    outright, and that is wrong -- "Year cannot be in the future" is about
    the year, not the account, and has to survive.

    So the handler re-derives instead of clearing, and this proves the half a
    reader would not notice was broken: the message stays. No network call.
    A future year is refused by the year field alone.
    """
    page.goto(f"{base_url}/", wait_until="load")
    page.locator("#year").fill("")
    page.locator("#year").type("2099")
    before = _year_warning(page)
    if "future" not in before.lower():
        return [f"/ #year: 2099 did not raise a future-year warning, got {before!r}"]

    page.locator("#username").type("a")
    after = _year_warning(page)
    if after != before:
        return [
            f"/ #username: typing changed a year warning it does not own, "
            f"{before!r} -> {after!r}"
        ]
    return []


def _year_warning(page) -> str:
    """The text of the warning the year field writes beside itself."""
    return page.evaluate(
        """() => {
            const year = document.querySelector('#year');
            const error = year && year.parentNode.querySelector('.field__error');
            return error && error.style.display !== 'none'
                ? error.textContent
                : '';
        }"""
    )


def check_initial_visibility(page, base_url: str) -> list[str]:
    """Everything a script reveals later is really invisible on load.

    Computed display, not a class name. `.index-grid { display: grid }` beat
    Tailwind's `.hidden` because a page stylesheet loads after tailwind.css and
    wins at equal specificity, so the heatmap rendered below a hero that was
    supposed to be gone. A probe that asserted the class name passed.
    """
    failures = []
    for path, selectors in HIDDEN_ON_LOAD.items():
        page.goto(f"{base_url}{path}", wait_until="load")
        for selector in selectors:
            state = page.evaluate(
                """(selector) => {
                    const node = document.querySelector(selector);
                    if (!node) return null;
                    return getComputedStyle(node).display;
                }""",
                selector,
            )
            if state is None:
                failures.append(f"{path}: {selector} is not in the page at all")
            elif state != "none":
                failures.append(
                    f"{path}: {selector} should start hidden but computes "
                    f"display: {state}"
                )
    return failures


def check_fonts(page, base_url: str) -> list[str]:
    """Every kit family resolves to a real downloaded face.

    A browser fetches a face only when something asks for it, and at this
    point in the migration no page uses all five. So the check asks for each
    family deliberately rather than reading what the page happened to load.

    Asserting that the kit stylesheet was requested proves nothing: a
    domain-locked kit returns a stylesheet that loads no faces at all, and the
    page then falls back silently with no error anywhere.
    """
    failures = []
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
        failures.extend(
            f"{path}: font family {family} loaded no faces from the kit"
            for family, count in loaded.items()
            if not count
        )
    return failures


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


def check_loading_composition(page, base_url: str) -> list[str]:
    """The job-backed loading route uses the shared determinate wait panel."""
    loading_path = next(path for path in MIGRATED_PAGES if path.startswith("/loading?"))
    page.goto(f"{base_url}{loading_path}", wait_until="networkidle")
    page.wait_for_function(
        "document.querySelector('#progress-track')?.getAttribute('aria-valuenow') === '42'"
    )
    geometry = page.evaluate(
        """() => {
          const mark = document.querySelector('.wait-panel__mark').getBoundingClientRect();
          const track = document.querySelector('#progress-track').getBoundingClientRect();
          const phase = document.querySelector('#step-text').getBoundingClientRect();
          return {
            redundantTitle: document.querySelector('.loading-screen > h1') !== null,
            markWidth: mark.width,
            trackWidth: track.width,
            trackHeight: track.height,
            trackTop: track.top,
            phaseTop: phase.top,
            fill: getComputedStyle(document.querySelector('#progress-bar')).backgroundColor,
            fillTransform: getComputedStyle(document.querySelector('#progress-bar')).transform,
            cancel: {
              href: document.querySelector('.loading-back')?.getAttribute('href'),
              text: document.querySelector('.loading-back')?.textContent?.trim(),
            },
            primary: document.documentElement.dataset.theme === 'dark'
              ? 'rgb(179, 157, 222)'
              : 'rgb(106, 75, 175)',
          };
        }"""
    )

    failures = []
    if geometry["redundantTitle"]:
        failures.append("/loading repeats the pinwheel's loading cue as a heading")
    if abs(geometry["trackHeight"] - 3) > 0.1:
        failures.append(
            f"/loading progress hairline is {geometry['trackHeight']}px, expected 3px"
        )
    if geometry["trackWidth"] < geometry["markWidth"] * 1.75:
        failures.append(
            "/loading progress hairline is not substantially wider than the pinwheel"
        )
    if geometry["phaseTop"] <= geometry["trackTop"]:
        failures.append("/loading phase label does not follow the progress hairline")
    if geometry["fill"] != geometry["primary"]:
        failures.append(
            f"/loading progress fill is {geometry['fill']}, expected {geometry['primary']}"
        )
    if geometry["fillTransform"] == "none":
        failures.append(
            "/loading progress fill still animates layout instead of transform"
        )
    if geometry["cancel"] != {"href": "/", "text": "Cancel and return home"}:
        failures.append("/loading has no honest Cancel and return home control")

    # Use a disposable job. Opening an explicit Heatmap job intentionally
    # stores it in the browser session; deleting it afterward lets the next
    # request clear that pointer instead of making later form checks resume a
    # synthetic in-progress run.
    heatmap_job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    set_job_stat(heatmap_job_id, "pages_received", 7)
    set_job_stat(heatmap_job_id, "pages_expected", 12)
    set_job_progress(
        heatmap_job_id,
        progress=48,
        message="Reading your Last.fm history...",
        error=False,
    )
    try:
        page.goto(f"{base_url}/heatmap?job_id={heatmap_job_id}", wait_until="load")
        page.locator("#heatmap-loading-stats").wait_for(state="visible")
        heatmap_state = page.evaluate(
            """() => ({
                progress: document.querySelector('#heatmap-progress-track')
                    ?.getAttribute('aria-valuenow'),
                pages: document.querySelector('#heatmap-stat-pages')?.textContent,
                parameters: document.querySelectorAll('.heatmap-loading__params li').length,
                phase: document.querySelector('#heatmap-progress-text')?.textContent?.trim(),
                fillTransform: getComputedStyle(document.querySelector('#heatmap-progress-bar')).transform,
                cancel: {
                  href: document.querySelector('.heatmap-loading__back')?.getAttribute('href'),
                  text: document.querySelector('.heatmap-loading__back')?.textContent?.trim(),
                },
            })"""
        )
    finally:
        delete_job(heatmap_job_id)
    if heatmap_state["progress"] != "48":
        failures.append("/heatmap did not render backend-owned progress")
    if heatmap_state["pages"] != "7 / 12":
        failures.append("/heatmap did not render live page-fetch depth")
    if heatmap_state["parameters"] != 2:
        failures.append(
            "/heatmap did not retain its loading parameters (expected username and date window)"
        )
    if heatmap_state["phase"] != "Reading your Last.fm history...":
        failures.append("/heatmap phase does not name the current operation")
    if heatmap_state["fillTransform"] == "none":
        failures.append(
            "/heatmap progress fill still animates layout instead of transform"
        )
    if heatmap_state["cancel"] != {"href": "/", "text": "Cancel and return home"}:
        failures.append("/heatmap has no honest Cancel and return home control")
    return failures


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

    def measure(width: int, height: int):
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

    def measure_wide_layout():
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
                    paddingLeft: parseFloat(style.paddingLeft),
                    paddingRight: parseFloat(style.paddingRight),
                    headerGap: parseFloat(getComputedStyle(header).gap),
                    navGap: parseFloat(getComputedStyle(nav).gap),
                    rowSpread: Math.max(...tops) - Math.min(...tops),
                };
            }"""
        )

    def measure_zoom_and_transform():
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

    def measure_fixed_state(actions):
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
                };
            }"""
        )

    try:
        measured_sizes = {}
        layouts = {}
        for label, (width, height) in windows.items():
            measured_sizes[label] = measure(width, height)
            layouts[label] = measure_wide_layout()
        zoom_transform = measure_zoom_and_transform()
        at_mobile = measure(390, 844)
        mobile_layout = page.evaluate(
            """() => ({
            factor: getComputedStyle(document.querySelector('.index-grid'))
                .getPropertyValue('--index-scale').trim(),
            columns: getComputedStyle(document.querySelector('.index-grid'))
                .gridTemplateColumns.split(' ').length,
        })"""
        )
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
                        bodyPaddingTop: parseFloat(getComputedStyle(document.body).paddingTop),
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
            state: measure_fixed_state(actions)
            for state, actions in fixed_states.items()
        }
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
    finally:
        if original_viewport:
            page.set_viewport_size(original_viewport)

    failures = []
    expected_scales = {
        # The old literal 76 was the fixed --shell-height in px; Step 5
        # replaces it with clamp(4.25rem, 2.96875vw, 4.75rem), so the bar
        # height that a real window subtracts from is now width-dependent
        # too. This does not change any of the four resulting scales below:
        # the width term already wins at 1080p/1200p-measured (1.075 <
        # height term either way), and the bar clamps to its 76px ceiling
        # by 2560px width regardless (1440p, 4K), matching the old literal.
        label: min(
            2.15,
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
    at_1080p = measured_sizes["1080p"]
    layout_1080p = layouts["1080p"]
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
    baseline_scale = expected_scales["1080p"]
    for label in ("1200p measured", "1440p", "4K"):
        ratio = expected_scales[label] / baseline_scale
        for name, dimensions in scalable_dimensions.items():
            for dimension in dimensions:
                if name == "wordmark" and dimension == "height":
                    expected = at_1080p["wordmark"]["height"] * (
                        layouts[label]["heroInnerWidth"]
                        / layouts["1080p"]["heroInnerWidth"]
                    )
                elif name == "hero composition" and dimension == "height":
                    expected_mark = at_1080p["wordmark"]["height"] * (
                        layouts[label]["heroInnerWidth"]
                        / layouts["1080p"]["heroInnerWidth"]
                    )
                    expected = (
                        expected_mark
                        + (
                            at_1080p["hero composition"]["height"]
                            - at_1080p["wordmark"]["height"]
                        )
                        * ratio
                    )
                else:
                    fixed_height = {"form": 5, "form composition": 7}.get(name, 0)
                    fixed = fixed_height if dimension == "height" else 0
                    expected = (at_1080p[name][dimension] - fixed) * ratio + fixed
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
        bottom_gutter = layout["wellBottom"] - layout["formInnerBottom"]
        if abs(top_gutter - bottom_gutter) > 2:
            failures.append(
                f"/: form composition is not vertically centred at {label}: "
                f"{top_gutter:.1f}px top / {bottom_gutter:.1f}px bottom"
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

    for width, header in mobile_headers.items():
        if (
            header["scrollWidth"] > header["clientWidth"] + 1
            or not header["linksInside"]
        ):
            failures.append(
                f"/: mobile navigation requires horizontal scrolling at {width}px"
            )
        if header["rows"] != 1:
            failures.append(
                f"/: mobile navigation uses {header['rows']} row(s) at {width}px, "
                "expected one directly visible row"
            )
        if header["actionsInHeader"] or not header["actionsInMobileSlot"]:
            failures.append(
                f"/: mobile theme control remains in the header at {width}px"
            )
        if header["actionsTop"] < header["contentBottom"] - 0.5:
            failures.append(
                f"/: mobile theme control is not below the page content at {width}px"
            )
        if header["themeHeight"] < 44:
            failures.append(
                f"/: mobile theme control is only {header['themeHeight']:.1f}px high "
                f"at {width}px, expected at least 44px"
            )
        if abs(header["headerHeight"] - header["bodyPaddingTop"]) > 0.5:
            failures.append(
                f"/: mobile body offset does not match its header at {width}px"
            )

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
    header_geometry = {
        "1080p": {
            "bar": _clamp_px(4.25, 2.96875, 4.75, 1920),
            "nav height": _clamp_px(2.75, 1.875, 3.5, 1920),
            "nav width": _clamp_px(5.75, 4.53, 7.25, 1920),
            "toggle height": _clamp_px(2.25, 1.5625, 2.5, 1920) + 8.4,
        },
        "1440p": {
            "bar": _clamp_px(4.25, 2.96875, 4.75, 2560),
            "nav height": _clamp_px(2.75, 1.875, 3.5, 2560),
            "nav width": _clamp_px(5.75, 4.53, 7.25, 2560),
            "toggle height": _clamp_px(2.25, 1.5625, 2.5, 2560) + 8.4,
        },
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


def _touch_minimum_failures(
    width: int, rectangles: dict[str, dict[str, float]]
) -> list[str]:
    """Name every control whose rendered box falls below the touch minimum."""
    return [
        f"/: {selector} loses its touch minimum at {width}px"
        for selector, rectangle in rectangles.items()
        if min(rectangle.values()) < 43.9
    ]


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


def _parse_matrix_scalex(transform_str: str | None) -> float | None:
    """Extract the scaleX component from a computed CSS transform matrix."""
    if not transform_str or transform_str == "none":
        return 0.0
    match = re.match(
        r"^matrix\(\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*,",
        transform_str,
    )
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _assert_loading_progress_state(
    page,
    track_sel: str,
    bar_sel: str,
    text_sel: str,
    expected_valuenow: int,
    expected_scalex: float,
    expected_text: str,
    tolerance: float = 0.05,
) -> list[str]:
    """Assert progress bar attributes, computed transform, and phase text."""
    state = {}
    scale = None
    for _ in range(8):
        state = page.evaluate(
            """([trackSel, barSel, phaseSel]) => {
                const track = document.querySelector(trackSel);
                const bar = document.querySelector(barSel);
                const phase = document.querySelector(phaseSel);
                const style = bar ? window.getComputedStyle(bar) : null;
                return {
                    valuenow: track ? track.getAttribute('aria-valuenow') : null,
                    valuetext: track ? track.getAttribute('aria-valuetext') : null,
                    transform: style ? style.transform : null,
                    phaseText: phase ? (phase.textContent || '').trim() : null,
                };
            }""",
            [track_sel, bar_sel, text_sel],
        )
        scale = _parse_matrix_scalex(state.get("transform"))
        if scale is not None and abs(scale - expected_scalex) <= tolerance:
            break
        if hasattr(page, "wait_for_timeout"):
            page.wait_for_timeout(60)

    failures = []
    if state.get("valuenow") != str(expected_valuenow):
        failures.append(
            f"{track_sel}: aria-valuenow was {state.get('valuenow')!r}, expected {str(expected_valuenow)!r}"
        )
    if state.get("valuetext") != expected_text:
        failures.append(
            f"{track_sel}: aria-valuetext was {state.get('valuetext')!r}, expected {expected_text!r}"
        )
    if state.get("phaseText") != expected_text:
        failures.append(
            f"{text_sel}: visible text was {state.get('phaseText')!r}, expected {expected_text!r}"
        )
    if scale is None or abs(scale - expected_scalex) > tolerance:
        failures.append(
            f"{bar_sel}: scaleX was {scale}, expected approximately {expected_scalex:.4f} "
            f"(transform: {state.get('transform')!r})"
        )
    return failures


def _exercise_loading_progress_phases(page, base_url: str) -> list[str]:
    """Exercise sequential counted/uncounted phases, stale response rejection, and composition."""
    album_job_id = GATE_JOB_IDS["album"]
    heatmap_job_id = GATE_JOB_IDS["heatmap"]
    loading_path = next(path for path in MIGRATED_PAGES if path.startswith("/loading?"))
    heatmap_path = f"/heatmap?job_id={heatmap_job_id}"
    failures = []

    # 1. Repository mutation isolation
    test_phase = {
        "key": "lastfm_fetch",
        "label": "Fetching scrobbles",
        "unit": "page",
        "current": 23,
        "total": 102,
    }
    set_job_progress(
        album_job_id, progress=20, message="Fetching scrobbles", phase=test_phase
    )
    test_phase["current"] = 99
    prog_caller = get_job_progress(album_job_id)
    ctx_caller = get_job_context(album_job_id)
    if not prog_caller or prog_caller.get("phase", {}).get("current") != 23:
        failures.append("repository get_job_progress leaked caller phase mutation")
    if (
        not ctx_caller
        or ctx_caller.get("progress", {}).get("phase", {}).get("current") != 23
    ):
        failures.append("repository get_job_context leaked caller phase mutation")

    prog_view = get_job_progress(album_job_id)
    ctx_view = get_job_context(album_job_id)
    if prog_view is not None and isinstance(prog_view.get("phase"), dict):
        prog_view["phase"]["current"] = 77
    else:
        failures.append("repository get_job_progress returned invalid phase structure")
    if (
        ctx_view is not None
        and isinstance(ctx_view.get("progress"), dict)
        and isinstance(ctx_view["progress"].get("phase"), dict)
    ):
        ctx_view["progress"]["phase"]["current"] = 88
    else:
        failures.append("repository get_job_context returned invalid phase structure")

    prog_returned = get_job_progress(album_job_id)
    ctx_returned = get_job_context(album_job_id)
    if not prog_returned or prog_returned.get("phase", {}).get("current") != 23:
        failures.append("repository get_job_progress leaked returned phase mutation")
    if (
        not ctx_returned
        or ctx_returned.get("progress", {}).get("phase", {}).get("current") != 23
    ):
        failures.append(
            "repository get_job_context leaked returned context phase mutation"
        )

    # 2. Sequential payloads on Album client (/loading)
    set_job_progress(
        album_job_id,
        progress=20,
        message="Fetching scrobbles",
        phase={
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 23,
            "total": 102,
        },
    )
    page.goto(f"{base_url}{loading_path}", wait_until="load")
    page.locator("#step-text").filter(has_text="PAGE 23 / 102").wait_for(
        state="visible"
    )
    failures.extend(
        _assert_loading_progress_state(
            page,
            "#progress-track",
            "#progress-bar",
            "#step-text",
            expected_valuenow=23,
            expected_scalex=23 / 102,
            expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
        )
    )

    set_job_progress(
        album_job_id,
        progress=90,
        message="Fetching scrobbles",
        phase={
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 90,
            "total": 100,
        },
    )
    page.locator("#step-text").filter(has_text="PAGE 90 / 100").wait_for(
        state="visible"
    )
    failures.extend(
        _assert_loading_progress_state(
            page,
            "#progress-track",
            "#progress-bar",
            "#step-text",
            expected_valuenow=90,
            expected_scalex=0.9,
            expected_text="FETCHING SCROBBLES · PAGE 90 / 100",
        )
    )

    set_job_progress(
        album_job_id,
        progress=92,
        message="Counting daily scrobbles",
        phase=None,
    )
    page.locator("#step-text").filter(has_text="Counting daily scrobbles").wait_for(
        state="visible"
    )
    failures.extend(
        _assert_loading_progress_state(
            page,
            "#progress-track",
            "#progress-bar",
            "#step-text",
            expected_valuenow=92,
            expected_scalex=0.92,
            expected_text="Counting daily scrobbles",
        )
    )
    if "PAGE" in page.locator("#step-text").inner_text():
        failures.append("album uncounted frame retained stale phase fraction")

    set_job_progress(
        album_job_id,
        progress=20,
        message="Fetching scrobbles",
        phase={
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 102,
            "total": 102,
        },
    )
    page.locator("#progress-track[aria-valuenow='100']").wait_for(state="visible")
    if not page.url.startswith(f"{base_url}/loading"):
        failures.append("album phase at 100% prematurely triggered navigation")

    # 3. Sequential payloads on Heatmap client
    reset_job_state(heatmap_job_id)
    set_job_progress(
        heatmap_job_id,
        progress=20,
        message="Fetching scrobbles",
        phase={
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 23,
            "total": 102,
        },
    )
    page.goto(f"{base_url}{heatmap_path}", wait_until="load")
    page.locator("#heatmap-progress-text").filter(has_text="PAGE 23 / 102").wait_for(
        state="visible"
    )
    failures.extend(
        _assert_loading_progress_state(
            page,
            "#heatmap-progress-track",
            "#heatmap-progress-bar",
            "#heatmap-progress-text",
            expected_valuenow=23,
            expected_scalex=23 / 102,
            expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
        )
    )

    set_job_progress(
        heatmap_job_id,
        progress=90,
        message="Fetching scrobbles",
        phase={
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 90,
            "total": 100,
        },
    )
    page.locator("#heatmap-progress-text").filter(has_text="PAGE 90 / 100").wait_for(
        state="visible"
    )
    failures.extend(
        _assert_loading_progress_state(
            page,
            "#heatmap-progress-track",
            "#heatmap-progress-bar",
            "#heatmap-progress-text",
            expected_valuenow=90,
            expected_scalex=0.9,
            expected_text="FETCHING SCROBBLES · PAGE 90 / 100",
        )
    )

    set_job_progress(
        heatmap_job_id,
        progress=92,
        message="Counting daily scrobbles",
        phase=None,
    )
    page.locator("#heatmap-progress-text").filter(
        has_text="Counting daily scrobbles"
    ).wait_for(state="visible")
    failures.extend(
        _assert_loading_progress_state(
            page,
            "#heatmap-progress-track",
            "#heatmap-progress-bar",
            "#heatmap-progress-text",
            expected_valuenow=92,
            expected_scalex=0.92,
            expected_text="Counting daily scrobbles",
        )
    )
    if "PAGE" in page.locator("#heatmap-progress-text").inner_text():
        failures.append("heatmap uncounted frame retained stale phase fraction")

    set_job_progress(
        heatmap_job_id,
        progress=15,
        message="Fetching scrobbles",
        phase={
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 0,
            "total": 0,
        },
    )
    page.locator("#heatmap-progress-text").filter(
        has_text="FETCHING SCROBBLES"
    ).wait_for(state="visible")
    failures.extend(
        _assert_loading_progress_state(
            page,
            "#heatmap-progress-track",
            "#heatmap-progress-bar",
            "#heatmap-progress-text",
            expected_valuenow=15,
            expected_scalex=0.15,
            expected_text="FETCHING SCROBBLES",
        )
    )

    # 4. Composition check: single stat is centered and hidden stats reserve 0 width
    page.evaluate(
        """() => {
            const stats = document.querySelector('#heatmap-loading-stats');
            if (stats) stats.classList.remove('hidden');
            const pages = document.querySelector('[data-heatmap-stat="pages"]');
            if (pages) pages.classList.remove('hidden');
            const scrobbles = document.querySelector('[data-heatmap-stat="scrobbles"]');
            if (scrobbles) scrobbles.classList.add('hidden');
            const days = document.querySelector('[data-heatmap-stat="days"]');
            if (days) days.classList.add('hidden');
        }"""
    )
    stat_layout = page.evaluate(
        """() => {
            const pages = document.querySelector('[data-heatmap-stat="pages"]');
            const scrobbles = document.querySelector('[data-heatmap-stat="scrobbles"]');
            const days = document.querySelector('[data-heatmap-stat="days"]');
            const container = document.querySelector('#heatmap-loading-stats');
            const pr = pages ? pages.getBoundingClientRect() : null;
            const sr = scrobbles ? scrobbles.getBoundingClientRect() : null;
            const dr = days ? days.getBoundingClientRect() : null;
            const cr = container ? container.getBoundingClientRect() : null;
            return {
                pagesWidth: pr ? pr.width : 0,
                scrobblesWidth: sr ? sr.width : 0,
                daysWidth: dr ? dr.width : 0,
                containerWidth: cr ? cr.width : 0,
                pagesCenter: pr && cr ? (pr.left + pr.width / 2) - (cr.left + cr.width / 2) : 999,
            };
        }"""
    )
    if stat_layout["scrobblesWidth"] != 0 or stat_layout["daysWidth"] != 0:
        failures.append("heatmap hidden stats reserved space in single-stat layout")
    if abs(stat_layout["pagesCenter"]) > 3.0:
        failures.append(
            f"heatmap single stat is not centered: offset {stat_layout['pagesCenter']:.1f}px"
        )

    # 5. Out-of-order response rejection and job replacement
    replacement_job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    set_job_progress(
        replacement_job_id,
        progress=80,
        message="Fetching scrobbles",
        phase={
            "key": "lastfm_fetch",
            "label": "Fetching scrobbles",
            "unit": "page",
            "current": 80,
            "total": 100,
        },
    )
    held_routes = []

    def intercept_progress(route):
        if heatmap_job_id in route.request.url and not held_routes:
            held_routes.append(route)
        else:
            route.continue_()

    page.route("**/progress?job_id=*", intercept_progress)
    try:
        # Load original heatmap job; its first poll will be held
        page.goto(f"{base_url}{heatmap_path}", wait_until="load")
        page.wait_for_timeout(100)
        # Navigate to replacement job while old job poll is held
        page.goto(f"{base_url}/heatmap?job_id={replacement_job_id}", wait_until="load")
        page.locator("#heatmap-progress-text").filter(
            has_text="PAGE 80 / 100"
        ).wait_for(state="visible")

        # Fulfill held response for the replaced job with stale 20%
        if held_routes:
            held_routes[0].fulfill(
                status=200,
                content_type="application/json",
                body=(
                    '{"progress": 20, "phase": {"key": "lastfm_fetch", '
                    '"label": "Fetching scrobbles", "unit": "page", '
                    '"current": 20, "total": 100}}'
                ),
            )
            page.wait_for_timeout(150)
            current_valuenow = page.locator("#heatmap-progress-track").get_attribute(
                "aria-valuenow"
            )
            if current_valuenow == "20":
                failures.append(
                    "stale out-of-order progress response regressed aria-valuenow"
                )
            if "PAGE 20" in page.locator("#heatmap-progress-text").inner_text():
                failures.append(
                    "stale out-of-order progress response regressed visible text"
                )
    finally:
        page.unroute("**/progress?job_id=*")
        delete_job(replacement_job_id)

    return failures


def _exercise_pipeline_state_machines(page, base_url: str) -> list[str]:
    """Both polling clients reach success, retryable, and terminal states."""
    album_job_id = GATE_JOB_IDS["album"]
    heatmap_job_id = GATE_JOB_IDS["heatmap"]
    loading_path = next(path for path in MIGRATED_PAGES if path.startswith("/loading?"))
    failures = []

    # Keep the production delay in source while making the gate deterministic
    # and fast. Accelerate 1000ms/2000ms polling and 3000ms redirect in the gate.
    page.add_init_script(
        """(() => {
            const nativeTimeout = window.setTimeout;
            window.setTimeout = (callback, delay, ...args) => {
                if (delay === 3000) return nativeTimeout(callback, 0, ...args);
                if (delay === 1000) return nativeTimeout(callback, 50, ...args);
                return nativeTimeout(callback, delay, ...args);
            };
            const nativeInterval = window.setInterval;
            window.setInterval = (callback, delay, ...args) => {
                if (delay === 2000) return nativeInterval(callback, 50, ...args);
                return nativeInterval(callback, delay, ...args);
            };
            window.__scrobbleGateFastRedirect = true;

            // A completed saved Heatmap job should reveal its cached result
            // without painting the loading panel first. Observe class changes
            // from before production DOMContentLoaded listeners run; a final
            // display check would miss the brief flash once the result wins.
            window.__scrobbleGateHeatmapLoadingPaints = 0;
            document.addEventListener('DOMContentLoaded', () => {
                const loading = document.querySelector('#heatmap-loading');
                if (!loading) return;
                const recordVisible = () => {
                    if (getComputedStyle(loading).display !== 'none') {
                        window.__scrobbleGateHeatmapLoadingPaints += 1;
                    }
                };
                new MutationObserver(recordVisible).observe(loading, {
                    attributes: true,
                    attributeFilter: ['class'],
                });
                recordVisible();
            });
        })();"""
    )

    failures.extend(_exercise_loading_progress_phases(page, base_url))

    reset_job_state(album_job_id)
    set_job_results(
        album_job_id,
        [
            {
                "artist": "Gate Artist",
                "album": "Gate Album",
                "play_count": 12,
                "play_time": "42m",
                "play_time_seconds": 2520,
                "release_date": "2025-01-01",
                "album_image": "",
                "spotify_id": "gate-album",
            }
        ],
    )
    set_job_progress(album_job_id, progress=100, message="Done", error=False)
    page.goto(f"{base_url}{loading_path}", wait_until="load")
    if not page.evaluate("window.__scrobbleGateFastRedirect === true"):
        failures.append("pipeline timer init script did not execute")
    page.wait_for_url(f"{base_url}/results")
    if "Gate Album" not in page.locator("body").inner_text():
        failures.append("album success did not render the saved result")

    reset_job_state(album_job_id)
    set_job_error(album_job_id, "lastfm_rate_limited")
    page.goto(f"{base_url}{loading_path}", wait_until="load")
    page.locator("#retry-button").wait_for(state="visible")
    if not page.url.startswith(f"{base_url}/loading"):
        failures.append("album retryable failure left the loading route")

    reset_job_state(album_job_id)
    set_job_error(album_job_id, "user_not_found", username="frontend-gate")
    page.goto(f"{base_url}{loading_path}", wait_until="load")
    page.wait_for_url(f"{base_url}/results")
    if not page.locator(".error-icon").is_visible():
        failures.append("album terminal failure did not reach its results error")

    heatmap_path = f"/heatmap?job_id={heatmap_job_id}"
    # The owner's side-by-side report came from a realistic 1080p browser
    # content box. The result should use that available width as confidently
    # as the index composition measured by the large-display check.
    page.set_viewport_size({"width": 1920, "height": 945})
    reset_job_state(heatmap_job_id)
    set_job_results(
        heatmap_job_id,
        {
            "username": "frontend-gate",
            "from_date": "2025-01-01",
            "to_date": "2025-12-31",
            "total_scrobbles": 4,
            "daily_counts": {"2025-01-01": 4},
        },
    )
    set_job_progress(heatmap_job_id, progress=100, message="Done", error=False)
    page.goto(f"{base_url}{heatmap_path}", wait_until="load")
    page.locator("#heatmap-result.is-handing-off").wait_for(state="visible")
    handoff_state = page.evaluate(
        """() => ({
            root: document.querySelector('#heatmap-result')?.classList.contains('heatmap-fade'),
            headline: document.querySelector('#heatmap-result-headline')?.classList.contains('heatmap-fade'),
            frame: document.querySelector('#heatmap-result-frame')?.classList.contains('heatmap-fade'),
        })"""
    )
    page.locator("#heatmap-result-frame svg").wait_for(state="visible")
    result_scale = page.evaluate(
        """() => {
            const frame = document.querySelector('#heatmap-result-frame')
                .getBoundingClientRect();
            const stage = document.querySelector('#heatmap-result')
                .getBoundingClientRect();
            const cell = document.querySelector('.heatmap-cell').getBoundingClientRect();
            const headline = document.querySelector('#heatmap-result-headline');
            const username = headline.querySelector('.heatmap-headline-username');
            return {
                frameRatio: frame.width / innerWidth,
                frameCenterOffset: (frame.left + frame.width / 2)
                    - (stage.left + stage.width / 2),
                cellWidth: cell.width,
                usernameColor: getComputedStyle(username).color,
                headlineColor: getComputedStyle(headline).color,
                usernameStyle: getComputedStyle(username).fontStyle,
            };
        }"""
    )
    loading_paints = page.evaluate("window.__scrobbleGateHeatmapLoadingPaints || 0")
    if loading_paints:
        failures.append(
            "cached heatmap restoration painted the loading panel before its result"
        )
    if handoff_state != {"root": True, "headline": False, "frame": False}:
        failures.append("cached heatmap result does not use one root handoff")
    if result_scale["frameRatio"] < 0.70 or result_scale["cellWidth"] < 22:
        failures.append(
            "desktop heatmap result is too small for its available viewport: "
            f"{result_scale['frameRatio']:.3f} wide with "
            f"{result_scale['cellWidth']:.1f}px cells"
        )
    if result_scale["cellWidth"] > 32:
        failures.append(
            f"desktop heatmap cells are oversized at {result_scale['cellWidth']:.1f}px"
        )
    if abs(result_scale["frameCenterOffset"]) > 1:
        failures.append("desktop heatmap frame is not centred in the viewport")
    if (
        result_scale["usernameStyle"] != "normal"
        or result_scale["usernameColor"] != result_scale["headlineColor"]
    ):
        failures.append("heatmap username retains accent colour or italic styling")
    header_wordmark_display = page.locator(".site-header__home").evaluate(
        "element => getComputedStyle(element).display"
    )
    if header_wordmark_display == "none":
        failures.append("heatmap success did not restore the header wordmark")

    reset_job_state(heatmap_job_id)
    set_job_error(heatmap_job_id, "lastfm_rate_limited")
    page.goto(f"{base_url}{heatmap_path}", wait_until="load")
    page.locator("#heatmap-error").wait_for(state="visible")
    if not page.locator("#heatmap-retry-btn").is_visible():
        failures.append("heatmap retryable failure did not offer Retry")

    reset_job_state(heatmap_job_id)
    set_job_error(heatmap_job_id, "user_not_found", username="frontend-gate")
    page.goto(f"{base_url}{heatmap_path}", wait_until="load")
    page.locator("#heatmap-error").wait_for(state="visible")
    if page.locator("#heatmap-retry-btn").is_visible():
        failures.append("heatmap terminal failure incorrectly offered Retry")
    return failures


def check_pipeline_state_machines(page, base_url: str) -> list[str]:
    """Exercise both clients on a disposable page and restore job fixtures.

    Playwright cannot remove a page init script. The accelerated redirect is
    therefore installed on a short-lived probe instead of the profile page
    used by later checks.
    """
    probe = page.context.new_page()
    try:
        probe.route("http://localhost:8400/**", lambda route: route.abort())
        return _exercise_pipeline_state_machines(probe, base_url)
    finally:
        probe.close()
        reset_job_state(GATE_JOB_IDS["album"])
        set_job_progress(
            GATE_JOB_IDS["album"],
            progress=42,
            message="Fetching scrobbles - page 21 / 50",
            error=False,
        )
        reset_job_state(GATE_JOB_IDS["heatmap"])


def check_artist_spotlight_rotation(page, base_url: str) -> list[str]:
    """Render five sampled artists, hydrate them once, and observe rotation."""
    job_id = create_job(
        {
            "username": "frontend-gate",
            "year": 2025,
            "sort_mode": "playcount",
            "release_scope": "all",
            "min_plays": 1,
            "min_tracks": 1,
            "limit_results": "all",
            "mode": "album",
        }
    )
    failures = []
    try:
        set_job_results(
            job_id,
            [
                {
                    "artist": f"Rotation Artist {index}",
                    "album": f"Rotation Album {index}",
                    "play_count": 20 - index,
                    "play_time": "42m",
                    "play_time_seconds": 2520 - index,
                    "release_date": "2025-01-01",
                    "album_image": "",
                    "spotify_id": f"rotation-album-{index}",
                }
                for index in range(10)
            ],
        )
        set_job_progress(job_id, progress=100, message="Done", error=False)
        page.add_init_script(
            """(() => {
                const nativeInterval = window.setInterval;
                const nativeFetch = window.fetch.bind(window);
                window.__spotlightRequests = [];
                window.__spotlightFirstResolved = false;
                window.setInterval = (callback, delay, ...args) => {
                    if (delay === 7000) return window.setTimeout(callback, 500, ...args);
                    return nativeInterval(callback, delay, ...args);
                };
                window.fetch = (resource, options) => {
                    const url = String(resource);
                    if (!url.includes('/api/artist_spotlight?')) {
                        return nativeFetch(resource, options);
                    }
                    const requestIndex = window.__spotlightRequests.push(url) - 1;
                    const response = {
                        ok: true,
                        json: async () => requestIndex === 0
                            ? {
                                image_url: 'data:image/svg+xml,<svg/>',
                                spotify_url: 'https://open.spotify.com/artist/stale',
                            }
                            : {image_url: null, spotify_url: null},
                    };
                    if (requestIndex !== 0) return Promise.resolve(response);
                    return new Promise((resolve) => {
                        window.setTimeout(() => {
                            window.__spotlightFirstResolved = true;
                            resolve(response);
                        }, 900);
                    });
                };
            })();"""
        )
        page.goto(
            f"{base_url}/results?job_id={job_id}",
            wait_until="domcontentloaded",
            timeout=10_000,
        )

        candidates = page.evaluate("window.APP_DATA.spotlight_artists")
        if len(candidates) != 5 or len({item["name"] for item in candidates}) != 5:
            failures.append("results did not expose five unique spotlight artists")

        for _ in range(20):
            spotlight_requests = page.evaluate("window.__spotlightRequests")
            if len(spotlight_requests) >= 5:
                break
            page.wait_for_timeout(50)
        if len(spotlight_requests) != 5:
            failures.append(
                f"spotlight hydrated {len(spotlight_requests)} artists instead of 5"
            )

        initial_index = page.locator("#artist-spotlight-card").get_attribute(
            "data-spotlight-index"
        )
        try:
            page.wait_for_function(
                "initial => document.querySelector('#artist-spotlight-card')?.dataset.spotlightIndex !== initial",
                arg=initial_index,
                timeout=2000,
            )
        except Exception:  # noqa: BLE001 - converted to an actionable gate failure
            failures.append("artist spotlight did not rotate through its sample")
        else:
            active_state = page.evaluate(
                """() => {
                    const card = document.querySelector('#artist-spotlight-card');
                    return {index: card?.dataset.spotlightIndex, artist: card?.dataset.artist};
                }"""
            )
            page.wait_for_function(
                "() => window.__spotlightFirstResolved",
                timeout=2_000,
            )
            if page.evaluate(
                """expected => {
                    const card = document.querySelector('#artist-spotlight-card');
                    return card?.dataset.spotlightIndex !== expected.index
                        || card?.dataset.artist !== expected.artist;
                }""",
                active_state,
            ):
                failures.append("late spotlight hydration replaced the active artist")
    finally:
        delete_job(job_id)
    return failures


#: Every check the gate runs, with the viewports each one runs at.
#:
#: Width changes nothing for stylesheet links, font downloads or the
#: validation request state machines, so those use the smallest useful set.
#: Layout and theme checks run on both sides of the design breakpoint. Touch
#: targets run on a narrow phone and a wide coarse-pointer device, because
#: pointer capability rather than window width is the contract.
CHECKS = (
    ("stylesheet isolation", check_stylesheet_isolation, (DESKTOP,)),
    ("fonts", check_fonts, (DESKTOP,)),
    ("theme tokens", check_theme_tokens, (DESKTOP, MOBILE)),
    ("divider contrast", check_divider_contrast, (DESKTOP,)),
    ("index design tokens", check_index_design_tokens, (DESKTOP, MOBILE)),
    ("theme persistence", check_theme_persistence, (DESKTOP, MOBILE)),
    ("body font", check_body_font, (DESKTOP, MOBILE)),
    ("shell text scaling", check_shell_scales_with_text, (DESKTOP, MOBILE)),
    ("loading composition", check_loading_composition, (DESKTOP, MOBILE)),
    ("initial visibility", check_initial_visibility, (DESKTOP, MOBILE)),
    ("validation feedback", check_validation_feedback, (DESKTOP,)),
    ("private profiles", check_private_profile_is_blocked, (DESKTOP,)),
    ("index entrance motion", check_index_entrance_motion, (DESKTOP,)),
    ("true warning survives", check_true_warning_survives, (DESKTOP,)),
    ("validator outage", check_validator_outage_is_recoverable, (DESKTOP,)),
    ("mark follows theme", check_mark_follows_theme, (DESKTOP,)),
    (
        "theme survives blocked storage",
        check_theme_survives_blocked_storage,
        (DESKTOP,),
    ),
    ("validator race", check_stale_validator_failure_is_discarded, (DESKTOP,)),
    (
        "validator network failure",
        check_current_validator_failure_replaces_old_verdict,
        (DESKTOP,),
    ),
    ("touch targets", check_touch_targets, (MOBILE, TOUCH_WIDE)),
    (
        "destination empty states",
        check_destination_empty_states,
        (DESKTOP, MOBILE),
    ),
    ("pipeline state machines", check_pipeline_state_machines, (DESKTOP,)),
    ("artist spotlight rotation", check_artist_spotlight_rotation, (DESKTOP,)),
    ("large display scale parity", check_large_display_scale_parity, (DESKTOP,)),
)

#: How many check runs a clean pass performs. Printed so a check that silently
#: stops running is visible as a smaller number.
PLANNED_RUNS = len(BROWSER_NAMES) * sum(len(viewports) for _, _, viewports in CHECKS)


def run_checks(new_page, base_url: str) -> list[str]:
    """Run every check against every profile it claims, collecting failures.

    Takes a factory rather than a page, because a coarse pointer cannot be
    switched on mid-session: touch emulation belongs to a browser context, so
    each profile needs its own page.

    A check that raises is reported as a failure and the run continues. A bare
    call would let one TypeError skip every later check and surface as a
    traceback, which reads as "the gate crashed" rather than "the gate found
    three problems".

    Every failure carries its profile. "the submit button is 38px" is not
    actionable until you know which device produced it.
    """
    failures = []
    for viewport, spec in VIEWPORTS.items():
        try:
            page = new_page(spec)
            # Impeccable Live is a developer overlay injected into base.html
            # while visual review is active. Keep the production UI gate
            # independent from that local instrumentation.
            page.route("http://localhost:8400/**", lambda route: route.abort())
        except Exception as exc:  # noqa: BLE001 - same rule as a check fault
            failures.append(
                f"the {viewport} profile could not be opened: "
                f"{type(exc).__name__}: {exc}"
            )
            continue
        for name, check, viewports in CHECKS:
            if viewport not in viewports:
                continue
            try:
                results = check(page, base_url)
            except Exception as exc:  # noqa: BLE001 - any check fault is a failure
                failures.append(
                    f"{name} [{viewport}]: raised {type(exc).__name__}: {exc}"
                )
                continue
            failures.extend(f"{name} [{viewport}]: {failure}" for failure in results)
    return failures


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the developer-facing options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--headed",
        action="store_true",
        help="show the browser window while the checks run",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run every check against a freshly served app and report all failures."""
    args = _parse_args(argv)
    try:
        sync_playwright = _load_playwright()
        with serve_app() as base_url, sync_playwright() as playwright:
            failures = []
            for browser_name in BROWSER_NAMES:
                browser = None
                try:
                    browser = _launch_browser(
                        playwright, browser_name, headless=not args.headed
                    )
                    # One context per profile, all closed with this engine.
                    results = run_checks(
                        lambda spec, browser=browser: browser.new_context(
                            **spec
                        ).new_page(),
                        base_url,
                    )
                    failures.extend(f"{browser_name}: {result}" for result in results)
                except Exception as exc:  # noqa: BLE001 - continue with the next engine
                    failures.append(
                        f"{browser_name}: raised {type(exc).__name__}: {exc}"
                    )
                finally:
                    if browser is not None:
                        try:
                            browser.close()
                        except Exception as exc:  # noqa: BLE001 - report cleanup faults
                            failures.append(
                                f"{browser_name}: close raised {type(exc).__name__}: {exc}"
                            )
    except FrontendGateError as exc:
        print(f"[frontend_gate] ERROR: {exc}", file=sys.stderr)
        return 1

    if failures:
        for failure in failures:
            print(f"[frontend_gate] FAIL {failure}", file=sys.stderr)
        return 1

    print(
        f"[frontend_gate] {len(CHECKS)} checks passed in {PLANNED_RUNS} runs "
        f"across {', '.join(BROWSER_NAMES)}; profiles: {', '.join(VIEWPORTS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
