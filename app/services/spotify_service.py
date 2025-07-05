"""Helper functions for interacting with the Spotify API."""

import asyncio
from typing import Any, Dict, Optional

import aiohttp

from config import Config

from ..cache import get_cached_response, set_cached_response
from ..state import get_spotify_limiter
from ..utils import normalize_name, normalize_track_name

spotify_token_cache = {"token": None, "expires_at": 0.0}


async def fetch_spotify_access_token() -> Optional[str]:
    """Retrieve an application access token from Spotify."""
    if spotify_token_cache["expires_at"] > asyncio.get_event_loop().time():
        return spotify_token_cache["token"]

    url = "https://accounts.spotify.com/api/token"
    auth = aiohttp.BasicAuth(Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, auth=auth) as resp:
            if resp.status == 200:
                token_data = await resp.json()
                spotify_token_cache.update(
                    {
                        "token": token_data["access_token"],
                        "expires_at": (
                            asyncio.get_event_loop().time() + token_data["expires_in"]
                        ),
                    }
                )
                return spotify_token_cache["token"]
    return None


async def fetch_spotify_track_durations(
    session: aiohttp.ClientSession, album_id: str, token: str
) -> Dict[str, int]:
    """Return a mapping of normalized track names to their duration in seconds."""
    url = f"https://api.spotify.com/v1/albums/{album_id}"
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            album_data = await resp.json()
            tracks = {}
            for t in album_data.get("tracks", {}).get("items", []):
                name_norm = normalize_track_name(t.get("name", ""))
                tracks[name_norm] = t.get("duration_ms", 0) // 1000
            return tracks
    return {}


async def fetch_spotify_album_release_date(
    session: aiohttp.ClientSession, artist: str, album: str, token: str
) -> Dict[str, Any]:
    """Search Spotify for an album and return metadata if found."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": f"artist:{artist} album:{album}", "type": "album", "limit": 1}
    limiter = get_spotify_limiter()
    for attempt in range(3):
        try:
            async with limiter:
                async with session.get(
                    "https://api.spotify.com/v1/search", params=params, headers=headers
                ) as resp:
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", "1"))
                        await asyncio.sleep(retry_after)
                        continue
                    if resp.status != 200:
                        break
                    data = await resp.json()
                    items = data.get("albums", {}).get("items", [])
                    if not items:
                        relaxed_q = {
                            "q": f"{artist} {album}",
                            "type": "album",
                            "limit": 1,
                        }
                        async with session.get(
                            "https://api.spotify.com/v1/search",
                            params=relaxed_q,
                            headers=headers,
                        ) as fallback:
                            relaxed_data = await fallback.json()
                            relaxed_items = relaxed_data.get("albums", {}).get(
                                "items", []
                            )
                            if not relaxed_items:
                                key = "|".join(normalize_name(artist, album))
                                set_cached_response(key, {"reason": "No Spotify match"})
                                return {}
                            album_info = relaxed_items[0]
                            return {
                                "release_date": album_info.get("release_date"),
                                "album_image": album_info.get("images", [{}])[0].get(
                                    "url"
                                ),
                            }
                    album_info = items[0]
                    return {
                        "release_date": album_info.get("release_date"),
                        "album_image": album_info.get("images", [{}])[0].get("url"),
                        "id": album_info.get("id"),
                    }
        except Exception:
            await asyncio.sleep(2**attempt)
    return {}
