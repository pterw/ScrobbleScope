import asyncio
import base64
import logging
import time

import aiohttp

from scrobblescope.config import (
    SPOTIFY_BATCH_RETRIES,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_SEARCH_RETRIES,
    spotify_token_cache,
)
from scrobblescope.domain import normalize_track_name
from scrobblescope.enrichment import AlbumMetadata
from scrobblescope.errors import ProviderError, provider_failure
from scrobblescope.utils import (
    create_optimized_session,
    get_spotify_limiter,
    parse_retry_after,
    retry_with_semaphore,
)


async def fetch_spotify_access_token():
    """Return a valid Spotify access token, refreshing from the API if expired.

    Returns None when no token can be had (a non-200 answer, a timeout or a
    connection error on the token request), and every caller already treats
    None as "Spotify unavailable": the album pipeline falls back to Deezer
    and the spotlight keeps the artwork on screen. Missing credentials take
    that same path. They used to be `assert`ed, which `python -O` strips and
    which otherwise raised past the fallback and failed the job (F-B22-2).
    Production cannot start without them (``app._validate_api_keys``), so
    this branch is reached in dev mode only.
    """
    if spotify_token_cache["expires_at"] > time.time():
        return spotify_token_cache["token"]
    if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        logging.error("Spotify credentials are not configured; no token requested")
        return None
    url = "https://accounts.spotify.com/api/token"
    # aiohttp 3.14 deprecates BasicAuth for removal in 4.0; the documented
    # replacement is a pre-encoded Authorization header. base64 is stdlib,
    # so no new dependency.
    credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {encoded}"}
    data = {"grant_type": "client_credentials"}
    try:
        async with create_optimized_session() as s:
            async with s.post(url, data=data, headers=headers) as r:
                if r.status == 200:
                    token_data = await r.json()
                    spotify_token_cache.update(
                        {
                            "token": token_data["access_token"],
                            "expires_at": time.time() + token_data["expires_in"],
                        }
                    )
                    return spotify_token_cache["token"]
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        # The token endpoint not answering is Spotify being unavailable, the
        # same as a non-200 answer: the caller degrades to Deezer.
        logging.error(f"Spotify token request failed: {type(exc).__name__}")
    logging.error("Failed to fetch Spotify token")
    return None


async def search_for_spotify_album_id(session, artist, album, token, semaphore=None):
    """
    Searches Spotify for a single album and returns its Spotify ID, or None
    when Spotify answered and had no match.
    Optimized: Uses relaxed query first (faster, higher success rate).

    A search Spotify could not answer is not a miss: a 429 (or a Retry-After
    above the cap), a 5xx, a timeout or a connection error that outlasts the
    retries raises ``ProviderError`` (``spotify_rate_limited`` or
    ``spotify_unavailable``). The search phase catches it per album, so that
    album falls back to Deezer and, failing that, is listed as unavailable;
    the job fails only when no search was answered and Deezer enriched nothing.
    """
    headers = {"Authorization": f"Bearer {token}"}
    # Use relaxed query directly - it has better success rate and avoids double-search
    params = {"q": f"{artist} {album}", "type": "album", "limit": 3}
    limiter = get_spotify_limiter()

    async def search_once():
        async with limiter:
            async with session.get(
                "https://api.spotify.com/v1/search", params=params, headers=headers
            ) as response:
                if response.status == 429:
                    retry_after = parse_retry_after(response.headers.get("Retry-After"))
                    logging.warning(
                        f"Spotify 429 on spotify.search. Retry in {retry_after}s"
                    )
                    return None, retry_after, False

                if response.status >= 500:
                    # An outage, not an answer: retried, and raised as
                    # spotify_unavailable once the retries are spent.
                    return None, None, False

                if response.status != 200:
                    return None, None, True

                data = await response.json()
                items = data.get("albums", {}).get("items", [])
                if items:
                    return items[0].get("id"), None, True

                return None, None, True

    return await retry_with_semaphore(
        search_once,
        retries=SPOTIFY_SEARCH_RETRIES,
        semaphore=semaphore,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=1,
        jitter=lambda a: (abs(hash((artist, album, a))) % 200) / 1000.0,
        error_label="spotify.search",
        failure=provider_failure("spotify"),
    )


#: Statuses that mean the Get Several Albums endpoint itself is gone, not that
#: one request failed. Spotify removed that endpoint for Development Mode apps
#: in February 2026 and postponed the removal for existing apps with no new
#: date (F-B21-59). 401 is excluded because single-album calls would fail on
#: the same token, and 5xx because an outage is no reason to multiply calls.
BATCH_ENDPOINT_GONE_STATUSES = frozenset({403, 404, 410})


class AlbumDetails(dict):
    """Album details keyed by Spotify ID, plus the IDs Spotify could not answer.

    A plain ``dict`` to every reader. ``unanswered`` holds the IDs whose
    detail call was refused or failed (a 5xx, a timeout, a 429 that outlasted
    the retries), as distinct from an ID Spotify answered but returned nothing
    for. The detail phase files those albums as unavailable, not as unmatched.
    """

    def __init__(self, details=(), unanswered=()):
        super().__init__(details)
        self.unanswered = frozenset(unanswered)


async def fetch_spotify_album_details_single(
    session, album_id, token, retries=SPOTIFY_BATCH_RETRIES
):
    """Fetch one album from GET /v1/albums/{id}; return None if unavailable.

    Returns the same album object the batch endpoint returns inside its
    `albums` list, so callers need no second extraction path. None means
    Spotify answered without the album. A call Spotify could not answer (a
    5xx, a timeout, a 429 that outlasts the retries) raises ``ProviderError``.
    """
    url = f"https://api.spotify.com/v1/albums/{album_id}"
    headers = {"Authorization": f"Bearer {token}"}
    limiter = get_spotify_limiter()

    async def fetch_once():
        async with limiter:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json(), None, True
                if response.status == 429:
                    retry_after = parse_retry_after(response.headers.get("Retry-After"))
                    return None, retry_after, False
                if response.status >= 500:
                    return None, None, False
                return None, None, True

    return await retry_with_semaphore(
        fetch_once,
        retries=retries,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=lambda a: 2**a,
        jitter=lambda a: (abs(hash((album_id, a))) % 200) / 1000.0,
        error_label="spotify.album_details",
        failure=provider_failure("spotify"),
    )


async def _fetch_album_details_one_by_one(session, album_ids, token, retries):
    """Fetch albums individually and key them by ID, dropping unavailable ones.

    An album Spotify could not answer for is dropped and listed in the
    result's ``unanswered``; one such album does not lose its siblings.
    """
    unanswered = set()

    async def fetch_one(album_id):
        try:
            return await fetch_spotify_album_details_single(
                session, album_id, token, retries
            )
        except ProviderError:
            unanswered.add(album_id)
            return None

    albums = await asyncio.gather(*(fetch_one(album_id) for album_id in album_ids))
    return AlbumDetails(
        {album["id"]: album for album in albums if album}, unanswered=unanswered
    )


async def fetch_spotify_album_details_batch(
    session,
    album_ids,
    token,
    semaphore=None,
    retries=SPOTIFY_BATCH_RETRIES,
    on_fallback=None,
):
    """
    Fetches full album details for a list of up to 50 Spotify album IDs
    in a single API call.

    When the batch endpoint answers with a status in
    BATCH_ENDPOINT_GONE_STATUSES, falls back to one GET /v1/albums/{id} call
    per album and calls ``on_fallback(status)`` so the caller can report it.

    Returns an ``AlbumDetails`` (a dict). A batch Spotify could not answer (a
    5xx, a timeout, a 429 that outlasts the retries) comes back empty with
    every requested ID in ``unanswered``: unavailable, not "no details".
    """
    if not album_ids:
        return {}

    url = "https://api.spotify.com/v1/albums"
    headers = {"Authorization": f"Bearer {token}"}
    # Spotify API takes a comma-separated string of IDs
    params = {"ids": ",".join(album_ids)}
    limiter = get_spotify_limiter()
    gone_status = None

    async def fetch_once():
        nonlocal gone_status
        async with limiter:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # response is a dict with an 'albums' key, which is a list.
                    # converts this list into a dict keyed by album ID for easy lookup.
                    return (
                        {
                            album["id"]: album
                            for album in data.get("albums", [])
                            if album
                        },
                        None,
                        True,
                    )
                if response.status == 429:
                    retry_after = parse_retry_after(response.headers.get("Retry-After"))
                    logging.warning(
                        f"⚠️ Batch fetch 429 hit. Retrying after {retry_after}s."
                    )
                    return {}, retry_after, False
                if response.status in BATCH_ENDPOINT_GONE_STATUSES:
                    gone_status = response.status
                    return {}, None, True
                if response.status >= 500:
                    return {}, None, False
                logging.error(
                    f"Failed to fetch batch album details. Status: {response.status}, Body: {await response.text()}"
                )
                return {}, None, True

    try:
        details = await retry_with_semaphore(
            fetch_once,
            retries=retries,
            semaphore=semaphore,
            is_done=lambda t: t[2],
            get_retry_after=lambda t: t[1],
            extract_result=lambda t: t[0],
            default={},
            backoff=lambda a: 2**a,
            jitter=lambda a: (abs(hash((tuple(album_ids), a))) % 200) / 1000.0,
            error_label="spotify.batch_details",
            failure=provider_failure("spotify"),
        )
    except ProviderError:
        return AlbumDetails(unanswered=album_ids)
    if gone_status is None:
        return AlbumDetails(details)
    if on_fallback is not None:
        on_fallback(gone_status)
    return await _fetch_album_details_one_by_one(session, album_ids, token, retries)


def album_metadata_from_details(spotify_id, details):
    """Translate one Spotify album object into the provider contract.

    The one place the application reads Spotify's album JSON. The
    orchestrator's detail phase files what this returns and never drills into
    the payload itself (global rule 4, F-B22-7). A sparse payload degrades
    field by field -- no images gives ``image_url=None``, no external URL
    falls back to the album's canonical URL -- rather than raising.

    Args:
        spotify_id: The album id Spotify issued.
        details: One album object from Get Album or Get Several Albums.

    Returns:
        AlbumMetadata with ``provider="spotify"`` and track durations in
        whole seconds, keyed by ``normalize_track_name``.
    """
    images = details.get("images") or [{}]
    return AlbumMetadata(
        provider="spotify",
        album_id=spotify_id,
        url=details.get("external_urls", {}).get(
            "spotify", f"https://open.spotify.com/album/{spotify_id}"
        ),
        release_date=details.get("release_date", ""),
        image_url=images[0].get("url"),
        track_durations={
            normalize_track_name(t.get("name", "")): t.get("duration_ms", 0) // 1000
            for t in details.get("tracks", {}).get("items", [])
        },
    )


def _artist_spotlight_details(artist, artist_name=None, artist_id=None):
    """Normalize artist payloads while preserving missing-field defaults."""
    images = artist.get("images", [])
    return {
        "name": artist.get("name", artist_name),
        "artist_id": artist.get("id", artist_id),
        "image_url": images[0].get("url") if images else None,
        "spotify_url": artist.get("external_urls", {}).get("spotify"),
    }


async def _request_spotlight_artist(session, headers, artist_name, artist_id):
    """Look up by ID, falling back to name after an unsuccessful HTTP response.

    Return None for unsuccessful or empty searches. Transport and decoding
    exceptions propagate to the caller's shared logging and fallback boundary.
    """
    if artist_id:
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return _artist_spotlight_details(
                    await response.json(), artist_name, artist_id
                )
    if artist_name:
        params = {"q": f"artist:{artist_name}", "type": "artist", "limit": 1}
        async with session.get(
            "https://api.spotify.com/v1/search", params=params, headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                items = data.get("artists", {}).get("items", [])
                if items:
                    return _artist_spotlight_details(items[0], artist_name)
    return None


async def fetch_spotify_artist_spotlight(
    session, artist_name=None, artist_id=None, token=None
):
    """Fetch optional spotlight metadata within the limiter, logging failures.

    Missing credentials or identifiers and failed lookups return None so
    callers can retain the album artwork already displayed on the card.
    """
    if not token or (not artist_name and not artist_id):
        return None

    headers = {"Authorization": f"Bearer {token}"}
    limiter = get_spotify_limiter()
    try:
        async with limiter:
            return await _request_spotlight_artist(
                session, headers, artist_name, artist_id
            )
    # The spotlight is decorative; None keeps the card's existing artwork.
    except Exception as e:  # noqa: BLE001
        logging.warning(f"Error in spotify.artist_spotlight: {type(e).__name__}")
    return None
