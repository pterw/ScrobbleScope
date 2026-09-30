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
from scrobblescope.errors import provider_failure
from scrobblescope.utils import (
    get_deezer_limiter,
    parse_retry_after,
    retry_with_semaphore,
)

_DEEZER_ERROR_QUOTA = 4


def _deezer_error_code(data):
    """Return the numeric error code from a Deezer error body, or None."""
    if not isinstance(data, dict):
        return None
    error = data.get("error")
    return error.get("code") if isinstance(error, dict) else None


async def _deezer_request(session, url, params, limiter, null_body=None):
    """Perform one rate-limited Deezer GET and classify the outcome.

    Returns the ``(result, retry_after, done)`` triple `retry_with_semaphore`
    reads, carrying the decoded body only when the request both succeeded and
    came back without an error code. Deezer reports failures with HTTP 200 and
    a code in the body, so a status check alone cannot separate a success from
    a quota refusal: code 4 is the retryable one and every other code is a
    terminal miss. Callers that need more than the raw body -- a search picking
    a candidate out of it -- inspect the body only when it is not None, so the
    two failure shapes pass straight through unchanged. A 200 whose body is
    JSON ``null`` was read, but says nothing: it returns *null_body* in its
    place, so a caller that keeps a partial answer can tell it from a terminal
    error (both give None otherwise).
    """
    async with limiter:
        async with session.get(url, params=params) as response:
            if response.status == 429:
                # Throttled at the HTTP layer (the quota code 4 below is the
                # 200-body form): honour Retry-After, default one second.
                retry_after = parse_retry_after(response.headers.get("Retry-After"))
                return None, retry_after, False
            if response.status >= 500 or response.status == 403:
                # An outage or a refusal, not an answer: retried, then raised
                # as deezer_unavailable rather than read as "no match".
                return None, None, False
            if response.status != 200:
                return None, None, True
            data = await response.json()
            if data is None:
                return null_body, None, True
            code = _deezer_error_code(data)
            if code == _DEEZER_ERROR_QUOTA:
                return None, 1, False
            if code is not None:
                return None, None, True
            return data, None, True


def _seconds(value):
    """Return *value* as a whole number of seconds, or 0 when it is not one."""
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


async def search_deezer_album(session, artist, album, retries=DEEZER_SEARCH_RETRIES):
    """Search Deezer for *artist*/*album* and return the matching album ID.

    The plain query ``f"{artist} {album}"`` outperforms Deezer's filtered
    ``artist:"..." album:"..."`` form, which favors tribute/cover results
    over the real album. A candidate is accepted only when
    ``normalize_name(candidate_artist, candidate_title)`` equals the key
    built from *artist*/*album* -- this never returns "the first result"
    as a guess. Returns None if no candidate matches. Raises ``ProviderError``
    when Deezer could not be read: throttled past the Retry-After cap or
    through every retry, a 5xx, a timeout. That is not "no match", and the
    caller records the album as unavailable instead.
    """
    key = normalize_name(artist, album)
    url = "https://api.deezer.com/search/album"
    params = {"q": f"{artist} {album}"}
    limiter = get_deezer_limiter()

    async def search_once():
        data, retry_after, done = await _deezer_request(session, url, params, limiter)
        if data is None:
            return None, retry_after, done
        # Every read tolerates a null or a foreign shape as "no candidate":
        # enrichment degrades, it never fails the job on a strange body.
        candidates = data.get("data") if isinstance(data, dict) else None
        for candidate in candidates if isinstance(candidates, list) else []:
            if not isinstance(candidate, dict):
                continue
            artist_object = candidate.get("artist")
            candidate_artist = (
                artist_object.get("name") if isinstance(artist_object, dict) else ""
            ) or ""
            candidate_title = candidate.get("title") or ""
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
        error_label="deezer.search",
        failure=provider_failure("deezer"),
    )


async def _fetch_deezer_json(
    session, url, params, retries, error_label, null_body=None
):
    """GET *url*, treating a 200-with-error-code-4 body as a retryable quota hit.

    *null_body* stands in for a 200 whose body is JSON ``null`` (see
    ``_deezer_request``).
    """
    limiter = get_deezer_limiter()

    async def fetch_once():
        return await _deezer_request(session, url, params, limiter, null_body)

    return await retry_with_semaphore(
        fetch_once,
        retries=retries,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=1,
        error_label=error_label,
        failure=provider_failure("deezer"),
    )


async def fetch_deezer_album(session, album_id, retries=DEEZER_DETAIL_RETRIES):
    """Fetch a Deezer album's details and full track list as an AlbumMetadata.

    ``/album/{id}`` lists at most 25 tracks even when ``nb_tracks`` reports
    more (the White Album reports 30 and lists 25); ``/album/{id}/tracks``
    with ``limit=500`` returns every track's duration in seconds. Returns
    None when Deezer answers that the album is not there, or answers with an
    album body of an unexpected shape (a null, a list): a miss, never a
    TypeError. Also None when the track call answers a terminal error: the
    album is a miss, so it is not persisted with empty durations. A track body
    that was read but carries no list (a JSON null, an object without ``data``)
    keeps the album, with no durations: its release metadata is still good. Raises
    ``ProviderError`` when Deezer could not be read (see ``search_deezer_album``).
    """
    album = await _fetch_deezer_json(
        session,
        f"https://api.deezer.com/album/{album_id}",
        None,
        retries,
        "deezer.album_details",
    )
    # A null or foreign body shape is a miss, exactly as it is in the search:
    # enrichment degrades, it never fails the job on a strange answer.
    if not isinstance(album, dict):
        return None

    tracks = await _fetch_deezer_json(
        session,
        f"https://api.deezer.com/album/{album_id}/tracks",
        {"limit": 500},
        retries,
        "deezer.album_tracks",
        null_body={},
    )
    if tracks is None:
        # The track call answered a terminal error (an error body, or a status
        # that is not a success): the durations were not read, and an album
        # filed with none would be persisted for METADATA_CACHE_TTL_DAYS and
        # drop out of the playtime ranking after Deezer recovers (R4-backend-10).
        # A miss is not persisted.
        return None
    track_rows = tracks.get("data") if isinstance(tracks, dict) else None
    if not isinstance(track_rows, list):
        track_rows = []

    # A track whose title is null (or not text) is skipped: normalising it
    # would raise TypeError and fail the whole job (F-B23-24). A duration that
    # is not a number counts as 0 rather than poisoning the play-time sum.
    track_durations = {
        normalize_track_name(t["title"]): _seconds(t.get("duration"))
        for t in track_rows
        if isinstance(t, dict) and isinstance(t.get("title"), str)
    }
    link = album.get("link")
    release_date = album.get("release_date")
    cover = album.get("cover_xl")
    return AlbumMetadata(
        provider="deezer",
        album_id=str(album_id),
        url=link
        if isinstance(link, str)
        else f"https://www.deezer.com/album/{album_id}",
        release_date=release_date if isinstance(release_date, str) else "",
        image_url=cover if isinstance(cover, str) else None,
        track_durations=track_durations,
    )
