from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope.musicbrainz import (
    _build_release_group_query,
    lookup_original_release,
)
from tests.helpers import NoopAsyncContext, make_response_context


def test_build_release_group_query_escapes_lucene_operators():
    """
    GIVEN a title and artist containing a quote and Lucene operators
    WHEN _build_release_group_query builds the search query
    THEN the special characters are escaped rather than passed through raw.
    """
    query = _build_release_group_query("AC/DC", 'Who Made Who: "Live"')

    assert query == ('releasegroup:"Who Made Who\\: \\"Live\\"" AND artist:"AC\\/DC"')


def test_build_release_group_query_plain_names_round_trip():
    """
    GIVEN a plain artist/title with no special characters
    WHEN _build_release_group_query builds the search query
    THEN it produces the documented Lucene form unescaped.
    """
    query = _build_release_group_query("Fleetwood Mac", "Rumours")

    assert query == 'releasegroup:"Rumours" AND artist:"Fleetwood Mac"'


@pytest.mark.asyncio
async def test_lookup_rejects_high_scoring_wrong_artist():
    """
    GIVEN a release-group result that scores above the floor but belongs to
        a different artist than the one searched for
    WHEN lookup_original_release runs
    THEN it returns (None, None) rather than trusting the score alone.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={
            "release-groups": [
                {
                    "id": "wrong-artist-id",
                    "title": "Rumours",
                    "score": 95,
                    "first-release-date": "1977-02-04",
                    "artist-credit": [{"name": "Fleetwood Mac Tribute Band"}],
                }
            ]
        }
    )
    session.get.return_value = make_response_context(resp)

    with (
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "test@example.com"),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
    ):
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == (None, None)


@pytest.mark.asyncio
async def test_lookup_rejects_below_score_floor():
    """
    GIVEN a release-group result matching artist and title exactly but
        scoring below the 90 floor
    WHEN lookup_original_release runs
    THEN it returns (None, None) -- a low score means MusicBrainz itself is
        not confident in the text match.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={
            "release-groups": [
                {
                    "id": "low-score-id",
                    "title": "Rumours",
                    "score": 80,
                    "first-release-date": "1977-02-04",
                    "artist-credit": [{"name": "Fleetwood Mac"}],
                }
            ]
        }
    )
    session.get.return_value = make_response_context(resp)

    with (
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "test@example.com"),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
    ):
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == (None, None)


@pytest.mark.asyncio
async def test_lookup_returns_release_group_id_and_original_date_on_match():
    """
    GIVEN a release-group result that clears the score floor and matches on
        normalized artist and title
    WHEN lookup_original_release runs
    THEN it returns (mb_release_group_id, first-release-date) -- both
        cacheable, per the plan's return-shape contract.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={
            "release-groups": [
                {
                    "id": "rg-rumours",
                    "title": "Rumours",
                    "score": 100,
                    "first-release-date": "1977-02-04",
                    "artist-credit": [{"name": "Fleetwood Mac"}],
                }
            ]
        }
    )
    session.get.return_value = make_response_context(resp)

    with (
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "test@example.com"),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
    ):
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == ("rg-rumours", "1977-02-04")


@pytest.mark.asyncio
async def test_lookup_returns_none_none_without_any_candidate():
    """
    GIVEN a search response with no release-groups at all
    WHEN lookup_original_release runs
    THEN it returns (None, None), a cacheable "nothing found" outcome.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"release-groups": []})
    session.get.return_value = make_response_context(resp)

    with (
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "test@example.com"),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
    ):
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == (None, None)


@pytest.mark.asyncio
async def test_lookup_retries_on_503_then_succeeds():
    """
    GIVEN MusicBrainz answers 503 once and then 200 with a matching result
    WHEN lookup_original_release runs
    THEN it waits and retries, asking the limiter for every attempt, and
        returns the eventual match.
    """
    session = MagicMock()
    resp_busy = AsyncMock()
    resp_busy.status = 503
    resp_ok = AsyncMock()
    resp_ok.status = 200
    resp_ok.json = AsyncMock(
        return_value={
            "release-groups": [
                {
                    "id": "rg-rumours",
                    "title": "Rumours",
                    "score": 100,
                    "first-release-date": "1977-02-04",
                    "artist-credit": [{"name": "Fleetwood Mac"}],
                }
            ]
        }
    )
    session.get.side_effect = [
        make_response_context(resp_busy),
        make_response_context(resp_ok),
    ]

    limiter = MagicMock(wraps=NoopAsyncContext())
    limiter.__aenter__ = AsyncMock(return_value=None)
    limiter.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=limiter,
        ),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "test@example.com"),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == ("rg-rumours", "1977-02-04")
    assert session.get.call_count == 2
    assert limiter.__aenter__.await_count == 2
    assert mock_sleep.await_count >= 1


@pytest.mark.asyncio
async def test_lookup_sends_user_agent_with_contact():
    """
    GIVEN a configured MUSICBRAINZ_CONTACT
    WHEN lookup_original_release makes a request
    THEN the request carries a User-Agent naming ScrobbleScope and the
        contact address -- MusicBrainz blocks anonymous clients.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={"release-groups": []})
    session.get.return_value = make_response_context(resp)

    with (
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
        patch(
            "scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT",
            "scrobblescope@example.com",
        ),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
    ):
        await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    _, kwargs = session.get.call_args
    user_agent = kwargs["headers"]["User-Agent"]
    assert "ScrobbleScope/" in user_agent
    assert "scrobblescope@example.com" in user_agent


@pytest.mark.asyncio
async def test_lookup_disabled_without_contact_makes_no_request():
    """
    GIVEN no MUSICBRAINZ_CONTACT is configured
    WHEN lookup_original_release runs
    THEN it returns (None, None) without calling the API at all --
        MusicBrainz blocks anonymous clients, so an unconfigured contact
        would only guarantee a rejected request.
    """
    session = MagicMock()

    with (
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", None),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
    ):
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == (None, None)
    session.get.assert_not_called()


@pytest.mark.asyncio
async def test_lookup_disabled_by_flag_makes_no_request():
    """
    GIVEN MUSICBRAINZ_ENABLED is False, even with a contact configured
    WHEN lookup_original_release runs
    THEN it returns (None, None) without calling the API.
    """
    session = MagicMock()

    with (
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "test@example.com"),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", False),
    ):
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == (None, None)
    session.get.assert_not_called()
