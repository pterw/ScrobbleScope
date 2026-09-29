"""Parity and behaviour tests for the spotlight-photo slice of the frontend
gate (F-B21-60 part 1)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

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
            "scripts.dev._frontend_gate_spotlight_photo.create_job",
            return_value="job-1",
        ) as create_job,
        patch(
            "scripts.dev._frontend_gate_spotlight_photo.set_job_results"
        ) as set_job_results,
        patch(
            "scripts.dev._frontend_gate_spotlight_photo.set_job_progress"
        ) as set_job_progress,
    ):
        job_id = _frontend_gate_spotlight_photo._seed_spotlight_job()

    assert job_id == "job-1"
    create_job.assert_called_once()
    results = set_job_results.call_args.args[1]
    artists = {entry["artist"] for entry in results}
    assert len(artists) > 1, "the seeded job must sample more than one artist"
    set_job_progress.assert_called_once_with(
        "job-1", progress=100, message="Done", error=False
    )


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
        patch("scripts.dev._frontend_gate_spotlight_photo.delete_job") as delete_job,
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


def _crop_overlay_page(overlap: list, motion: list) -> MagicMock:
    def evaluate(script, *args):
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
        return [["1", "1"]]

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
