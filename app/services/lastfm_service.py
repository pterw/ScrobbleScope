"""Functions for interacting with the Last.fm API."""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import aiohttp

from config import Config

from ..cache import get_cached_response, set_cached_response
from ..state import get_lastfm_limiter, get_session
from ..utils import normalize_name, normalize_track_name

async def check_user_exists(username: str) -> bool:
    """Return ``True`` if the Last.fm user exists."""


    url = "https://ws.audioscrobbler.com/2.0/"

    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": Config.LASTFM_API_KEY,
        "format": "json",
    }

    session = await get_session()
    async with session.get(url, params=params) as resp:
        if resp.status == 200:
            return True
        if resp.status == 404:
            return False
        resp.raise_for_status()
        return False


async def fetch_recent_tracks_page_async(
    session: aiohttp.ClientSession,
    username: str,
    from_ts: int,
    to_ts: int,
    page: int,
    retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """Fetch a single page of recent tracks from Last.fm."""
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getrecenttracks",
        "user": username,
        "api_key": Config.LASTFM_API_KEY,
        "format": "json",
        "from": from_ts,
        "to": to_ts,
        "limit": 200,
        "page": page,
    }

    cached = get_cached_response(url, params)
    if cached:
        return cached

    limiter = get_lastfm_limiter()
    for attempt in range(retries):
        try:
            async with limiter:
                async with session.get(url, params=params) as resp:
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", "1"))
                        await asyncio.sleep(retry_after)
                        continue
                    if resp.status == 404:
                        raise ValueError(f"User '{username}' not found on Last.fm")
                    if resp.status != 200:
                        break
                    data = await resp.json()
                    set_cached_response(url, data, params)
                    return data
        except Exception:
            await asyncio.sleep(2**attempt)
    return None


async def fetch_pages_batch_async(
    session: aiohttp.ClientSession,
    username: str,
    from_ts: int,
    to_ts: int,
    pages: Iterable[int],
) -> List[Optional[Dict[str, Any]]]:
    """Fetch a batch of pages concurrently."""
    tasks = [
        fetch_recent_tracks_page_async(session, username, from_ts, to_ts, p)
        for p in pages
    ]
    return await asyncio.gather(*tasks)


async def fetch_all_recent_tracks_async(
    username: str, from_ts: int, to_ts: int
) -> List[Dict[str, Any]]:
    """Retrieve all recent tracks for the given time range."""
    session = await get_session()
    first = await fetch_recent_tracks_page_async(session, username, from_ts, to_ts, 1)
    if not first or "recenttracks" not in first:
        return []

    total_pages = int(first["recenttracks"]["@attr"]["totalPages"])
    pages = [first]
    batch_size = 20
    for start in range(2, total_pages + 1, batch_size):
        end = min(start + batch_size, total_pages + 1)
        batch = await fetch_pages_batch_async(
            session, username, from_ts, to_ts, range(start, end)
        )
        pages.extend([p for p in batch if p])
    return pages


async def fetch_top_albums_async(
    username: str, year: int, min_plays: int = 10, min_tracks: int = 3
) -> Dict[tuple[str, str], Dict[str, Any]]:
    """Return a mapping of normalized album keys to play statistics."""
    from_ts = int(datetime(year, 1, 1).timestamp())
    to_ts = int(datetime(year, 12, 31, 23, 59, 59).timestamp())
    pages = await fetch_all_recent_tracks_async(username, from_ts, to_ts)
    albums: Dict[tuple[str, str], Dict[str, Any]] = defaultdict(
        lambda: {"play_count": 0, "track_counts": defaultdict(int)}
    )
    for page in pages:
        for t in page.get("recenttracks", {}).get("track", []):
            alb = t.get("album", {}).get("#text", "...")
            art = t.get("artist", {}).get("#text", "...")
            name = t.get("name", "...")
            date = t.get("date", {}).get("uts")
            if not date:
                continue
            ts = int(date)
            if ts < from_ts or ts > to_ts:
                continue
            if alb and art and name:
                key = normalize_name(art, alb)
                if "original_artist" not in albums[key]:
                    albums[key]["original_artist"] = art
                    albums[key]["original_album"] = alb
                albums[key]["play_count"] += 1
                n = normalize_track_name(name)
                albums[key]["track_counts"][n] += 1
    return {
        k: v
        for k, v in albums.items()
        if v["play_count"] >= min_plays and len(v["track_counts"]) >= min_tracks
    }
