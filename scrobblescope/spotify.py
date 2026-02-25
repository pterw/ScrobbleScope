import asyncio
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
    auth = aiohttp.BasicAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}
    async with create_optimized_session() as s:
        async with s.post(url, data=data, auth=auth) as r:
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
        backoff=lambda _a: 1,
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
