"""Repository-owned frontend gate for the Batch 21 Tailwind migration.

`pytest` sees Python and `pre-commit` sees text. Neither can see what a browser
computes, so the deliverables that matter most in a CSS migration -- which
stylesheet a page loads, what a token resolves to, whether the theme survives a
reload, whether a font actually arrives -- have nothing enforcing them.

This script closes that gap. It starts the real Flask app on a loopback port it
owns, drives a real Chromium, and asserts those four properties. It needs no
separately running server and no MCP service, so it runs the same way locally
and in CI.

Checks 5 and 6 from the batch definition belong to WP-5 and WP-6, and land with
the work they check.
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
MIGRATED_PAGES = (ERROR_PAGE_PATH,)

#: Pages still served by Bootstrap. Move each one into MIGRATED_PAGES in the
#: work package that migrates it.
LEGACY_PAGES = ("/",)

#: Consumed by check_stylesheet_isolation. Exactly one framework stylesheet is
#: a claim about every page, migrated or not, so this check takes both lists.
ALL_PAGES = LEGACY_PAGES + MIGRATED_PAGES


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
    """
    page.goto(f"{base_url}/", wait_until="load")
    toggle = page.locator("[data-theme-toggle]")
    if toggle.count() == 0:
        return ["no [data-theme-toggle] control found on the index page"]

    before = page.evaluate("() => document.documentElement.dataset.theme")
    try:
        toggle.first.click(timeout=TOGGLE_TIMEOUT_MS)
    except Exception as exc:  # noqa: BLE001 - any failure to click is a failure
        return [f"the theme toggle could not be clicked: {type(exc).__name__}"]

    toggled = page.evaluate("() => document.documentElement.dataset.theme")
    if toggled == before:
        return [f"toggling did not change data-theme (stayed {before!r})"]

    page.reload(wait_until="load")
    after = page.evaluate("() => document.documentElement.dataset.theme")
    if after != toggled:
        return [f"theme did not survive reload: {toggled!r} became {after!r}"]
    return []


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


#: Every check the gate runs, in the order it runs them.
CHECKS = (
    ("stylesheet isolation", check_stylesheet_isolation),
    ("theme tokens", check_theme_tokens),
    ("theme persistence", check_theme_persistence),
    ("fonts", check_fonts),
)


def run_checks(page, base_url: str) -> list[str]:
    """Run every check and collect all failures rather than stopping at one.

    A check that raises is reported as a failure and the run continues. A bare
    call would let one TypeError skip every later check and surface as a
    traceback, which reads as "the gate crashed" rather than "the gate found
    three problems".
    """
    failures = []
    for name, check in CHECKS:
        try:
            results = check(page, base_url)
        except Exception as exc:  # noqa: BLE001 - any check fault is a failure
            failures.append(f"{name}: raised {type(exc).__name__}: {exc}")
            continue
        failures.extend(f"{name}: {failure}" for failure in results)
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

    print(f"[frontend_gate] {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
