"""POST /results_loading: parse, pre-check, admit -- and refuse before any job."""

from unittest.mock import MagicMock, patch

import pytest

from scrobblescope import jobs
from tests.helpers import VALID_FORM_DATA

PUBLIC_USER = {"exists": True, "registered_year": None}


@pytest.mark.parametrize(
    "overrides, sentence",
    [
        ({"release_scope": "forever"}, "Choose a release filter from the list."),
        (
            {"release_scope": "decade", "decade": "2030s"},
            "Choose a decade from the list.",
        ),
        (
            {"release_scope": "custom", "release_year": "1899"},
            "Release year must be between 1900 and 2025.",
        ),
        ({"sort_by": "loudness"}, "Choose Play count or Play time to rank by."),
        ({"limit_results": "7"}, "Choose how many albums to show from the list."),
        (
            {"min_plays": "0"},
            "Minimum plays must be a whole number from 1 to 50.",
        ),
        (
            {"min_tracks": "11"},
            "Minimum unique tracks must be a whole number from 1 to 10.",
        ),
    ],
)
def test_a_bad_filter_is_refused_on_the_form_and_starts_nothing(
    client, fresh_job_store, overrides, sentence
):
    """
    GIVEN a form whose filter value the form never offers
    WHEN POST /results_loading is submitted
    THEN the form comes back with that field's sentence (the listener is not
    shown "no albums" later), Last.fm is not asked, and nothing starts.

    Mutation: skip the decade membership check in album_request and the
    decade row starts a job.
    """
    with (
        patch("scrobblescope.routes._current_year", return_value=2025),
        patch("scrobblescope.routes._check_user_exists") as lookup,
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post(
            "/results_loading", data={**VALID_FORM_DATA, **overrides}
        )

    assert response.status_code == 200
    assert sentence in response.get_data(as_text=True)
    lookup.assert_not_called()
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


@pytest.mark.parametrize("failing", ["exists", "privacy"])
def test_a_pre_check_outage_refuses_retryably_and_starts_nothing(
    client, fresh_job_store, failing
):
    """
    GIVEN Last.fm cannot answer the existence check, or the privacy check
    WHEN POST /results_loading is submitted
    THEN the answer is the retryable 503, no slot is taken and no job starts
    (before this the route logged "proceeding" and started a doomed job).

    Mutation: treat UNAVAILABLE like PUBLIC in the route and both rows start a job.
    """
    down = {"side_effect": RuntimeError("down")}
    exists = down if failing == "exists" else {"return_value": PUBLIC_USER}
    privacy = down if failing == "privacy" else {"return_value": True}
    with (
        patch("scrobblescope.routes._check_user_exists", **exists),
        patch("scrobblescope.routes._check_profile_is_public", **privacy),
        patch(
            "scrobblescope.routes.acquire_job_slot", MagicMock(return_value=True)
        ) as slot,
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert response.status_code == 503
    assert "Validation service unavailable. Try again." in response.get_data(
        as_text=True
    )
    slot.assert_not_called()
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


@pytest.mark.parametrize(
    "answer",
    [{"registered_year": 2000}, {"exists": "yes", "registered_year": 2000}, None],
    ids=["no-exists-key", "exists-not-a-bool", "none"],
)
def test_a_malformed_last_fm_answer_refuses_retryably_and_starts_nothing(
    client, fresh_job_store, answer
):
    """
    GIVEN Last.fm answers the existence check with a body of the wrong shape
    WHEN POST /results_loading is submitted
    THEN the listener gets the retryable 503, not a 500 and not a started job.

    Mutation: read `info["exists"]` outside precheck's try (the route 500s),
    or treat a missing `exists` as true (a job starts).
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=answer),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert response.status_code == 503
    assert "Validation service unavailable. Try again." in response.get_data(
        as_text=True
    )
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


def test_an_album_job_record_says_it_is_an_album_job(client, fresh_job_store):
    """The kind is written when the job is created, not defaulted when read.

    Mutation: build the params without `mode` and this fails.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.start_job_thread"),
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert response.status_code == 303
    (job_id,) = fresh_job_store.ids()
    assert jobs.context(job_id)["params"]["mode"] == "album"
