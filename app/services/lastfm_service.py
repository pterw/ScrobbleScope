"""Functions for interacting with the Last.fm API."""

import aiohttp

from config import Config


async def check_user_exists(username: str) -> bool:
    """Return ``True`` if the Last.fm user exists."""

    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": Config.LASTFM_API_KEY,
        "format": "json",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return True
            if resp.status == 404:
                return False
            resp.raise_for_status()
            return False
