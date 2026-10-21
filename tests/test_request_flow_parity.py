"""Parity tests for the album, heatmap and validate_user request flows.

Written before the request module, the pre-check and the admission module
replace the code behind these routes (AGENTS.md "Refactor requires parity
tests"). Each test states a listener-visible behaviour that must survive the
refactor. Nothing here pins the fail-open pre-check or the positional thread
arguments: those are what the refactor removes.
"""

from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope import jobs
from tests.helpers import VALID_FORM_DATA

PUBLIC_USER = {"exists": True, "registered_year": None}

#: The ten parameters a job record holds for an album run.
RECORD_KEYS = (
    "username",
    "year",
    "sort_mode",
    "include_unmatched",
    "release_scope",
    "decade",
    "release_year",
    "min_plays",
    "min_tracks",
    "limit_results",
)


def _run_inline(target, args=()):
    """Stand in for start_job_thread: run the thread's target on this thread."""
    target(*args)


def _post_album(client, form):
    """POST /results_loading for a public user with the worker thread stubbed."""
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data={**VALID_FORM_DATA, **form})
    return response, mock_start


@pytest.mark.parametrize(
    "form, expected",
    [
        pytest.param(
            {"release_scope": "custom", "decade": "1990s", "release_year": "1982"},
            {"release_scope": "custom", "decade": None, "release_year": 1982},
            id="custom-keeps-the-year-and-drops-the-decade",
        ),
        pytest.param(
            {"release_scope": "decade", "decade": "1990s", "release_year": "1982"},
            {"release_scope": "decade", "decade": "1990s", "release_year": None},
            id="decade-keeps-the-decade-and-drops-the-year",
        ),
        pytest.param(
            {"release_scope": "previous", "decade": "1990s", "release_year": "1982"},
            {"release_scope": "previous", "decade": None, "release_year": None},
            id="previous-drops-both",
        ),
    ],
)
def test_the_job_record_keeps_only_the_release_fields_its_scope_uses(
    client, fresh_job_store, form, expected
):
    """
    GIVEN a form posted with both a decade and a release year
    WHEN the album job is created
    THEN the record holds every other field as posted, and only the release
    field the chosen scope reads, so a stale hidden input cannot narrow a run.
    """
    base = {
        "year": "2023",
        "sort_by": "playtime",
        "min_plays": "7",
        "min_tracks": "4",
        "limit_results": "25",
    }

    response, _ = _post_album(client, {**base, **form})

    assert response.status_code == 303
    (job_id,) = fresh_job_store.ids()
    params = jobs.context(job_id)["params"]
    assert {key: params[key] for key in RECORD_KEYS} == {
        "username": "flounder14",
        "year": 2023,
        "sort_mode": "playtime",
        "include_unmatched": False,
        "min_plays": 7,
        "min_tracks": 4,
        "limit_results": "25",
        **expected,
    }


def test_the_forms_values_reach_the_album_pipeline_in_order(client, fresh_job_store):
    """
    GIVEN a form with a distinct value in every slot
    WHEN the job's thread runs (inline here)
    THEN the pipeline is awaited once with each value in its own slot.

    Mutation: swap min_plays and min_tracks in background_task's call to
    _fetch_and_process and this fails.
    """
    form = {
        **VALID_FORM_DATA,
        "year": "2023",
        "sort_by": "playcount",
        "release_scope": "custom",
        "release_year": "1982",
        "min_plays": "7",
        "min_tracks": "4",
        "limit_results": "25",
        "include_unmatched": "1",
    }
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch("scrobblescope.routes.start_job_thread", side_effect=_run_inline),
        patch(
            "scrobblescope.orchestrator._fetch_and_process", new_callable=AsyncMock
        ) as pipeline,
        patch("scrobblescope.orchestrator.release_job_slot"),
    ):
        response = client.post("/results_loading", data=form)

    assert response.status_code == 303
    (job_id,) = fresh_job_store.ids()
    pipeline.assert_awaited_once_with(
        job_id,
        "flounder14",
        2023,
        "playcount",
        "custom",
        None,
        1982,
        7,
        4,
        "25",
        include_unmatched=True,
    )


def test_the_heatmap_username_is_trimmed_and_reaches_its_pipeline(
    client, fresh_job_store
):
    """
    GIVEN a heatmap start whose username has surrounding spaces
    WHEN the job's thread runs (inline here)
    THEN the record and the pipeline both hold the trimmed name, and the
    record says the job is a heatmap.

    Mutation: stop stripping the username in heatmap_loading and this fails.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch("scrobblescope.routes.start_job_thread", side_effect=_run_inline),
        patch(
            "scrobblescope.heatmap._fetch_and_process_heatmap",
            new_callable=AsyncMock,
        ) as pipeline,
        patch("scrobblescope.heatmap.release_job_slot"),
    ):
        response = client.post("/heatmap_loading", data={"username": "  flounder14  "})

    assert response.status_code == 202
    job_id = response.get_json()["job_id"]
    assert jobs.context(job_id)["params"] == {
        "username": "flounder14",
        "mode": "heatmap",
    }
    pipeline.assert_awaited_once_with(job_id, "flounder14")


@pytest.mark.parametrize(
    "form, message",
    [
        ({"username": ""}, "Username and year are required."),
        ({"year": ""}, "Username and year are required."),
        ({"year": "20x5"}, "Year must be a valid number."),
        ({"year": "2001"}, "Year must be between 2002 and 2025."),
        ({"year": "2026"}, "Year must be between 2002 and 2025."),
    ],
)
def test_an_unusable_name_or_year_is_refused_before_any_lookup(
    client, fresh_job_store, form, message
):
    """
    GIVEN a form with no name, no year, a non-numeric year or a year outside
    2002 to the current year
    WHEN POST /results_loading is submitted
    THEN the form comes back with the reason, Last.fm is not asked, and no job
    or thread is started.
    """
    with (
        patch("scrobblescope.routes._current_year", return_value=2025),
        patch("scrobblescope.routes._check_user_exists") as lookup,
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data={**VALID_FORM_DATA, **form})

    assert response.status_code == 200
    assert message in response.get_data(as_text=True)
    lookup.assert_not_called()
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


@pytest.mark.parametrize("year", ["2002", "2025"])
def test_the_first_and_last_listening_years_are_accepted(client, year):
    """The year range is inclusive at both ends.

    Mutation: change `year < 2002` to `year <= 2002` in results_loading and
    the 2002 row fails.
    """
    with patch("scrobblescope.routes._current_year", return_value=2025):
        response, _ = _post_album(client, {"year": year})

    assert response.status_code == 303


def test_a_full_house_refuses_before_a_job_exists(client, fresh_job_store):
    """
    GIVEN every job slot is busy
    WHEN an album search and a heatmap start are submitted
    THEN both are refused and neither leaves a job behind.

    Mutation: create the job before acquiring the slot in either route and the
    store is no longer empty.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
    ):
        album = client.post("/results_loading", data=VALID_FORM_DATA)
        heatmap = client.post("/heatmap_loading", data={"username": "flounder14"})

    assert album.status_code == 200
    assert b"Too many requests in progress" in album.data
    assert heatmap.status_code == 429
    assert heatmap.get_json()["retryable"] is True
    assert fresh_job_store.ids() == []


def test_a_heatmap_privacy_check_outage_is_a_retryable_503(client, fresh_job_store):
    """
    GIVEN the user exists but Last.fm cannot answer the privacy check
    WHEN POST /heatmap_loading is submitted
    THEN the answer is the retryable 503 body and nothing starts.

    Mutation: change the message or `retryable` in that answer and this fails.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch(
            "scrobblescope.routes._check_profile_is_public",
            side_effect=RuntimeError("down"),
        ),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/heatmap_loading", data={"username": "flounder14"})

    assert response.status_code == 503
    assert response.get_json() == {
        "error": True,
        "message": "Validation service unavailable. Try again.",
        "retryable": True,
    }
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


def test_validate_user_outage_is_a_retryable_503(client):
    """GET /validate_user answers 503 with the shared unavailable sentence."""
    with patch(
        "scrobblescope.routes._check_user_exists", side_effect=RuntimeError("down")
    ):
        response = client.get("/validate_user", query_string={"username": "someone"})

    assert response.status_code == 503
    assert response.get_json() == {
        "valid": False,
        "message": "Validation service unavailable. Try again.",
    }


def test_validate_user_asks_about_privacy_only_for_an_existing_user(client):
    """
    GIVEN Last.fm does not know the name
    WHEN GET /validate_user runs
    THEN the answer is "not found" and the privacy check is never made.

    Mutation: ask for privacy before existence and the mock is called.
    """
    with (
        patch(
            "scrobblescope.routes._check_user_exists",
            return_value={"exists": False, "registered_year": None},
        ),
        patch("scrobblescope.routes._check_profile_is_public") as privacy,
    ):
        response = client.get("/validate_user", query_string={"username": "ghost"})

    assert response.status_code == 200
    assert response.get_json() == {
        "valid": False,
        "message": "Username not found on Last.fm.",
    }
    privacy.assert_not_called()
