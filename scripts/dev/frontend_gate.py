"""Repository-owned frontend gate for the Batch 21 Tailwind migration.

`pytest` sees Python and `pre-commit` sees text. Neither can see what a browser
computes, so the deliverables that matter most in a CSS migration -- which
stylesheet a page loads, what a token resolves to, whether the theme survives a
reload, whether a font actually arrives -- have nothing enforcing them.

This script closes that gap. It starts the real Flask app on a loopback port it
owns, drives a real Chromium, and asserts those properties. It needs no
separately running server and no MCP service, so it runs the same way locally
and in CI.

Every check runs at a real viewport, desktop and mobile, and every failure says
which one it came from. The gate grows with the migration: each work package
adds its page to MIGRATED_PAGES, and adds a check when it ships something the
existing ones cannot see.
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

SETUP_COMMAND = "python -m playwright install chromium"

#: Cool-grey surfaces the warm themes replaced. Batch criterion 2 forbids them.
FORBIDDEN_SURFACES = ("rgb(248, 249, 250)", "rgb(18, 18, 18)")

#: Every family in Adobe Fonts kit rwy8ghw that the design system uses.
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
MIGRATED_PAGES = ("/", ERROR_PAGE_PATH)

#: Pages still served by Bootstrap. Move each one into MIGRATED_PAGES in the
#: work package that migrates it.
#:
#: Empty since WP-3, and it stays empty until a GET route exists for the three
#: remaining templates. loading.html, results.html and unmatched.html render
#: only from a POST with session state, so a browser cannot reach them by URL
#: and no check here has ever covered them. WP-4 needs a route before the gate
#: can see the page it migrates.
LEGACY_PAGES = ()

#: Consumed by check_stylesheet_isolation. Exactly one framework stylesheet is
#: a claim about every page, migrated or not, so this check takes both lists.
ALL_PAGES = LEGACY_PAGES + MIGRATED_PAGES

#: The two widths every visual check runs at.
#:
#: Every check this batch built ran at Playwright's 1280x720 default, so
#: mobile was verified by owner review and nothing else. The design has one
#: breakpoint, 860px -- docs/design/README.md "Responsive" -- so a width each
#: side of it is the whole matrix. 390x844 is the design's mobile reference
#: canvas.
DESKTOP = "desktop"
MOBILE = "mobile"
VIEWPORTS = {
    DESKTOP: {"width": 1280, "height": 720},
    MOBILE: {"width": 390, "height": 844},
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
    server = make_server("127.0.0.1", 0, create_app())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


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


def check_theme_persistence(page, base_url: str) -> list[str]:
    """Toggling the theme then reloading keeps it. This is what F-B21-2 broke.

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
    for path in MIGRATED_PAGES:
        page.goto(f"{base_url}{path}", wait_until="load")
        toggle = page.locator("[data-theme-toggle]")
        if toggle.count() == 0:
            failures.append(f"{path}: no [data-theme-toggle] control found")
            continue

        before = page.evaluate("() => document.documentElement.dataset.theme")
        try:
            toggle.first.click(timeout=TOGGLE_TIMEOUT_MS)
        except Exception as exc:  # noqa: BLE001 - any failure to click is a failure
            failures.append(
                f"{path}: the theme toggle could not be clicked: "
                f"{type(exc).__name__}"
            )
            continue

        toggled = page.evaluate("() => document.documentElement.dataset.theme")
        if toggled == before:
            failures.append(
                f"{path}: toggling did not change data-theme " f"(stayed {before!r})"
            )
            continue

        page.reload(wait_until="load")
        after = page.evaluate("() => document.documentElement.dataset.theme")
        if after != toggled:
            failures.append(
                f"{path}: theme did not survive reload: "
                f"{toggled!r} became {after!r}"
            )
    return failures


def check_touch_targets(page, base_url: str) -> list[str]:
    """Every tappable element is at least 44px on its smaller side.

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


#: Every check the gate runs, with the viewports each one runs at.
#:
#: Width changes nothing for the first two: a link set and a font download are
#: the same at any size. The rest can all differ across the 860px breakpoint,
#: so they run twice. Touch targets are a mobile question only.
CHECKS = (
    ("stylesheet isolation", check_stylesheet_isolation, (DESKTOP,)),
    ("fonts", check_fonts, (DESKTOP,)),
    ("theme tokens", check_theme_tokens, (DESKTOP, MOBILE)),
    ("theme persistence", check_theme_persistence, (DESKTOP, MOBILE)),
    ("body font", check_body_font, (DESKTOP, MOBILE)),
    ("initial visibility", check_initial_visibility, (DESKTOP, MOBILE)),
    ("validation feedback", check_validation_feedback, (DESKTOP,)),
    ("touch targets", check_touch_targets, (MOBILE,)),
)

#: How many check runs a clean pass performs. Printed so a check that silently
#: stops running is visible as a smaller number.
PLANNED_RUNS = sum(len(viewports) for _, _, viewports in CHECKS)


def run_checks(page, base_url: str) -> list[str]:
    """Run every check at every viewport it claims, collecting all failures.

    A check that raises is reported as a failure and the run continues. A bare
    call would let one TypeError skip every later check and surface as a
    traceback, which reads as "the gate crashed" rather than "the gate found
    three problems".

    Every failure carries its viewport. "the submit button is 38px" is not
    actionable until you know which width produced it.
    """
    failures = []
    for viewport, size in VIEWPORTS.items():
        try:
            page.set_viewport_size(size)
        except Exception as exc:  # noqa: BLE001 - same rule as a check fault
            failures.append(
                f"the {viewport} viewport could not be set: "
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
                failures = run_checks(browser.new_page(), base_url)
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
        f"[frontend_gate] {len(CHECKS)} checks passed "
        f"in {PLANNED_RUNS} runs across desktop and mobile"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
