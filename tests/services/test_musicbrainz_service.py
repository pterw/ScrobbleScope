import logging
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from scrobblescope.config import APP_USER_AGENT, MAX_RETRY_AFTER_SECONDS
from scrobblescope.errors import ProviderError
from scrobblescope.musicbrainz import (
    _build_release_group_query,
    _musicbrainz_headers,
    lookup_original_release,
)
from scrobblescope.release_checks import _check_candidate
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
    resp_busy.headers = {}
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
    # No Retry-After: the first backoff is 2 ** 0 seconds plus bounded jitter.
    (waited,), _ = mock_sleep.await_args
    assert 1 <= waited < 1.2


@pytest.mark.asyncio
async def test_lookup_sends_user_agent_with_contact():
    """
    GIVEN a configured MUSICBRAINZ_CONTACT
    WHEN lookup_original_release makes a request
    THEN the request carries a User-Agent naming ScrobbleScope and the
        contact -- MusicBrainz requires one in every User-Agent.
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
        MusicBrainz requires a contact in every User-Agent, so a request
        without one would break its policy.
    """
    session = MagicMock()

    with (
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", None),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
    ):
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == (None, None)
    session.get.assert_not_called()


def test_musicbrainz_headers_refuses_a_missing_contact():
    """
    GIVEN MUSICBRAINZ_CONTACT is unset
    WHEN _musicbrainz_headers builds the request headers directly, without
        going through the disable gate in lookup_original_release
    THEN it raises rather than interpolating the literal string "None" into
        the User-Agent. MusicBrainz requires a contact, and a header
        naming "None" identifies nobody -- it is an anonymous request
        dressed as an identified one.
    """
    with patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", None):
        with pytest.raises(RuntimeError, match="MUSICBRAINZ_CONTACT"):
            _musicbrainz_headers()


def test_musicbrainz_headers_is_derived_from_the_shared_identity():
    """
    GIVEN a configured MUSICBRAINZ_CONTACT
    WHEN _musicbrainz_headers builds the request headers
    THEN the User-Agent starts from the application's single identity and
        appends the contact, so musicbrainz.py cannot name the application
        differently from every other provider client.
    """
    with patch(
        "scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "scrobblescope@example.com"
    ):
        user_agent = _musicbrainz_headers()["User-Agent"]

    assert user_agent.startswith(APP_USER_AGENT)
    assert "scrobblescope@example.com" in user_agent


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


_LEAK_ALBUM = "Zqxv Distinctive Album"
_LEAK_ARTIST = "Wjkl Distinctive Artist"


@pytest.mark.asyncio
async def test_lookup_failure_lines_carry_no_album_or_artist(caplog):
    """
    GIVEN the MusicBrainz transport raises with the query text in its message
    WHEN lookup_original_release exhausts its retries
    THEN it raises ProviderError musicbrainz_unavailable, and no record at
    any level names the album or artist.
    """
    session = MagicMock()
    session.get.side_effect = aiohttp.ClientConnectionError(
        f"failed q={_LEAK_ARTIST} {_LEAK_ALBUM}"
    )

    with (
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "me@example.com"),
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
        caplog.at_level(logging.DEBUG),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await lookup_original_release(session, _LEAK_ARTIST, _LEAK_ALBUM, retries=2)

    assert excinfo.value.code == "musicbrainz_unavailable"
    assert "All 2 retries failed for musicbrainz.lookup" in caplog.text
    assert caplog.records
    for record in caplog.records:
        assert _LEAK_ALBUM not in record.getMessage()
        assert _LEAK_ARTIST not in record.getMessage()


@pytest.mark.asyncio
async def test_lookup_raises_when_musicbrainz_stays_throttled_not_no_match():
    """
    GIVEN MusicBrainz answers 503 with no Retry-After on every attempt
    WHEN lookup_original_release runs
    THEN it raises ProviderError musicbrainz_unavailable (nothing said how
    long to wait, so it is an outage, not a rate limit); (None, None) is a
    cacheable "no match" and a throttled call must never pass for one.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 503
    resp.headers = {}
    session.get.return_value = make_response_context(resp)

    with (
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "me@example.com"),
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await lookup_original_release(session, "Artist", "Album", retries=2)

    assert excinfo.value.code == "musicbrainz_unavailable"


@pytest.mark.asyncio
async def test_lookup_raises_unavailable_on_a_5xx_not_a_cacheable_no_match():
    """
    GIVEN MusicBrainz answers HTTP 500 on every attempt
    WHEN lookup_original_release runs
    THEN it raises ProviderError musicbrainz_unavailable after every retry;
    returning (None, None) would be cached as a false negative that outlives
    the outage.
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = 500
    session.get.return_value = make_response_context(resp)

    with (
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "me@example.com"),
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(ProviderError) as excinfo:
            await lookup_original_release(session, "Artist", "Album", retries=2)

    assert excinfo.value.code == "musicbrainz_unavailable"
    assert session.get.call_count == 2


_RG_RUMOURS = {
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


def _answer(status, headers=None, body=None):
    resp = AsyncMock()
    resp.status = status
    resp.headers = headers or {}
    resp.json = AsyncMock(return_value=body if body is not None else {})
    return make_response_context(resp)


def _lookup_patches():
    return (
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_ENABLED", True),
        patch("scrobblescope.musicbrainz.MUSICBRAINZ_CONTACT", "me@example.com"),
        patch(
            "scrobblescope.musicbrainz.get_musicbrainz_limiter",
            return_value=NoopAsyncContext(),
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 503])
async def test_lookup_waits_the_retry_after_header_then_matches(status):
    """
    GIVEN MusicBrainz answers 429 or 503 with Retry-After: 2 and then a match
    WHEN lookup_original_release runs
    THEN it waits the header's seconds (plus bounded jitter) and returns the
    match, rather than caching the 429 as "no match".
    """
    session = MagicMock()
    session.get.side_effect = [
        _answer(status, {"Retry-After": "2"}),
        _answer(200, body=_RG_RUMOURS),
    ]
    p1, p2, p3 = _lookup_patches()
    with p1, p2, p3, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await lookup_original_release(session, "Fleetwood Mac", "Rumours")

    assert result == ("rg-rumours", "1977-02-04")
    (waited,), _ = mock_sleep.await_args
    assert 2 <= waited < 2.2


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 503])
async def test_lookup_backs_off_exponentially_without_a_retry_after(status):
    """
    GIVEN MusicBrainz answers 429 or 503 with no Retry-After twice, then 200
    WHEN lookup_original_release runs
    THEN each wait is longer than the last (2 ** attempt plus bounded
    jitter) and the match is returned.
    """
    session = MagicMock()
    session.get.side_effect = [
        _answer(status),
        _answer(status),
        _answer(200, body=_RG_RUMOURS),
    ]
    p1, p2, p3 = _lookup_patches()
    with p1, p2, p3, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await lookup_original_release(
            session, "Fleetwood Mac", "Rumours", retries=3
        )

    assert result == ("rg-rumours", "1977-02-04")
    first, second = (call.args[0] for call in mock_sleep.await_args_list)
    assert 1 <= first < 1.2
    assert 2 <= second < 2.2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, headers, code",
    [
        (429, {"Retry-After": "1"}, "musicbrainz_rate_limited"),
        (503, {"Retry-After": "1"}, "musicbrainz_rate_limited"),
        (429, {}, "musicbrainz_unavailable"),
        (503, {}, "musicbrainz_unavailable"),
    ],
)
async def test_exhausted_throttling_raises_and_caches_nothing(status, headers, code):
    """
    GIVEN MusicBrainz answers 429 or 503 on every attempt
    WHEN lookup_original_release runs, and then a release check drives it
    THEN it raises rate_limited only when a Retry-After was sent (else
    unavailable), and the release check writes nothing to the
    original-release cache.
    """
    session = MagicMock()
    session.get.side_effect = lambda *a, **k: _answer(status, headers)
    candidate = {
        "key": ("artist", "album"),
        "artist": "Artist",
        "album": "Album",
        "kind": "other",
    }
    state = {"checked": 0}
    p1, p2, p3 = _lookup_patches()
    with p1, p2, p3, patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ProviderError) as excinfo:
            await lookup_original_release(session, "Artist", "Album", retries=2)
        with patch(
            "scrobblescope.release_checks.batch_persist_original_release",
            new_callable=AsyncMock,
        ) as persist:
            await _check_candidate(session, MagicMock(), "job", candidate, {}, state)

    assert excinfo.value.code == code
    persist.assert_not_awaited()
    assert state["checked"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 503])
async def test_retry_after_over_the_cap_raises_at_once_without_sleeping(status):
    """
    GIVEN MusicBrainz answers 429 or 503 with a Retry-After above the cap
    WHEN lookup_original_release runs
    THEN it raises musicbrainz_rate_limited on the first answer and sleeps
    not at all.
    """
    session = MagicMock()
    session.get.side_effect = lambda *a, **k: _answer(
        status, {"Retry-After": str(MAX_RETRY_AFTER_SECONDS + 1)}
    )
    p1, p2, p3 = _lookup_patches()
    with p1, p2, p3, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(ProviderError) as excinfo:
            await lookup_original_release(session, "Artist", "Album", retries=3)

    assert excinfo.value.code == "musicbrainz_rate_limited"
    assert session.get.call_count == 1
    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_lookup_treats_a_404_as_a_definite_no_match():
    """
    GIVEN MusicBrainz answers 404
    WHEN lookup_original_release runs
    THEN it returns (None, None) after one request: a plain 4xx is an answer.
    """
    session = MagicMock()
    session.get.side_effect = lambda *a, **k: _answer(404)
    p1, p2, p3 = _lookup_patches()
    with p1, p2, p3, patch("asyncio.sleep", new_callable=AsyncMock):
        result = await lookup_original_release(session, "Artist", "Album")

    assert result == (None, None)
    assert session.get.call_count == 1
