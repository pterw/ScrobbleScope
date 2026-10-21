"""One Last.fm answer, three routes: the album form, the heatmap start and the blur check.

A listener must be told the same thing about a name whichever button asks.
This table is the parity test for moving the heatmap and validate routes onto
the shared pre-check (it passes for them before that move, and for the album
route once it uses the pre-check).
"""

import asyncio
import html
import time
from unittest.mock import patch

import pytest

from scrobblescope.routes import _PRIVATE_PROFILE_MESSAGE
from tests.helpers import VALID_FORM_DATA

ROUTES = ("album", "heatmap", "validate")
KNOWN = {"exists": True, "registered_year": 2016}
GHOST = {"exists": False, "registered_year": None}
DOWN = RuntimeError("down")

#: answer name -> (existence lookup, privacy lookup, what the listener is told)
ANSWERS = {
    "public": (KNOWN, True, "accepted"),
    "missing": (GHOST, True, "not_found"),
    "private": (KNOWN, False, "private"),
    "outage-on-existence": (DOWN, True, "unavailable"),
    "outage-on-privacy": (KNOWN, DOWN, "unavailable"),
}


def _kwargs(value):
    return (
        {"side_effect": value}
        if isinstance(value, Exception)
        else {"return_value": value}
    )


def _call(client, route):
    if route == "album":
        return client.post("/results_loading", data=VALID_FORM_DATA)
    if route == "heatmap":
        return client.post("/heatmap_loading", data={"username": "flounder14"})
    return client.get("/validate_user", query_string={"username": "flounder14"})


def _outcome(route, response):
    """Name what the listener was told, in words every route shares."""
    if route == "album":
        if response.status_code == 303:
            return "accepted"
        text = response.get_data(as_text=True)
        if response.status_code == 503 and "Validation service unavailable" in text:
            return "unavailable"
        if "was not found on Last.fm" in text:
            return "not_found"
        if html.escape(_PRIVATE_PROFILE_MESSAGE) in text:
            return "private"
        return f"unclassified {response.status_code}"
    body = response.get_json()
    if route == "heatmap":
        if response.status_code == 202:
            return "accepted"
        if response.status_code == 503:
            return "unavailable"
        return {"user_not_found": "not_found", "private_profile": "private"}.get(
            body.get("error_code"), f"unclassified {response.status_code}"
        )
    if response.status_code == 503:
        return "unavailable"
    if body["valid"]:
        return "accepted"
    if "not found" in body["message"]:
        return "not_found"
    if "private" in body["message"].lower():
        return "private"
    return f"unclassified {response.status_code}"


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("answer", list(ANSWERS))
def test_every_route_reads_the_last_fm_answer_the_same_way(
    client, fresh_job_store, route, answer
):
    """
    Mutation: ask for privacy before existence (the "missing" row then calls
    the privacy mock), or let an outage through in any route (the outage rows
    then report "accepted").
    """
    exists, public, expected = ANSWERS[answer]
    with (
        patch("scrobblescope.routes._check_user_exists", **_kwargs(exists)),
        patch(
            "scrobblescope.routes._check_profile_is_public", **_kwargs(public)
        ) as privacy,
        patch("scrobblescope.routes.start_job_thread"),
    ):
        response = _call(client, route)

    assert _outcome(route, response) == expected
    if answer in ("missing", "outage-on-existence"):
        privacy.assert_not_called()
    starts_a_job = expected == "accepted" and route != "validate"
    assert (len(fresh_job_store.ids()) == 1) is starts_a_job


@pytest.mark.parametrize("route", ROUTES)
def test_a_stalled_last_fm_costs_a_route_its_budget_not_the_session(
    client, fresh_job_store, route
):
    """
    GIVEN Last.fm accepts the lookup and never answers
    WHEN any of the three routes asks
    THEN it answers "unavailable" within the pre-check budget and starts nothing.

    Mutation: remove `timeout=` from `routes._check_user_exists` and each row
    waits the stall out and then accepts.
    """

    async def stalled(_username):
        await asyncio.sleep(3)

    with (
        patch("scrobblescope.routes.check_user_exists", stalled),
        patch("scrobblescope.routes.LASTFM_PRECHECK_TIMEOUT_SECONDS", 0.05),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        started = time.monotonic()
        response = _call(client, route)
        elapsed = time.monotonic() - started

    assert _outcome(route, response) == "unavailable"
    assert elapsed < 1.5
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize(
    "answer",
    [{"registered_year": 2016}, {"exists": "yes"}, None],
    ids=["no-exists-key", "exists-not-a-bool", "none"],
)
def test_a_malformed_last_fm_answer_is_unavailable_on_every_route(
    client, fresh_job_store, route, answer
):
    """
    GIVEN Last.fm answers the existence check with a body of the wrong shape
    WHEN the album form, the heatmap start or the blur check asks
    THEN each says "unavailable" (retryable) and starts nothing: a bad body is
    an outage, never a 500 and never a guess.

    Mutation: read `info["exists"]` outside precheck's try and every row 500s.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=answer),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = _call(client, route)

    assert _outcome(route, response) == "unavailable"
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []
