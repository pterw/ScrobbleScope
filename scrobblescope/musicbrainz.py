"""MusicBrainz client: corrects a reissue's release year to the album's
original release date. Spotify and Deezer both date a remaster by its
reissue (Deezer dates The Beatles' White Album 2015-12-24); MusicBrainz's
release-group carries ``first-release-date``, the original.

MusicBrainz allows 1 request per second per IP and blocks anonymous
clients outright, so every request needs a contact address in the
User-Agent. A wrong match is worse than no match here -- a rejected result
costs nothing, but a bad correction would misdate an album silently -- so a
candidate is accepted only when it clears both a score floor and a
normalized-name match, never on score alone.

Source: https://musicbrainz.org/doc/MusicBrainz_API and
https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting.
"""

from scrobblescope.config import (
    MUSICBRAINZ_CONTACT,
    MUSICBRAINZ_ENABLED,
    MUSICBRAINZ_SEARCH_RETRIES,
)
from scrobblescope.domain import normalize_name
from scrobblescope.utils import get_musicbrainz_limiter, retry_with_semaphore

_APP_VERSION = "1.0"
_MIN_MATCH_SCORE = 90
_SEARCH_URL = "https://musicbrainz.org/ws/2/release-group/"
_RATE_LIMIT_STATUS = 503

# Lucene query-syntax special characters that must be escaped in a search
# term: https://lucene.apache.org/core/.../QueryParserSyntax.html
_LUCENE_SPECIAL_CHARS = set('+-&|!(){}[]^"~*?:\\/')


def _escape_lucene(text):
    """Escape Lucene query-syntax special characters in *text*."""
    return "".join(f"\\{ch}" if ch in _LUCENE_SPECIAL_CHARS else ch for ch in text)


def _build_release_group_query(artist, title):
    """Build the Lucene query MusicBrainz's release-group search expects."""
    return (
        f'releasegroup:"{_escape_lucene(title)}" AND artist:"{_escape_lucene(artist)}"'
    )


def _artist_credit_name(artist_credit):
    """Join a release-group's artist-credit list into one display name."""
    return "".join(
        f"{credit.get('name', '')}{credit.get('joinphrase', '')}"
        for credit in artist_credit
    )


def _is_matching_candidate(candidate, key):
    """Return True when *candidate* clears the score floor and matches *key*.

    MusicBrainz's score ranks text similarity, not identity -- a
    high-scoring tribute act or a same-titled album by a different artist
    can still clear the floor. Both the score and the normalized
    (artist, title) pair must agree with *key* before a match is trusted.
    """
    if candidate.get("score", 0) < _MIN_MATCH_SCORE:
        return False
    candidate_key = normalize_name(
        _artist_credit_name(candidate.get("artist-credit", [])),
        candidate.get("title", ""),
    )
    return candidate_key == key


def _musicbrainz_headers():
    return {"User-Agent": f"ScrobbleScope/{_APP_VERSION} ( {MUSICBRAINZ_CONTACT} )"}


async def lookup_original_release(
    session, artist, album, retries=MUSICBRAINZ_SEARCH_RETRIES
):
    """Look up *artist*/*album*'s original release-group and first-release-date.

    Returns ``(mb_release_group_id, "YYYY-MM-DD")`` on a trusted match, or
    ``(None, None)`` when nothing matches closely enough -- both outcomes
    are cacheable. Also returns ``(None, None)`` without making a request
    when MusicBrainz is disabled or no contact address is configured:
    MusicBrainz blocks anonymous clients, so an unconfigured contact would
    only guarantee a rejected request.
    """
    if not MUSICBRAINZ_ENABLED or not MUSICBRAINZ_CONTACT:
        return None, None

    key = normalize_name(artist, album)
    params = {"query": _build_release_group_query(artist, album), "fmt": "json"}
    headers = _musicbrainz_headers()
    limiter = get_musicbrainz_limiter()

    async def search_once():
        async with limiter:
            async with session.get(
                _SEARCH_URL, params=params, headers=headers
            ) as response:
                if response.status == _RATE_LIMIT_STATUS:
                    return None, 1, False
                if response.status != 200:
                    return None, None, True
                data = await response.json()
                for candidate in data.get("release-groups", []):
                    if _is_matching_candidate(candidate, key):
                        match = (
                            candidate.get("id"),
                            candidate.get("first-release-date"),
                        )
                        return match, None, True
                return None, None, True

    result = await retry_with_semaphore(
        search_once,
        retries=retries,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=1,
        error_label=f"MusicBrainz release-group search for '{album}' by '{artist}'",
    )
    return result if result is not None else (None, None)
