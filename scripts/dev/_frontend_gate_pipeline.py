"""Pipeline checks: loading composition, progress state machines, spotlight.

A slice of the frontend gate (F-B21-51). The state-machine checks write real
job state through `scrobblescope.repositories` and watch the page follow it,
because the defects they guard -- a stale message outliving its phase, a
replaced job still delivering progress -- exist only in that interaction.
"""

from __future__ import annotations

import re

from scripts.dev._frontend_gate_shared import GATE_JOB_IDS, MIGRATED_PAGES
from scrobblescope.repositories import (
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

ALBUM_PROGRESS_TRACK = "#progress-track"
ALBUM_PROGRESS_BAR = "#progress-bar"
ALBUM_PROGRESS_TEXT = "#step-text"
HEATMAP_PROGRESS_TRACK = "#heatmap-progress-track"
HEATMAP_PROGRESS_BAR = "#heatmap-progress-bar"
HEATMAP_PROGRESS_TEXT = "#heatmap-progress-text"
FETCHING_SCROBBLES = "Fetching scrobbles"
COUNTING_SCROBBLES = "Counting daily scrobbles"
PAGE_23_OF_102 = "PAGE 23 / 102"
PAGE_90_OF_100 = "PAGE 90 / 100"


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
        page.locator("#heatmap-progress-text").filter(
            has_text="Reading your Last.fm history..."
        ).wait_for(state="visible")
        heatmap_state = page.evaluate(
            """() => ({
                progress: document.querySelector('#heatmap-progress-track')
                    ?.getAttribute('aria-valuenow'),
                counterCount: document.querySelectorAll('[data-heatmap-stat]').length,
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
    if heatmap_state["counterCount"] != 0:
        failures.append("/heatmap repeats phase counts in a counter rail")
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

    failures.extend(_check_phase_repository_isolation(album_job_id))
    failures.extend(
        _exercise_album_progress(page, base_url, album_job_id, loading_path)
    )
    failures.extend(
        _exercise_heatmap_progress(page, base_url, heatmap_job_id, heatmap_path)
    )
    failures.extend(
        _exercise_replaced_job_progress(page, base_url, heatmap_job_id, heatmap_path)
    )
    return failures


def _check_phase_repository_isolation(album_job_id) -> list[str]:
    """Verify caller and returned phase objects cannot mutate stored progress."""
    failures = []
    # 1. Repository mutation isolation
    test_phase = {
        "key": "lastfm_fetch",
        "label": FETCHING_SCROBBLES,
        "unit": "page",
        "current": 23,
        "total": 102,
    }
    set_job_progress(
        album_job_id, progress=20, message=FETCHING_SCROBBLES, phase=test_phase
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

    return failures


def _exercise_counted_progress(
    page, base_url, job_id, path, selectors, client
) -> list[str]:
    """Exercise the shared counted-to-uncounted transition on either client."""
    track, bar, text = selectors
    failures = []
    set_job_progress(
        job_id,
        progress=20,
        message=FETCHING_SCROBBLES,
        phase={
            "key": "lastfm_fetch",
            "label": FETCHING_SCROBBLES,
            "unit": "page",
            "current": 23,
            "total": 102,
        },
    )
    page.goto(f"{base_url}{path}", wait_until="load")
    page.locator(text).filter(has_text=PAGE_23_OF_102).wait_for(state="visible")
    failures.extend(
        _assert_loading_progress_state(
            page,
            track,
            bar,
            text,
            expected_valuenow=23,
            expected_scalex=23 / 102,
            expected_text="FETCHING SCROBBLES · PAGE 23 / 102",
        )
    )

    set_job_progress(
        job_id,
        progress=90,
        message=FETCHING_SCROBBLES,
        phase={
            "key": "lastfm_fetch",
            "label": FETCHING_SCROBBLES,
            "unit": "page",
            "current": 90,
            "total": 100,
        },
    )
    page.locator(text).filter(has_text=PAGE_90_OF_100).wait_for(state="visible")
    failures.extend(
        _assert_loading_progress_state(
            page,
            track,
            bar,
            text,
            expected_valuenow=90,
            expected_scalex=0.9,
            expected_text="FETCHING SCROBBLES · PAGE 90 / 100",
        )
    )

    set_job_progress(
        job_id,
        progress=92,
        message=COUNTING_SCROBBLES,
        phase=None,
    )
    page.locator(text).filter(has_text=COUNTING_SCROBBLES).wait_for(state="visible")
    failures.extend(
        _assert_loading_progress_state(
            page,
            track,
            bar,
            text,
            expected_valuenow=92,
            expected_scalex=0.92,
            expected_text=COUNTING_SCROBBLES,
        )
    )
    if "PAGE" in page.locator(text).inner_text():
        failures.append(f"{client} uncounted frame retained stale phase fraction")

    return failures


def _exercise_album_progress(page, base_url, album_job_id, loading_path) -> list[str]:
    """Drive counted, uncounted and complete phases on the album page."""
    failures = []
    failures.extend(
        _exercise_counted_progress(
            page,
            base_url,
            album_job_id,
            loading_path,
            (ALBUM_PROGRESS_TRACK, ALBUM_PROGRESS_BAR, ALBUM_PROGRESS_TEXT),
            "album",
        )
    )
    set_job_progress(
        album_job_id,
        progress=20,
        message=FETCHING_SCROBBLES,
        phase={
            "key": "lastfm_fetch",
            "label": FETCHING_SCROBBLES,
            "unit": "page",
            "current": 102,
            "total": 102,
        },
    )
    page.locator("#progress-track[aria-valuenow='100']").wait_for(state="visible")
    if not page.url.startswith(f"{base_url}/loading"):
        failures.append("album phase at 100% prematurely triggered navigation")

    return failures


def _exercise_heatmap_progress(
    page, base_url, heatmap_job_id, heatmap_path
) -> list[str]:
    """Drive counted, uncounted and zero-total phases on the heatmap page."""
    failures = []
    reset_job_state(heatmap_job_id)
    failures.extend(
        _exercise_counted_progress(
            page,
            base_url,
            heatmap_job_id,
            heatmap_path,
            (HEATMAP_PROGRESS_TRACK, HEATMAP_PROGRESS_BAR, HEATMAP_PROGRESS_TEXT),
            "heatmap",
        )
    )
    set_job_progress(
        heatmap_job_id,
        progress=15,
        message=FETCHING_SCROBBLES,
        phase={
            "key": "lastfm_fetch",
            "label": FETCHING_SCROBBLES,
            "unit": "page",
            "current": 0,
            "total": 0,
        },
    )
    page.locator(HEATMAP_PROGRESS_TEXT).filter(has_text="FETCHING SCROBBLES").wait_for(
        state="visible"
    )
    failures.extend(
        _assert_loading_progress_state(
            page,
            HEATMAP_PROGRESS_TRACK,
            HEATMAP_PROGRESS_BAR,
            HEATMAP_PROGRESS_TEXT,
            expected_valuenow=15,
            expected_scalex=0.15,
            expected_text="FETCHING SCROBBLES",
        )
    )

    return failures


def _exercise_replaced_job_progress(
    page, base_url, heatmap_job_id, heatmap_path
) -> list[str]:
    """Hold an old poll while replacing the job, then check stale rejection."""
    failures = []
    # 5. Out-of-order response rejection and job replacement
    replacement_job_id = create_job({"username": "frontend-gate", "mode": "heatmap"})
    set_job_progress(
        replacement_job_id,
        progress=80,
        message=FETCHING_SCROBBLES,
        phase={
            "key": "lastfm_fetch",
            "label": FETCHING_SCROBBLES,
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
        page.locator(HEATMAP_PROGRESS_TEXT).filter(has_text="PAGE 80 / 100").wait_for(
            state="visible"
        )

        # Fulfill held response for the replaced job with stale 20%
        if held_routes:
            held_routes[0].fulfill(
                status=200,
                json={
                    "progress": 20,
                    "phase": {
                        "key": "lastfm_fetch",
                        "label": FETCHING_SCROBBLES,
                        "unit": "page",
                        "current": 20,
                        "total": 100,
                    },
                },
            )
            page.wait_for_timeout(150)
            current_valuenow = page.locator(HEATMAP_PROGRESS_TRACK).get_attribute(
                "aria-valuenow"
            )
            if current_valuenow == "20":
                failures.append(
                    "stale out-of-order progress response regressed aria-valuenow"
                )
            if "PAGE 20" in page.locator(HEATMAP_PROGRESS_TEXT).inner_text():
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

        # Bound before the poll loop so the post-loop read is never unbound:
        # a static analyzer treats a loop body as possibly-zero-iteration,
        # and an init-script failure would otherwise surface as NameError
        # instead of the hydration-count failure below.
        spotlight_requests: list = []
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
