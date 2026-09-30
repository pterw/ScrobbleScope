"""Parity and behaviour tests for the spotlight-photo slice of the frontend
gate (F-B21-60 part 1)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from scripts.dev import _frontend_gate_spotlight_photo, frontend_gate
from tests.scripts.dev.gate_parity import defined_names

CHECKS = (
    "check_artist_spotlight_photo_has_no_crop_overlay_or_animation",
    "check_artist_spotlight_card_hidden_with_no_photo",
)
CONSTANTS = (
    "RESULTS_PATH",
    "SQUARE_PHOTO_DATA_URL",
)
HELPERS = (
    "_seed_spotlight_job",
    "_install_spotlight_fetch_mock",
)


@pytest.mark.parametrize("name", (*CHECKS, *CONSTANTS, *HELPERS))
def test_the_slice_defines_the_name(name: str) -> None:
    assert name in defined_names(_frontend_gate_spotlight_photo)
    assert name not in defined_names(frontend_gate)


@pytest.mark.parametrize("name", CHECKS)
def test_the_name_resolves_through_the_gate_module(name: str) -> None:
    assert getattr(frontend_gate, name) is getattr(_frontend_gate_spotlight_photo, name)


def test_results_path_is_the_migrated_results_route() -> None:
    assert _frontend_gate_spotlight_photo.RESULTS_PATH == "/results"


def test_square_photo_data_url_declares_equal_width_and_height() -> None:
    url = _frontend_gate_spotlight_photo.SQUARE_PHOTO_DATA_URL
    assert "width='300'" in url
    assert "height='300'" in url


def test_seed_spotlight_job_seeds_several_artists_and_marks_it_done() -> None:
    with (
        patch(
            "scripts.dev._frontend_gate_spotlight_photo.jobs.create",
            return_value="job-1",
        ) as create_job,
        patch("scripts.dev._frontend_gate_spotlight_photo.jobs.succeed") as succeed,
    ):
        job_id = _frontend_gate_spotlight_photo._seed_spotlight_job()

    assert job_id == "job-1"
    create_job.assert_called_once()
    succeed.assert_called_once()
    assert succeed.call_args.args[0] == "job-1"
    assert succeed.call_args.args[2] == "Done"
    results = succeed.call_args.args[1]
    artists = {entry["artist"] for entry in results}
    assert len(artists) > 1, "the seeded job must sample more than one artist"


def test_install_spotlight_fetch_mock_carries_the_photo_url() -> None:
    page = MagicMock()
    _frontend_gate_spotlight_photo._install_spotlight_fetch_mock(
        page, "https://example.com/photo.svg"
    )
    script = page.add_init_script.call_args.args[0]
    assert '"https://example.com/photo.svg"' in script
    assert "/api/artist_spotlight?" in script
    assert "delay === 7000" in script


def test_install_spotlight_fetch_mock_carries_no_photo_as_null() -> None:
    page = MagicMock()
    _frontend_gate_spotlight_photo._install_spotlight_fetch_mock(page, None)
    script = page.add_init_script.call_args.args[0]
    assert "window.__spotlightPhotoUrl = null" in script


def test_install_spotlight_fetch_mock_counts_requests_and_answers() -> None:
    page = MagicMock()
    _frontend_gate_spotlight_photo._install_spotlight_fetch_mock(page, None)
    script = page.add_init_script.call_args.args[0]
    assert "window.__spotlightRequests += 1" in script
    assert "window.__spotlightResponses += 1" in script


def _geometry(**overrides) -> dict:
    """A reading of a 3:2 photo painted whole in a 100px box."""
    geometry = {
        "noBox": False,
        "objectFit": "contain",
        "painted": {"left": 0.0, "top": 16.7, "right": 100.0, "bottom": 83.3},
        "clip": {"left": 0.0, "top": 0.0, "right": 100.0, "bottom": 100.0},
        "moved": [],
    }
    geometry.update(overrides)
    return geometry


def test_a_photo_painted_whole_inside_its_clip_passes() -> None:
    assert _frontend_gate_spotlight_photo.photo_crop_failures(_geometry()) == []


def test_a_photo_painted_past_its_clip_fails_even_with_object_fit_contain() -> None:
    failures = _frontend_gate_spotlight_photo.photo_crop_failures(
        _geometry(painted={"left": -15.0, "top": 10.0, "right": 115.0, "bottom": 90.0})
    )
    assert len(failures) == 1
    assert "leaves the 100.0x100.0 box that clips it on the left, right" in failures[0]


@pytest.mark.parametrize(
    "moved",
    [
        "the photo has transform matrix(1.3, 0, 0, 1.3, 0, 0)",
        "the photo has clipPath x",
    ],
)
def test_a_scaled_or_clipped_photo_fails_whatever_it_paints(moved: str) -> None:
    failures = _frontend_gate_spotlight_photo.photo_crop_failures(
        _geometry(moved=[moved])
    )
    assert failures == [f"spotlight photo is cropped: {moved}"]


def test_a_photo_with_object_fit_cover_fails() -> None:
    failures = _frontend_gate_spotlight_photo.photo_crop_failures(
        _geometry(objectFit="cover")
    )
    assert failures == ["spotlight photo object-fit is 'cover', not 'contain'"]


def test_a_photo_with_no_clipping_box_fails_instead_of_passing() -> None:
    failures = _frontend_gate_spotlight_photo.photo_crop_failures({"noBox": True})
    assert failures == [
        "spotlight photo has no .spotlight-image-box ancestor to clip it"
    ]


def _check_page(*, waits=None, evaluate=None) -> MagicMock:
    page = MagicMock()
    if waits is not None:
        page.wait_for_function.side_effect = waits
    page.evaluate.side_effect = evaluate
    return page


def _run(check, page):
    with (
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._seed_spotlight_job",
            return_value="job-1",
        ),
        patch("scripts.dev._frontend_gate_spotlight_photo.jobs.delete") as delete_job,
    ):
        failures = check(page, "http://127.0.0.1:0")
    delete_job.assert_called_once_with("job-1")
    return failures


def test_both_photo_checks_wait_for_the_photo_to_decode_before_measuring() -> None:
    for check in (
        _frontend_gate_spotlight_photo.check_artist_spotlight_photo_has_no_crop_overlay_or_animation,
        _frontend_gate_spotlight_photo.check_artist_spotlight_photo_not_cropped_when_non_square,
    ):
        page = _check_page(waits=[TimeoutError("never decoded")])
        assert _run(check, page) == ["spotlight photo never loaded a confirmed image"]
        script = page.wait_for_function.call_args.args[0]
        assert "img.complete" in script
        assert "img.naturalWidth > 0" in script
        page.evaluate.assert_not_called()


def test_the_no_photo_check_fails_when_hydration_never_ran() -> None:
    page = _check_page(
        waits=[TimeoutError("no requests")], evaluate=lambda *a: [5, 0, 0]
    )
    failures = _run(
        _frontend_gate_spotlight_photo.check_artist_spotlight_card_hidden_with_no_photo,
        page,
    )
    assert failures == [
        "spotlight hydration never ran, so a hidden card proves nothing: "
        "5 candidates, 0 requests, 0 answers"
    ]


def test_the_no_photo_check_waits_for_every_answer_then_reads_the_card() -> None:
    page = _check_page(
        evaluate=lambda script, *a: "none" if "display" in script else None
    )
    failures = _run(
        _frontend_gate_spotlight_photo.check_artist_spotlight_card_hidden_with_no_photo,
        page,
    )
    assert failures == []
    script = page.wait_for_function.call_args.args[0]
    assert "__spotlightRequests >= seeded" in script
    assert "__spotlightResponses >= seeded" in script
    page.wait_for_timeout.assert_not_called()


def test_the_no_photo_check_fails_on_a_visible_card() -> None:
    page = _check_page(
        evaluate=lambda script, *a: "block" if "display" in script else None
    )
    failures = _run(
        _frontend_gate_spotlight_photo.check_artist_spotlight_card_hidden_with_no_photo,
        page,
    )
    assert failures == ["spotlight card is visible ('block') with no confirmed photo"]


def _steady_samples() -> list[dict]:
    """A window in which the artist changed and the opacity never did."""
    return [
        {"opacity": ["1", "1"], "index": str(index), "ticks": index}
        for index in (0, 0, 1, 1, 2)
    ]


def _crop_overlay_page(overlap: list, motion: list) -> MagicMock:
    def evaluate(script, *args):
        if script is _frontend_gate_spotlight_photo._PHOTO_PAINT_JS:
            return _geometry()
        if "naturalWidth" in script and "getBoundingClientRect" in script:
            return {
                "naturalWidth": 300,
                "naturalHeight": 300,
                "width": 100.0,
                "height": 100.0,
            }
        if script is _frontend_gate_spotlight_photo._PHOTO_OVERLAY_JS:
            return overlap
        if script is _frontend_gate_spotlight_photo._PHOTO_MOTION_JS:
            return motion
        return _steady_samples()

    return _check_page(evaluate=evaluate)


def test_a_pseudo_element_scrim_and_a_transform_animation_are_reported() -> None:
    check = _frontend_gate_spotlight_photo.check_artist_spotlight_photo_has_no_crop_overlay_or_animation
    failures = _run(
        check,
        _crop_overlay_page(["photo box ::after"], ["photo animation drift"]),
    )
    assert failures == [
        "spotlight photo is overlaid by: photo box ::after",
        "spotlight photo is animated: photo animation drift",
    ]
    assert _run(check, _crop_overlay_page([], [])) == []


def test_the_overlay_and_motion_probes_read_pseudo_elements_and_motion() -> None:
    overlay = _frontend_gate_spotlight_photo._PHOTO_OVERLAY_JS
    motion = _frontend_gate_spotlight_photo._PHOTO_MOTION_JS
    assert "getComputedStyle(owner, pseudo)" in overlay
    assert "['::before', '::after']" in overlay
    assert "animationName" in motion
    assert "'transform', 'filter'" in motion


def _samples(*rows) -> list[dict]:
    return [
        {"artist": artist, "height": height, "broken": broken}
        for artist, height, broken in rows
    ]


def test_a_steady_card_with_no_broken_word_passes() -> None:
    samples = _samples(("A", 200.0, []), ("B", 200.2, []))
    assert (
        _frontend_gate_spotlight_photo.spotlight_layout_failures(
            samples, "at 1024px", 2
        )
        == []
    )


def test_a_card_that_changes_height_between_candidates_fails() -> None:
    samples = _samples(("A", 224.6, []), ("B", 240.6, []))
    failures = _frontend_gate_spotlight_photo.spotlight_layout_failures(
        samples, "at 1024px", 2
    )
    assert failures == [
        "at 1024px: the card height changes between candidates: [224.6, 240.6]"
    ]


def test_a_word_broken_inside_the_name_fails_once_per_artist_and_word() -> None:
    samples = _samples(
        ("Radiohead", 200.0, ["Radiohead"]),
        ("Radiohead", 200.0, ["Radiohead"]),
        ("Other", 200.0, []),
    )
    failures = _frontend_gate_spotlight_photo.spotlight_layout_failures(
        samples, "at 1180px", 2
    )
    assert failures == [
        "at 1180px: the name of 'Radiohead' breaks inside the word 'Radiohead'"
    ]


def test_a_rotation_that_never_showed_every_candidate_fails() -> None:
    failures = _frontend_gate_spotlight_photo.spotlight_layout_failures(
        _samples(("A", 200.0, [])), "at 320px", 5
    )
    assert failures == [
        "at 320px: only 1 of 5 spotlight candidates were on screen, so the "
        "card height was not compared"
    ]


def test_the_layout_probe_reads_words_by_the_lines_their_characters_sit_on() -> None:
    script = _frontend_gate_spotlight_photo._LAYOUT_SAMPLE_JS
    assert "createRange()" in script
    assert "getClientRects()" in script


def test_the_layout_check_keeps_the_rotation_going_and_sees_every_width() -> None:
    page = MagicMock()
    steady = _samples(*((f"A{i}", 200.0, []) for i in range(5)))
    page.evaluate.side_effect = lambda script, *a: (
        steady if script is _frontend_gate_spotlight_photo._LAYOUT_SAMPLE_JS else None
    )
    check = _frontend_gate_spotlight_photo.check_artist_spotlight_name_whole_and_card_height_fixed
    assert _run_layout(check, page) == []
    assert "const keepRotating = true" in page.add_init_script.call_args.args[0]
    widths = [call.args[0]["width"] for call in page.set_viewport_size.call_args_list]
    assert widths[:5] == [320, 390, 1024, 1180, 1920]
    assert 1024 in widths[5:] and widths[-1] == 1920


def _run_layout(check, page):
    with (
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._seed_spotlight_job",
            return_value="job-1",
        ) as seed,
        patch("scripts.dev._frontend_gate_spotlight_photo.jobs.delete") as delete_job,
    ):
        failures = check(page, "http://127.0.0.1:0")
    seed.assert_called_once_with(_frontend_gate_spotlight_photo.LAYOUT_ARTISTS)
    delete_job.assert_called_once_with("job-1")
    return failures


def test_the_seed_can_give_an_artist_several_albums() -> None:
    with (
        patch(
            "scripts.dev._frontend_gate_spotlight_photo.jobs.create", return_value="j"
        ),
        patch("scripts.dev._frontend_gate_spotlight_photo.jobs.succeed") as succeed,
    ):
        _frontend_gate_spotlight_photo._seed_spotlight_job((("Radiohead", 3, 900),))
    rows = succeed.call_args.args[1]
    assert [row["artist"] for row in rows] == ["Radiohead"] * 3
    assert len({row["album"] for row in rows}) == 3
    assert {row["play_time_seconds"] for row in rows} == {900}


def _hold(**changes) -> tuple[dict, dict]:
    before = {
        "focused": True,
        "visible": True,
        "href": "https://open.spotify.com/artist/a",
        "label": "View A on Spotify (opens in new tab)",
        "artist": "A",
        "ticks": 4,
    }
    return before, {**before, "ticks": 7, **changes}


def test_a_hold_that_changes_nothing_over_three_periods_passes() -> None:
    before, after = _hold()
    assert (
        _frontend_gate_spotlight_photo.spotlight_hold_failures(before, after, "focus")
        == []
    )


def test_a_focused_link_that_was_retargeted_or_lost_focus_fails() -> None:
    before, after = _hold(label="View B on Spotify (opens in new tab)", focused=False)
    failures = _frontend_gate_spotlight_photo.spotlight_hold_failures(
        before, after, "focus"
    )
    assert failures == [
        "spotlight hold (focus): focused changed from True to False while the "
        "card was in use",
        "spotlight hold (focus): label changed from 'View A on Spotify (opens in "
        "new tab)' to 'View B on Spotify (opens in new tab)' while the card was "
        "in use",
    ]


def test_a_hold_judged_over_too_few_periods_fails() -> None:
    before, after = _hold(ticks=5)
    failures = _frontend_gate_spotlight_photo.spotlight_hold_failures(
        before, after, "pointer"
    )
    assert failures == [
        "spotlight hold (pointer): only 1 rotation periods passed, so holding "
        "still was not tested"
    ]


def test_the_hold_check_focuses_then_hovers_and_counts_the_periods() -> None:
    page = MagicMock()
    page.evaluate.return_value = {
        "focused": True,
        "visible": True,
        "href": "h",
        "label": "l",
        "artist": "A",
        "ticks": 0,
    }
    check = _frontend_gate_spotlight_photo.check_artist_spotlight_holds_still_while_focused_or_hovered
    with (
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._seed_spotlight_job",
            return_value="job-1",
        ),
        patch("scripts.dev._frontend_gate_spotlight_photo.jobs.delete"),
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._open_spotlight_card",
            return_value=None,
        ),
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._remeasure_hold_failures",
            return_value=[],
        ),
    ):
        failures = check(page, "http://127.0.0.1:0")
    page.focus.assert_called_once_with("#spotlight-spotify-link")
    page.hover.assert_called_once_with("#artist-spotlight-card")
    assert "const keepRotating = true" in page.add_init_script.call_args.args[0]
    assert "__spotlightTicks += 1" in page.add_init_script.call_args.args[0]
    assert len(failures) == 2 and all("only 0 rotation periods" in f for f in failures)


def test_a_window_with_a_swap_and_steady_opacity_passes() -> None:
    assert (
        _frontend_gate_spotlight_photo.spotlight_fade_failures(_steady_samples()) == []
    )


def test_opacity_that_moves_during_a_swap_fails() -> None:
    samples = _steady_samples()
    samples[2]["opacity"] = ["1", "0.4"]
    failures = _frontend_gate_spotlight_photo.spotlight_fade_failures(samples)
    assert len(failures) == 1
    assert failures[0].startswith(
        "spotlight photo opacity changed during a rotation tick: "
    )


def test_steady_opacity_over_a_window_with_no_swap_fails_instead_of_passing() -> None:
    """The one-shot tick once fired before sampling began, so every sample was
    identical and the check passed whatever a swap did (S4-2)."""
    samples = [{"opacity": ["1", "1"], "index": "3", "ticks": 4} for _ in range(5)]
    failures = _frontend_gate_spotlight_photo.spotlight_fade_failures(samples)
    assert len(failures) == 1
    assert "never swapped the artist while opacity was sampled" in failures[0]


def test_the_opacity_sampler_records_the_artist_and_runs_across_rotation_periods() -> (
    None
):
    script = _frontend_gate_spotlight_photo._PHOTO_SAMPLE_JS
    assert "dataset.spotlightIndex" in script
    assert "}, 1000);" in script
    page = _crop_overlay_page([], [])
    _run(
        _frontend_gate_spotlight_photo.check_artist_spotlight_photo_has_no_crop_overlay_or_animation,
        page,
    )
    assert "const keepRotating = true" in page.add_init_script.call_args.args[0]


def test_a_photo_cut_by_a_clipping_ancestor_names_it() -> None:
    """A height cap with overflow hidden on the card content leaves 42% of the
    photo visible; the clip the reading reports is the intersection (S4-6)."""
    failures = _frontend_gate_spotlight_photo.photo_crop_failures(
        _geometry(
            clip={"left": 0.0, "top": 0.0, "right": 100.0, "bottom": 40.0},
            clippedBy=["spotlight-card-content"],
        )
    )
    assert len(failures) == 1
    assert "on the bottom (clipped by spotlight-card-content)" in failures[0]


_CLIPPED_GRANDPARENT_HTML = """<!doctype html><html><body style="margin:0">
<div id="grand" style="overflow:hidden;width:200px;height:40px">
<div id="parent"><div class="spotlight-image-box" style="width:100px;height:100px">
<img id="spotlight-artist-img" src="{src}"
     style="width:100%;height:100%;object-fit:contain"></div></div></div>
</body></html>"""


@pytest.mark.browser
def test_the_paint_probe_reports_a_clipping_grandparent_and_its_box() -> None:
    """Runs `_PHOTO_PAINT_JS` in Chromium on a photo box whose parent does not
    clip but whose grandparent does (S4-6): a probe that read only the parent
    would report no clip and a clip box of the whole 100px photo box."""
    from scripts.dev._frontend_gate_runtime import _launch_browser, _load_playwright

    html = _CLIPPED_GRANDPARENT_HTML.replace(
        "{src}", _frontend_gate_spotlight_photo.SQUARE_PHOTO_DATA_URL
    )
    with _load_playwright()() as playwright:
        browser = _launch_browser(playwright, "chromium")
        try:
            page = browser.new_page()
            page.set_content(html)
            page.wait_for_function(
                "() => document.querySelector('#spotlight-artist-img').complete"
            )
            reading = page.evaluate(_frontend_gate_spotlight_photo._PHOTO_PAINT_JS)
        finally:
            browser.close()
    assert reading["clippedBy"] == ["grand"]
    assert reading["clip"]["bottom"] == pytest.approx(40.0)
    assert reading["clip"]["right"] == pytest.approx(100.0)
    failures = _frontend_gate_spotlight_photo.photo_crop_failures(reading)
    assert len(failures) == 1 and "clipped by grand" in failures[0]


def test_the_first_photo_check_also_judges_the_crop() -> None:
    page = _crop_overlay_page([], [])
    real = page.evaluate.side_effect

    def cut(script, *args):
        if script is _frontend_gate_spotlight_photo._PHOTO_PAINT_JS:
            return _geometry(
                clip={"left": 0.0, "top": 0.0, "right": 100.0, "bottom": 40.0}
            )
        return real(script, *args)

    page.evaluate.side_effect = cut
    failures = _run(
        _frontend_gate_spotlight_photo.check_artist_spotlight_photo_has_no_crop_overlay_or_animation,
        page,
    )
    assert len(failures) == 1 and "spotlight photo is cropped" in failures[0]


def _hold_page(wait_error: Exception) -> MagicMock:
    page = MagicMock()
    page.evaluate.return_value = {
        "focused": True,
        "visible": True,
        "href": "h",
        "label": "l",
        "artist": "A",
        "ticks": 0,
    }
    page.wait_for_function.side_effect = wait_error
    return page


def _run_hold(page: MagicMock) -> list[str]:
    check = _frontend_gate_spotlight_photo.check_artist_spotlight_holds_still_while_focused_or_hovered
    with (
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._seed_spotlight_job",
            return_value="job-1",
        ),
        patch("scripts.dev._frontend_gate_spotlight_photo.jobs.delete"),
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._open_spotlight_card",
            return_value=None,
        ),
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._remeasure_hold_failures",
            return_value=[],
        ),
    ):
        return check(page, "http://127.0.0.1:0")


def test_a_timed_out_hold_wait_is_judged_by_the_tick_count() -> None:
    failures = _run_hold(_hold_page(PlaywrightTimeoutError("no ticks")))
    assert len(failures) == 2 and all("only 0 rotation periods" in f for f in failures)


def test_a_crashed_page_during_the_hold_wait_propagates() -> None:
    """A broad except once swallowed this and reported a tick count instead."""
    with pytest.raises(PlaywrightError, match="Target crashed"):
        _run_hold(_hold_page(PlaywrightError("Target crashed")))


def _remeasured(**changes) -> dict:
    return {
        "focused": True,
        "visible": True,
        "writes": 0,
        "measures": 2,
        **changes,
    }


def test_a_remeasure_that_leaves_the_focused_link_alone_passes() -> None:
    assert (
        _frontend_gate_spotlight_photo.spotlight_remeasure_failures(_remeasured()) == []
    )


def test_a_remeasure_that_rewrote_the_focused_link_fails() -> None:
    """The mutant that drops `keepLink` rewrites the link once per candidate."""
    failures = _frontend_gate_spotlight_photo.spotlight_remeasure_failures(
        _remeasured(writes=13)
    )
    assert failures == [
        "spotlight re-measure: the focused link was rewritten 13 times while "
        "the card's height was re-measured"
    ]


def test_a_remeasure_that_dropped_focus_or_hid_the_link_fails() -> None:
    for change in ({"focused": False}, {"visible": False}):
        failures = _frontend_gate_spotlight_photo.spotlight_remeasure_failures(
            _remeasured(**change)
        )
        assert failures == [
            "spotlight re-measure: the link lost focus or was hidden while the "
            "card's height was re-measured"
        ]


def test_a_remeasure_that_never_ran_is_a_failure_instead_of_a_pass() -> None:
    failures = _frontend_gate_spotlight_photo.spotlight_remeasure_failures(
        _remeasured(measures=0)
    )
    assert len(failures) == 1
    assert "never re-measured" in failures[0]


def _remeasure_run(state: dict, wait_error: Exception | None = None):
    page = MagicMock()
    probe = page.context.new_page.return_value
    probe.evaluate.return_value = state
    probe.wait_for_function.side_effect = [None, wait_error]
    with patch(
        "scripts.dev._frontend_gate_spotlight_photo._open_spotlight_card",
        return_value=None,
    ):
        failures = _frontend_gate_spotlight_photo._remeasure_hold_failures(
            page, "http://127.0.0.1:0/results?job_id=j"
        )
    return failures, probe


def test_the_remeasure_hold_focuses_then_resizes_a_card_with_a_linkless_artist() -> (
    None
):
    failures, probe = _remeasure_run(_remeasured())
    assert failures == []
    mock_script = probe.add_init_script.call_args.args[0]
    assert '["Springsteen"]' in mock_script
    focus_script = probe.wait_for_function.call_args_list[0].args[0]
    assert focus_script is _frontend_gate_spotlight_photo._FOCUS_VISIBLE_LINK_JS
    probe.set_viewport_size.assert_called_once_with(
        _frontend_gate_spotlight_photo.LAYOUT_VIEWPORTS[2]
    )
    probe.close.assert_called_once_with()


def test_a_timed_out_remeasure_wait_is_judged_by_the_measure_count() -> None:
    failures, probe = _remeasure_run(
        _remeasured(measures=0), PlaywrightTimeoutError("no measure")
    )
    assert len(failures) == 1 and "never re-measured" in failures[0]
    probe.close.assert_called_once_with()


def test_a_crashed_page_during_the_remeasure_wait_propagates_and_closes() -> None:
    page = MagicMock()
    probe = page.context.new_page.return_value
    probe.wait_for_function.side_effect = [None, PlaywrightError("Target crashed")]
    with (
        patch(
            "scripts.dev._frontend_gate_spotlight_photo._open_spotlight_card",
            return_value=None,
        ),
        pytest.raises(PlaywrightError, match="Target crashed"),
    ):
        _frontend_gate_spotlight_photo._remeasure_hold_failures(page, "u")
    probe.close.assert_called_once_with()


def test_the_fetch_mock_answers_a_linkless_artist_without_a_spotify_url() -> None:
    page = MagicMock()
    _frontend_gate_spotlight_photo._install_spotlight_fetch_mock(
        page, "photo.png", linkless=("A B", "C")
    )
    script = page.add_init_script.call_args.args[0]
    assert 'const linkless = ["A B", "C"];' in script
    assert "!linkless.includes(artist)" in script
