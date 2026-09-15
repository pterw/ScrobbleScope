"""Deezer client: a fallback provider when Spotify cannot match or detail an
album (F-B21-59 -- Spotify removed the Get Several Albums endpoint for
Development Mode apps and postponed removal for existing ones with no new
date). No API key is required.

Deezer reports errors with HTTP 200 and a body of
``{"error": {"type": ..., "message": ..., "code": N}}``: 800 means "no
data" (a terminal miss), 4 means the request quota was exceeded and is
worth retrying after a short wait.

Attribution: read https://developers.deezer.com/guidelines before
rendering any Deezer-sourced result. Task 6 owns that gate; this module
only fetches data.
"""

from scrobblescope.config import DEEZER_DETAIL_RETRIES, DEEZER_SEARCH_RETRIES
from scrobblescope.domain import normalize_name, normalize_track_name
from scrobblescope.enrichment import AlbumMetadata
from scrobblescope.utils import get_deezer_limiter, retry_with_semaphore

_DEEZER_ERROR_QUOTA = 4


def _deezer_error_code(data):
    """Return the numeric error code from a Deezer error body, or None."""
    error = data.get("error")
    return error.get("code") if error else None


async def search_deezer_album(session, artist, album, retries=DEEZER_SEARCH_RETRIES):
    """Search Deezer for *artist*/*album* and return the matching album ID.

    The plain query ``f"{artist} {album}"`` outperforms Deezer's filtered
    ``artist:"..." album:"..."`` form, which favors tribute/cover results
    over the real album. A candidate is accepted only when
    ``normalize_name(candidate_artist, candidate_title)`` equals the key
    built from *artist*/*album* -- this never returns "the first result"
    as a guess. Returns None if no candidate matches.
    """
    key = normalize_name(artist, album)
    url = "https://api.deezer.com/search/album"
    params = {"q": f"{artist} {album}"}
    limiter = get_deezer_limiter()

    async def search_once():
        async with limiter:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None, None, True
                data = await response.json()
                code = _deezer_error_code(data)
                if code == _DEEZER_ERROR_QUOTA:
                    return None, 1, False
                if code is not None:
                    return None, None, True
                for candidate in data.get("data", []):
                    candidate_artist = candidate.get("artist", {}).get("name", "")
                    candidate_title = candidate.get("title", "")
                    if normalize_name(candidate_artist, candidate_title) == key:
                        return candidate.get("id"), None, True
                return None, None, True

    return await retry_with_semaphore(
        search_once,
        retries=retries,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=1,
        error_label=f"Deezer search for '{album}' by '{artist}'",
    )


async def _fetch_deezer_json(session, url, params, retries, error_label):
    """GET *url*, treating a 200-with-error-code-4 body as a retryable quota hit."""
    limiter = get_deezer_limiter()

    async def fetch_once():
        async with limiter:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None, None, True
                data = await response.json()
                code = _deezer_error_code(data)
                if code == _DEEZER_ERROR_QUOTA:
                    return None, 1, False
                if code is not None:
                    return None, None, True
                return data, None, True

    return await retry_with_semaphore(
        fetch_once,
        retries=retries,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=1,
        error_label=error_label,
    )


async def fetch_deezer_album(session, album_id, retries=DEEZER_DETAIL_RETRIES):
    """Fetch a Deezer album's details and full track list as an AlbumMetadata.

    ``/album/{id}`` lists at most 25 tracks even when ``nb_tracks`` reports
    more (the White Album reports 30 and lists 25); ``/album/{id}/tracks``
    with ``limit=500`` returns every track's duration in seconds. Returns
    None if either request fails after retries.
    """
    album = await _fetch_deezer_json(
        session,
        f"https://api.deezer.com/album/{album_id}",
        None,
        retries,
        f"Deezer album details for '{album_id}'",
    )
    if album is None:
        return None

    tracks = await _fetch_deezer_json(
        session,
        f"https://api.deezer.com/album/{album_id}/tracks",
        {"limit": 500},
        retries,
        f"Deezer album tracks for '{album_id}'",
    )
    if tracks is None:
        return None

    track_durations = {
        normalize_track_name(t.get("title", "")): t.get("duration", 0)
        for t in tracks.get("data", [])
    }
    return AlbumMetadata(
        provider="deezer",
        album_id=str(album_id),
        url=album.get("link", f"https://www.deezer.com/album/{album_id}"),
        release_date=album.get("release_date", ""),
        image_url=album.get("cover_xl"),
        track_durations=track_durations,
    )
