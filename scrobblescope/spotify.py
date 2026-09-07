import base64
import logging
import time

from scrobblescope.config import (
    SPOTIFY_BATCH_RETRIES,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_SEARCH_RETRIES,
    spotify_token_cache,
)
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


async def fetch_spotify_album_details_batch(
    session, album_ids, token, semaphore=None, retries=SPOTIFY_BATCH_RETRIES
):
    """
    Fetches full album details for a list of up to 50 Spotify album IDs
    in a single API call.
    """
    if not album_ids:
        return {}

    url = "https://api.spotify.com/v1/albums"
    headers = {"Authorization": f"Bearer {token}"}
    # Spotify API takes a comma-separated string of IDs
    params = {"ids": ",".join(album_ids)}
    limiter = get_spotify_limiter()

    async def fetch_once():
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
                logging.error(
                    f"Failed to fetch batch album details. Status: {response.status}, Body: {await response.text()}"
                )
                return {}, None, True

    return await retry_with_semaphore(
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
