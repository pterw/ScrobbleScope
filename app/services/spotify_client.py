# app/services/spotify_client.py

import asyncio
import contextvars
import logging
import time

import aiohttp
from aiolimiter import AsyncLimiter
from flask import current_app  # To access app.config

# Import normalize_name from utils (as fetch_spotify_album_release_date uses it)
from app.utils import normalize_name, normalize_track_name

# Context-bound limiter (moved from app_old_backup.py)
_spotify_limiter = contextvars.ContextVar("spotify_limiter", default=None)


def get_spotify_limiter():
    limiter = _spotify_limiter.get()
    if limiter is None:
        # Reduced from 20 to 5 requests per second to be safer
        limiter = AsyncLimiter(5, 1)
        _spotify_limiter.set(limiter)
    return limiter


# Global token cache for Spotify (moved from app_old_backup.py)
spotify_token_cache = {"token": None, "expires_at": 0}


class SpotifyClient:
    def __init__(self):
        # Access API keys from Flask's current_app config
        self.client_id = current_app.config["SPOTIFY_CLIENT_ID"]
        self.client_secret = current_app.config["SPOTIFY_CLIENT_SECRET"]
        self.limiter = get_spotify_limiter()

    async def fetch_spotify_access_token(self):
        if spotify_token_cache["expires_at"] > time.time():
            return spotify_token_cache["token"]

        # Correct Spotify token URL
        url = "https://accounts.spotify.com/api/token"
        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}

        async with aiohttp.ClientSession() as s:
            try:
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
                    else:
                        body = await r.text()
                        logging.error(
                            f"Failed to fetch Spotify token. Status: {r.status}, Body: {body[:200]}"
                        )
                        return None
            except Exception as e:
                logging.error(f"Exception fetching Spotify token: {e}")
                return None

    async def fetch_spotify_track_durations(self, session, album_id, token):
        # Correct Spotify API URL for album tracks
        url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        headers = {"Authorization": f"Bearer {token}"}
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                album_data = await response.json()
                tracks = {}
                # Spotify API returns tracks in "items" under "tracks" object
                for t in album_data.get("items", []):
                    name_norm = normalize_track_name(t.get("name", ""))
                    tracks[name_norm] = t.get("duration_ms", 0) // 1000
                return tracks
            else:
                body = await response.text()
                logging.warning(
                    f"Failed to fetch track durations for album {album_id}. Status: {response.status}, Body: {body[:200]}"
                )
                return {}

    async def fetch_spotify_album_release_date(self, session, artist, album, token):
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": f"artist:{artist} album:{album}", "type": "album", "limit": 1}

        for attempt in range(3):
            try:
                async with self.limiter:
                    logging.debug(
                        f"[Attempt {attempt+1}/3] Fetching Spotify: {album} by {artist}"
                    )
                    async with session.get(
                        "https://api.spotify.com/v1/search",
                        params=params,
                        headers=headers,  # Correct Spotify API URL
                    ) as response:
                        if response.status == 429:
                            retry_after = response.headers.get("Retry-After", "1")
                            logging.warning(
                                f"⚠️ Spotify 429 rate limit hit. Retry after {retry_after} seconds "
                                f"on attempt {attempt + 1} for '{album}' by '{artist}'"
                            )
                            await asyncio.sleep(int(retry_after))
                            continue

                        if response.status != 200:
                            body = await response.text()
                            logging.warning(
                                f"❌ Spotify unexpected status {response.status} for {album} by {artist}. Body: {body[:200]}"
                            )
                            break

                        data = await response.json()
                        items = data.get("albums", {}).get("items", [])
                        if not items:
                            logging.debug(
                                f"🎯 Retrying with relaxed query: {artist} {album}"
                            )
                            relaxed_q = {
                                "q": f"{artist} {album}",
                                "type": "album",
                                "limit": 1,
                            }
                            async with session.get(
                                "https://api.spotify.com/v1/search",  # Correct Spotify API URL
                                params=relaxed_q,
                                headers=headers,
                            ) as fallback:
                                relaxed_data = await fallback.json()
                                relaxed_items = relaxed_data.get("albums", {}).get(
                                    "items", []
                                )
                                if not relaxed_items:
                                    logging.info(
                                        f"🔎 No match found on Spotify for {album} by {artist}"
                                    )
                                    # This part related to UNMATCHED will be handled by app/state.py
                                    # For now, just return empty dict
                                    return {}
                                album_info = relaxed_items[0]
                                return {
                                    "release_date": album_info.get("release_date"),
                                    "album_image": album_info.get("images", [{}])[
                                        0
                                    ].get("url"),
                                    "id": album_info.get(
                                        "id"
                                    ),  # Ensure ID is returned for track durations
                                }
                        album_info = items[0]
                        return {
                            "release_date": album_info.get("release_date"),
                            "album_image": album_info.get("images", [{}])[0].get("url"),
                            "id": album_info.get("id"),
                        }

            except Exception as e:
                logging.error(
                    f"Spotify exception on attempt {attempt+1} for {album} by {artist}: {e}"
                )

            backoff = 2**attempt
            logging.debug(
                f"🔁 Backing off for {backoff} seconds before retrying {album} by {artist}"
            )
            await asyncio.sleep(backoff)

        return {}
