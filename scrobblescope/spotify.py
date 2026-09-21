import asyncio
import base64
import logging
import time

from scrobblescope.config import (
    SPOTIFY_BATCH_RETRIES,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_SEARCH_CONCURRENCY,
    SPOTIFY_SEARCH_RETRIES,
    spotify_token_cache,
)
from scrobblescope.domain import normalize_track_name
from scrobblescope.enrichment import AlbumMetadata
from scrobblescope.utils import (
    create_optimized_session,
    get_spotify_limiter,
    retry_with_semaphore,
)


async def fetch_spotify_access_token():
    """Return a valid Spotify access token, refreshing from the API if expired."""
    if spotify_token_cache["expires_at"] > time.time():
        return spotify_token_cache["token"]
    url = "https://accounts.spotify.com/api/token"
    assert SPOTIFY_CLIENT_ID is not None, "SPOTIFY_CLIENT_ID not set"
    assert SPOTIFY_CLIENT_SECRET is not None, "SPOTIFY_CLIENT_SECRET not set"
    # aiohttp 3.14 deprecates BasicAuth for removal in 4.0; the documented
    # replacement is a pre-encoded Authorization header. base64 is stdlib,
    # so no new dependency.
    credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {encoded}"}
    data = {"grant_type": "client_credentials"}
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
    logging.error("Failed to fetch Spotify token")
    return None


async def search_for_spotify_album_id(session, artist, album, token, semaphore=None):
    """
    Searches Spotify for a single album and returns its Spotify ID.
    Optimized: Uses relaxed query first (faster, higher success rate).
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
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    logging.warning(
                        f"Spotify 429 on '{album}' by '{artist}'. Retry in {retry_after}s"
                    )
                    return None, retry_after, False

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
        error_label=f"Spotify search for '{album}' by '{artist}'",
    )


#: Statuses that mean the Get Several Albums endpoint itself is gone, not that
#: one request failed. Spotify removed that endpoint for Development Mode apps
#: in February 2026 and postponed the removal for existing apps with no new
#: date (F-B21-59). 401 is excluded because single-album calls would fail on
#: the same token, and 5xx because an outage is no reason to multiply calls.
BATCH_ENDPOINT_GONE_STATUSES = frozenset({403, 404, 410})


async def fetch_spotify_album_details_single(
    session, album_id, token, retries=SPOTIFY_BATCH_RETRIES
):
    """Fetch one album from GET /v1/albums/{id}; return None if unavailable.

    Returns the same album object the batch endpoint returns inside its
    `albums` list, so callers need no second extraction path.
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
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    return None, retry_after, False
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
        error_label=f"Spotify album details for '{album_id}'",
    )


async def _fetch_album_details_one_by_one(session, album_ids, token, retries):
    """Fetch albums individually and key them by ID, dropping unavailable ones."""
    albums = await asyncio.gather(
        *(
            fetch_spotify_album_details_single(session, album_id, token, retries)
            for album_id in album_ids
        )
    )
    return {album["id"]: album for album in albums if album}


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
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    logging.warning(
                        f"⚠️ Batch fetch 429 hit. Retrying after {retry_after}s."
                    )
                    return {}, retry_after, False
                if response.status in BATCH_ENDPOINT_GONE_STATUSES:
                    gone_status = response.status
                    return {}, None, True
                logging.error(
                    f"Failed to fetch batch album details. Status: {response.status}, Body: {await response.text()}"
                )
                return {}, None, True

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
        error_label="Spotify batch album details",
    )
    if gone_status is None:
        return details
    if on_fallback is not None:
        on_fallback(gone_status)
    return await _fetch_album_details_one_by_one(session, album_ids, token, retries)


async def enrich_albums(session, misses, token):
    """Enrich a batch of cache-miss albums via Spotify search + batch detail.

    *misses* is a dict keyed by (artist_norm, album_norm) tuples; only the
    keys are read here, so a caller may pass the same {key: original_data}
    shape it already keeps for other purposes. Returns (matched, unmatched):
    ``matched`` is {key: AlbumMetadata} for every album Spotify both found
    and returned details for; ``unmatched`` is the set of keys Spotify could
    not find, or found but could not detail. This module owns its own
    retry, limiter and matching -- the caller does not see how the match was
    made, only the result.
    """
    if not misses:
        return {}, set()

    search_semaphore = asyncio.Semaphore(SPOTIFY_SEARCH_CONCURRENCY)

    async def search_one(key):
        artist, album = key
        spotify_id = await search_for_spotify_album_id(
            session, artist, album, token, semaphore=search_semaphore
        )
        return key, spotify_id

    search_results = await asyncio.gather(*(search_one(key) for key in misses))

    id_to_key = {}
    unmatched = set()
    for key, spotify_id in search_results:
        if spotify_id:
            id_to_key[spotify_id] = key
        else:
            unmatched.add(key)

    matched = {}
    if id_to_key:
        album_details = await fetch_spotify_album_details_batch(
            session, list(id_to_key.keys()), token
        )
        for spotify_id, key in id_to_key.items():
            details = album_details.get(spotify_id)
            if not details:
                unmatched.add(key)
                continue
            images = details.get("images") or [{}]
            matched[key] = AlbumMetadata(
                provider="spotify",
                album_id=spotify_id,
                url=details.get("external_urls", {}).get(
                    "spotify", f"https://open.spotify.com/album/{spotify_id}"
                ),
                release_date=details.get("release_date", ""),
                image_url=images[0].get("url"),
                track_durations={
                    normalize_track_name(t.get("name", "")): t.get("duration_ms", 0)
                    // 1000
                    for t in details.get("tracks", {}).get("items", [])
                },
            )

    return matched, unmatched


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
    except Exception as e:
        logging.warning(
            f"Error querying Spotify artist spotlight for '{artist_name or artist_id}': {e}"
        )
    return None
