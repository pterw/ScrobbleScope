"""Repository-owned frontend gate for the Batch 21 Tailwind migration.

`pytest` sees Python and `pre-commit` sees text. Neither can see what a browser
computes, so the deliverables that matter most in a CSS migration -- which
stylesheet a page loads, what a token resolves to, whether the theme survives a
reload, whether a font actually arrives -- have nothing enforcing them.

This script closes that gap. It starts the real Flask app on a loopback port it
owns, drives a real Chromium, and asserts those properties. It needs no
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
    reset_job_state,
    set_job_error,
    set_job_progress,
    set_job_results,
    set_job_stat,
)

SETUP_COMMAND = "python -m playwright install chromium"

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
MIGRATED_PAGES = ["/", ERROR_PAGE_PATH]

#: Throwaway jobs owned by serve_app and driven by pipeline checks.
GATE_JOB_IDS: dict[str, str] = {}

#: Pages still served by Bootstrap. Move each one into MIGRATED_PAGES in the
#: work package that migrates it.
#:
#: Results and Unmatched remain on Bootstrap until their work packages.
#: Their friendly no-job pages render error.html, so those routes do not prove
#: the job-backed templates use the right framework yet.
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
        '[data-mode-hero="heatmap"]',
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


def _launch_chromium(playwright, *, headless: bool = True):
    """Launch Chromium, translating a missing browser build into guidance.

    Pinning the package does not fetch the browser. The two failures look
    completely different but have the same remedy.
    """
    try:
        return playwright.chromium.launch(headless=headless)
    except Exception as exc:
        raise FrontendGateError(
            f"Chromium is not available to Playwright. Run: {SETUP_COMMAND}"
        ) from exc


@contextmanager
def serve_app() -> Iterator[str]:
    """Serve the real app on a loopback port for the duration of the block.

    Port 0 asks the OS for a free port, so parallel runs cannot collide. The
    shutdown sits in a finally block: a failing check must never leave a
    listening socket behind.
    """
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

    server = make_server("127.0.0.1", 0, create_app())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        MIGRATED_PAGES.remove(loading_path)
        ALL_PAGES.remove(loading_path)
        delete_job(loading_job_id)
        delete_job(heatmap_job_id)
        GATE_JOB_IDS.clear()


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
        context.add_init_script(_BLOCK_STORAGE)
        probe = context.new_page()
        try:
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
    """The header grows with root text without changing the shared page."""
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
                    expected: (mobile ? 3.75 : 4.25) * 20,
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
            markWidth: mark.width,
            trackWidth: track.width,
            trackHeight: track.height,
            trackTop: track.top,
            phaseTop: phase.top,
            fill: getComputedStyle(document.querySelector('#progress-bar')).backgroundColor,
            primary: document.documentElement.dataset.theme === 'dark'
              ? 'rgb(179, 157, 222)'
              : 'rgb(106, 75, 175)',
          };
        }"""
    )

    failures = []
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
        message="Fetching Last.fm page 7/12...",
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
                backHome: document.querySelector('.heatmap-loading__back')?.getAttribute('href'),
            })"""
        )
    finally:
        delete_job(heatmap_job_id)
    if heatmap_state["progress"] != "48":
        failures.append("/heatmap did not render backend-owned progress")
    if heatmap_state["pages"] != "7 / 12":
        failures.append("/heatmap did not render live page-fetch depth")
    if heatmap_state["parameters"] != 3:
        failures.append("/heatmap did not retain its loading parameters")
    if heatmap_state["backHome"] != "/":
        failures.append("/heatmap loading state has no route-backed home escape")
    return failures


def check_large_display_scale_parity(page, base_url: str) -> list[str]:
    """A 4K canvas preserves the established 1080p component scale.

    Responsive placement may use the extra room, but the wordmark, type,
    navigation, form, and controls must not independently inflate. This is a
    CSS-pixel comparison: it protects proportions without pretending that
    browser or operating-system display scaling belongs to the page.
    """
    original_viewport = page.viewport_size
    selectors = {
        "wordmark": ".index-hero__mark",
        "headline": ".index-hero__headline",
        "form": ".ss-card",
        "input": ".ss-input",
        "mode tab": ".mode-pill",
        "page navigation": ".site-header__nav-link",
    }
    dimensions = {
        "wordmark": ("width", "height"),
        # A heading is a flow box: its available width follows the responsive
        # column while its type scale stays fixed.
        "headline": ("fontSize",),
        "form": ("width",),
        "input": ("width", "height", "fontSize"),
        "mode tab": ("width", "height", "fontSize"),
        "page navigation": ("width", "height", "fontSize"),
    }

    def measure(width: int, height: int):
        page.set_viewport_size({"width": width, "height": height})
        page.goto(f"{base_url}/", wait_until="load")
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
                    }];
                })
            )""",
            selectors,
        )

    try:
        at_1080p = measure(1920, 1080)
        at_4k = measure(3840, 2160)
    finally:
        if original_viewport:
            page.set_viewport_size(original_viewport)

    failures = []
    for name in selectors:
        baseline = at_1080p.get(name)
        large = at_4k.get(name)
        if baseline is None or large is None:
            failures.append(f"/: {name} could not be measured at both display sizes")
            continue
        for dimension in dimensions[name]:
            if abs(baseline[dimension] - large[dimension]) > 0.5:
                failures.append(
                    f"/: {name} {dimension} changes from "
                    f"{baseline[dimension]:.1f}px at 1080p to "
                    f"{large[dimension]:.1f}px at 4K"
                )
    return failures


def _exercise_pipeline_state_machines(page, base_url: str) -> list[str]:
    """Both polling clients reach success, retryable, and terminal states."""
    album_job_id = GATE_JOB_IDS["album"]
    heatmap_job_id = GATE_JOB_IDS["heatmap"]
    loading_path = next(path for path in MIGRATED_PAGES if path.startswith("/loading?"))
    failures = []

    # Keep the production delay in source while making the gate deterministic
    # and fast. The one-second poll cadence is unchanged.
    page.add_init_script(
        """() => {
            const nativeTimeout = window.setTimeout;
            window.setTimeout = (callback, delay, ...args) =>
                nativeTimeout(callback, delay === 3000 ? 0 : delay, ...args);
        }"""
    )

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
    reset_job_state(heatmap_job_id)
    set_job_results(
        heatmap_job_id,
        {
            "username": "frontend-gate",
            "from_date": "2025-01-01",
            "to_date": "2025-01-01",
            "total_scrobbles": 4,
            "daily_counts": {"2025-01-01": 4},
        },
    )
    set_job_progress(heatmap_job_id, progress=100, message="Done", error=False)
    page.goto(f"{base_url}{heatmap_path}", wait_until="load")
    page.locator("#heatmap-result-frame svg").wait_for(state="visible")

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
    """Exercise both clients and restore the shared loading fixture."""
    try:
        return _exercise_pipeline_state_machines(page, base_url)
    finally:
        reset_job_state(GATE_JOB_IDS["album"])
        set_job_progress(
            GATE_JOB_IDS["album"],
            progress=42,
            message="Fetching scrobbles - page 21 / 50",
            error=False,
        )
        reset_job_state(GATE_JOB_IDS["heatmap"])


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
    ("index design tokens", check_index_design_tokens, (DESKTOP, MOBILE)),
    ("theme persistence", check_theme_persistence, (DESKTOP, MOBILE)),
    ("body font", check_body_font, (DESKTOP, MOBILE)),
    ("shell text scaling", check_shell_scales_with_text, (DESKTOP, MOBILE)),
    ("loading composition", check_loading_composition, (DESKTOP, MOBILE)),
    ("initial visibility", check_initial_visibility, (DESKTOP, MOBILE)),
    ("validation feedback", check_validation_feedback, (DESKTOP,)),
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
    ("pipeline state machines", check_pipeline_state_machines, (DESKTOP,)),
    ("large display scale parity", check_large_display_scale_parity, (DESKTOP,)),
)

#: How many check runs a clean pass performs. Printed so a check that silently
#: stops running is visible as a smaller number.
PLANNED_RUNS = sum(len(viewports) for _, _, viewports in CHECKS)


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
            browser = _launch_chromium(playwright, headless=not args.headed)
            try:
                # One context per profile, all closed with the browser.
                failures = run_checks(
                    lambda spec: browser.new_context(**spec).new_page(),
                    base_url,
                )
            finally:
                browser.close()
    except FrontendGateError as exc:
        print(f"[frontend_gate] ERROR: {exc}", file=sys.stderr)
        return 1

    if failures:
        for failure in failures:
            print(f"[frontend_gate] FAIL {failure}", file=sys.stderr)
        return 1

    print(
        f"[frontend_gate] {len(CHECKS)} checks passed in {PLANNED_RUNS} runs "
        f"across {', '.join(VIEWPORTS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
