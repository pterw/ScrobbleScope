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

# create_app also refuses to start without the three provider keys outside dev
# mode (F-SWE-4), and CI's secrets arrive empty in exactly the same way. The
# gate renders pages from seeded jobs and never calls a provider, so a
# placeholder is enough to boot the application.
for _key in ("LASTFM_API_KEY", "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"):
    if not os.environ.get(_key):
        os.environ[_key] = "frontend-gate-placeholder"

from app import create_app  # noqa: E402

# Re-exported so the split stays invisible to callers, per F-B21-51: a facade
# keeps the stable public names and `worktree_guard.py` is the precedent. Four
# of these are unused inside this module, which is why `F401` is suppressed --
# without it ruff strips the re-export and the existing gate tests stop
# importing.
from scripts.dev._frontend_gate_assets import (  # noqa: E402, F401
    BOOTSTRAP_MARKER,
    TAILWIND_MARKER,
    check_stylesheet_isolation,
)
from scripts.dev._frontend_gate_colour import (  # noqa: E402, F401
    _clamp_px,
    _composite_over,
    _contrast_ratio,
    _divider_contrast_failure,
    _is_forbidden_surface,
    _parse_rgb_string,
    _relative_luminance,
    _worst_divider_contrast,
)
from scripts.dev._frontend_gate_forms import (  # noqa: E402, F401
    HIDDEN_ON_LOAD,
    check_current_validator_failure_replaces_old_verdict,
    check_initial_visibility,
    check_private_profile_is_blocked,
    check_stale_validator_failure_is_discarded,
    check_true_warning_survives,
    check_validation_feedback,
    check_validator_outage_is_recoverable,
)
from scripts.dev._frontend_gate_layout import (  # noqa: E402, F401
    DEFAULT_STATES,
    FONTS_READY_EXPRESSION,
    INTERACTIVE_SELECTOR,
    MIN_TOUCH_TARGET_PX,
    REQUIRED_FONT_FAMILIES,
    TOUCH_TARGET_STATES,
    check_body_font,
    check_destination_empty_states,
    check_fonts,
    check_large_display_scale_parity,
    check_shell_scales_with_text,
    check_touch_targets,
)
from scripts.dev._frontend_gate_pipeline import (  # noqa: E402, F401
    ALBUM_PROGRESS_BAR,
    ALBUM_PROGRESS_TEXT,
    ALBUM_PROGRESS_TRACK,
    COUNTING_SCROBBLES,
    FETCHING_SCROBBLES,
    HEATMAP_PROGRESS_BAR,
    HEATMAP_PROGRESS_TEXT,
    HEATMAP_PROGRESS_TRACK,
    PAGE_23_OF_102,
    PAGE_90_OF_100,
    check_artist_spotlight_rotation,
    check_loading_composition,
    check_pipeline_state_machines,
)
from scripts.dev._frontend_gate_results import (  # noqa: E402
    check_release_check_disclosure,
    check_results_interactions,
    check_results_provider_attribution,
)

# Re-exported: the facade keeps the public names stable (F-B21-51).
from scripts.dev._frontend_gate_shared import (  # noqa: E402, F401
    ALL_PAGES,
    ERROR_PAGE_PATH,
    GATE_JOB_IDS,
    LEGACY_PAGES,
    MIGRATED_PAGES,
    TOGGLE_TIMEOUT_MS,
    _reach_state,
)
from scripts.dev._frontend_gate_theme import (  # noqa: E402, F401
    FORBIDDEN_SURFACES,
    SET_THEME_EXPRESSION,
    THEME_EXPRESSION,
    check_divider_contrast,
    check_heatmap_export_header_matches_page,
    check_heatmap_zero_cells_follow_theme,
    check_index_design_tokens,
    check_index_entrance_motion,
    check_mark_follows_theme,
    check_theme_persistence,
    check_theme_survives_blocked_storage,
    check_theme_tokens,
)
from scripts.dev._frontend_gate_unmatched import (  # noqa: E402, F401
    UNMATCHED_MIN_TITLE_WIDTH,
    UNMATCHED_SWEEP_WIDTHS,
    UNMATCHED_TWO_PANEL_MIN,
    check_unmatched_report,
)
from scrobblescope.repositories import (  # noqa: E402
    create_job,
    delete_job,
    set_job_progress,
)

BROWSER_NAMES = ("chromium", "firefox")
SETUP_COMMAND = "python -m playwright install chromium firefox"


#: Fail-fast navigation. Playwright's 30s default turned one stalled
#: subresource into a 30s wait per check, and the shared page let one
#: wedge cascade through the rest of the run. 10s bounds the damage.
NAVIGATION_TIMEOUT_MS = 10_000


def install_cdn_routes(page, live_fonts: bool = False) -> None:
    """Keep developer-only origins out of the gate's pages.

    Impeccable Live is a developer overlay injected into base.html while
    visual review is active; the gate must stay independent of it, so its
    origin is aborted. ``live_fonts`` skips that for a local calibration run.

    The Adobe Fonts kit always loads from its real origin: its families are
    licensed web fonts, and re-hosting or synthesizing them would misdeclare
    licensed typefaces (owner ruling 2026-09-07, no exceptions per family).
    A stall there costs the page its webfonts, never the gate its pass,
    because check_fonts reports misses as advisory WARN lines.

    The cdnjs Bootstrap fixture this used to serve was removed on 2026-09-21:
    no template requests Bootstrap, and check_stylesheet_isolation reads link
    hrefs, so it still catches a page that reintroduces it.
    """
    if live_fonts:
        return
    page.route("http://localhost:8400/**", lambda route: route.abort())


#: ``serve_app`` temporarily extends module-level page inventories for the
#: loading fixture. Serialising that context keeps two in-process gate runs
#: from clearing each other's job IDs or removing each other's route.
_SERVE_APP_LOCK = threading.Lock()

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


#: Group names for the check grouping below. A stalled check can leave
#: its page wedged (a half-loaded stylesheet, a leaked poller); the
#: 2026-09-07 CI run cascaded one navigation timeout through every later
#: check on the same page object. Each group therefore runs on a fresh
#: browser context so the damage ends with the group that caused it.
STATIC_ASSETS = "static assets & tokens"
THEME_MOTION = "theme & motion"
FORMS_VALIDATION = "forms & validation"
LAYOUT_PIPELINE = "layout & pipeline"

#: Every check the gate runs, with the viewports each one runs at and the
#: group that owns it. Groups are derived from this tuple -- there is no
#: second declared copy to fall out of sync (owner ruling: testing the
#: grouping would be testing a test).
#:
#: Width changes nothing for stylesheet links, font downloads or the
#: validation request state machines, so those use the smallest useful set.
#: Layout and theme checks run on both sides of the design breakpoint. Touch
#: targets run on a narrow phone and a wide coarse-pointer device, because
#: pointer capability rather than window width is the contract.
CHECKS = (
    ("stylesheet isolation", check_stylesheet_isolation, (DESKTOP,), STATIC_ASSETS),
    ("fonts", check_fonts, (DESKTOP,), STATIC_ASSETS),
    ("body font", check_body_font, (DESKTOP, MOBILE), STATIC_ASSETS),
    ("theme tokens", check_theme_tokens, (DESKTOP, MOBILE), STATIC_ASSETS),
    ("divider contrast", check_divider_contrast, (DESKTOP,), STATIC_ASSETS),
    (
        "index design tokens",
        check_index_design_tokens,
        (DESKTOP, MOBILE),
        STATIC_ASSETS,
    ),
    ("mark follows theme", check_mark_follows_theme, (DESKTOP,), STATIC_ASSETS),
    (
        "heatmap zero cells follow theme",
        check_heatmap_zero_cells_follow_theme,
        (DESKTOP,),
        THEME_MOTION,
    ),
    (
        "heatmap export header matches page",
        check_heatmap_export_header_matches_page,
        (DESKTOP,),
        THEME_MOTION,
    ),
    ("theme persistence", check_theme_persistence, (DESKTOP, MOBILE), THEME_MOTION),
    ("true warning survives", check_true_warning_survives, (DESKTOP,), THEME_MOTION),
    (
        "theme survives blocked storage",
        check_theme_survives_blocked_storage,
        (DESKTOP,),
        THEME_MOTION,
    ),
    ("index entrance motion", check_index_entrance_motion, (DESKTOP,), THEME_MOTION),
    ("validation feedback", check_validation_feedback, (DESKTOP,), FORMS_VALIDATION),
    (
        "private profiles",
        check_private_profile_is_blocked,
        (DESKTOP,),
        FORMS_VALIDATION,
    ),
    (
        "validator outage",
        check_validator_outage_is_recoverable,
        (DESKTOP,),
        FORMS_VALIDATION,
    ),
    (
        "validator race",
        check_stale_validator_failure_is_discarded,
        (DESKTOP,),
        FORMS_VALIDATION,
    ),
    (
        "validator network failure",
        check_current_validator_failure_replaces_old_verdict,
        (DESKTOP,),
        FORMS_VALIDATION,
    ),
    (
        "initial visibility",
        check_initial_visibility,
        (DESKTOP, MOBILE),
        FORMS_VALIDATION,
    ),
    (
        "shell text scaling",
        check_shell_scales_with_text,
        (DESKTOP, MOBILE),
        LAYOUT_PIPELINE,
    ),
    (
        "loading composition",
        check_loading_composition,
        (DESKTOP, MOBILE),
        LAYOUT_PIPELINE,
    ),
    ("touch targets", check_touch_targets, (MOBILE, TOUCH_WIDE), LAYOUT_PIPELINE),
    (
        "results interactions",
        check_results_interactions,
        (DESKTOP, MOBILE),
        LAYOUT_PIPELINE,
    ),
    (
        "results provider attribution",
        check_results_provider_attribution,
        (DESKTOP,),
        LAYOUT_PIPELINE,
    ),
    (
        "release check disclosure",
        check_release_check_disclosure,
        (DESKTOP,),
        LAYOUT_PIPELINE,
    ),
    (
        "destination empty states",
        check_destination_empty_states,
        (DESKTOP, MOBILE),
        LAYOUT_PIPELINE,
    ),
    (
        "unmatched report",
        check_unmatched_report,
        (DESKTOP, MOBILE, TOUCH_WIDE),
        LAYOUT_PIPELINE,
    ),
    (
        "pipeline state machines",
        check_pipeline_state_machines,
        (DESKTOP,),
        LAYOUT_PIPELINE,
    ),
    (
        "artist spotlight rotation",
        check_artist_spotlight_rotation,
        (DESKTOP,),
        LAYOUT_PIPELINE,
    ),
    (
        "large display scale parity",
        check_large_display_scale_parity,
        (DESKTOP,),
        LAYOUT_PIPELINE,
    ),
)

#: Groups in execution order, derived from CHECKS. dict preserves insertion
#: order, so the first occurrence of a group fixes its position. The
#: accumulator is honestly a list dict; only the final comprehension produces
#: the promised tuple shape, so the annotation is true at every read site.
_GROUP_MEMBERS: dict[str, list[str]] = {}
for _entry in CHECKS:
    _GROUP_MEMBERS.setdefault(_entry[3], []).append(_entry[0])
CHECK_GROUPS: dict[str, tuple[str, ...]] = {
    _group: tuple(members) for _group, members in _GROUP_MEMBERS.items()
}
del _GROUP_MEMBERS

#: Firefox is a regression canary, not a second acceptance gate: the
#: 2026-09-01 remediation plan measured both engines agreeing within 0.1px
#: at four window profiles, so a full second pass doubles the stall surface
#: for near-zero signal. Group A (STATIC_ASSETS) is the fastest set and the
#: one the CDN fixtures serve, so it is the canary's scope. Chromium runs
#: everything (None means all groups).
BROWSER_SCOPES: dict[str, tuple[str, ...] | None] = {
    "chromium": None,
    "firefox": (STATIC_ASSETS,),
}


def groups_for(browser_name: str) -> tuple[str, ...]:
    """Groups this engine runs, in execution order."""
    scope = BROWSER_SCOPES.get(browser_name)
    if scope is None:
        return tuple(CHECK_GROUPS)
    return tuple(group for group in CHECK_GROUPS if group in scope)


#: How many check runs a clean pass performs. Printed so a check that silently
#: stops running is visible as a smaller number.
PLANNED_RUNS = sum(
    1
    for _b in BROWSER_NAMES
    for _e in CHECKS
    for _v in _e[2]
    if groups_for(_b) and _e[3] in groups_for(_b)
)


def run_checks(
    new_page, base_url: str, group_order: Sequence[str] | None = None
) -> list[str]:
    """Run every check group against every profile it claims, in order.

    Takes a factory rather than a page, because a coarse pointer cannot be
    switched on mid-session: touch emulation belongs to a browser context, so
    each profile needs its own page. Each group opens a fresh page through the
    factory, so a check that wedges its page (a stalled navigation, a leaked
    poller) cannot poison the groups that follow it.

    A check that raises is reported as a failure and the run continues. A bare
    call would let one TypeError skip every later check and surface as a
    traceback, which reads as "the gate crashed" rather than "the gate found
    three problems".

    Every failure carries its profile. "the submit button is 38px" is not
    actionable until you know which device produced it.
    """
    live_groups = tuple(dict.fromkeys(entry[3] for entry in CHECKS))
    failures = []
    for group in group_order or live_groups:
        claimed_in_group = [entry for entry in CHECKS if entry[3] == group]
        for viewport, spec in VIEWPORTS.items():
            claimed = [entry for entry in claimed_in_group if viewport in entry[2]]
            if claimed:
                failures.extend(
                    _run_profile_checks(
                        new_page, base_url, group, viewport, spec, claimed
                    )
                )
    return failures


def _run_profile_checks(
    new_page, base_url, group, viewport, spec, claimed
) -> list[str]:
    """Open one isolated group/profile and report setup faults without aborting."""
    try:
        page = new_page(spec)
    except Exception as exc:  # noqa: BLE001 - any factory fault is a gate failure
        return [
            f"{group} [{viewport}]: context could not be opened: "
            f"{type(exc).__name__}: {exc}"
        ]
    failures = []
    for name, check, _viewports, _group in claimed:
        failures.extend(_run_check(page, base_url, name, viewport, check))
    return failures


def _run_check(page, base_url, name, viewport, check) -> list[str]:
    """Keep one failed diagnostic from hiding later checks on the same profile."""
    try:
        results = check(page, base_url)
    except Exception as exc:  # noqa: BLE001 - any check fault is a failure
        return [f"{name} [{viewport}]: raised {type(exc).__name__}: {exc}"]
    return [f"{name} [{viewport}]: {failure}" for failure in results]


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the developer-facing options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--headed",
        action="store_true",
        help="show the browser window while the checks run",
    )
    parser.add_argument(
        "--live-fonts",
        action="store_true",
        help="let the Impeccable Live developer overlay load (local visual review only)",
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

                    # One context per group-profile, all closed with this
                    # engine. The 10s navigation timeout bounds a stalled
                    # subresource to one failed check instead of a cascade.
                    # (Timeout is page-level: Playwright's context has no
                    # default_navigation_timeout kwarg.)
                    def open_page(spec, browser=browser):
                        context = browser.new_context(**spec)
                        page = context.new_page()
                        page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
                        install_cdn_routes(page, live_fonts=args.live_fonts)
                        return page

                    results = run_checks(
                        open_page,
                        base_url,
                        group_order=groups_for(browser_name),
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

    # Read the canary through groups_for, whose return type is a plain
    # tuple: BROWSER_SCOPES carries a None sentinel for "run everything"
    # (chromium's full pass), so subscripting its values directly is a
    # type error. Firefox always declares an explicit canary scope.
    canary_groups = groups_for("firefox")
    canary = canary_groups[0] if canary_groups else "no groups"
    print(
        f"[frontend_gate] {len(CHECKS)} checks passed in {PLANNED_RUNS} runs "
        f"across {', '.join(BROWSER_NAMES)} "
        f"({canary} canary on firefox); "
        f"profiles: {', '.join(VIEWPORTS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
