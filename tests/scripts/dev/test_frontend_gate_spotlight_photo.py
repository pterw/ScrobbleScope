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
