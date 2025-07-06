# app/services/lastfm_client.py

import asyncio
import contextvars
import logging
from collections import defaultdict  # Added for fetch_top_albums_async
from datetime import datetime  # Added for fetch_top_albums_async

import aiohttp
from aiolimiter import AsyncLimiter
from flask import current_app  # To access app.config

# Import normalize functions from utils
from app.utils import normalize_name, normalize_track_name

# Context-bound limiter (moved from app_old_backup.py)
_lastfm_limiter = contextvars.ContextVar("lastfm_limiter", default=None)


def get_lastfm_limiter():
    limiter = _lastfm_limiter.get()
    if limiter is None:
        # Reduced from 20 to 5 requests per second to be safer
        limiter = AsyncLimiter(5, 1)
        _lastfm_limiter.set(limiter)
    return limiter


class LastFmClient:
    def __init__(self):
        # Access API key from Flask's current_app config
        self.api_key = current_app.config["LASTFM_API_KEY"]
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        self.limiter = get_lastfm_limiter()

    async def check_user_exists(self, username):
        """Verify if a Last.fm user exists before proceeding with album fetching."""
        params = {
            "method": "user.getinfo",
            "user": username,
            "api_key": self.api_key,
            "format": "json",
        }
        # Caching will be handled by a dedicated cache module later
        # For now, we'll just make the direct call
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status == 200:
                        return True
                    elif resp.status == 404:
                        return False
                    else:
                        resp.raise_for_status()
                        return False
            except Exception as e:
                logging.error(f"Error checking Last.fm user existence: {e}")
                return True  # Return True to allow further processing, specific error will be caught later

    async def fetch_recent_tracks_page_async(
        self, session, username, from_ts, to_ts, page, retries=3
    ):
        params = {
            "method": "user.getrecenttracks",
            "user": username,
            "api_key": self.api_key,
            "format": "json",
            "from": from_ts,
            "to": to_ts,
            "limit": 200,
            "page": page,
        }

        for attempt in range(retries):
            try:
                async with self.limiter:
                    logging.debug(f"Requesting Last.fm page {page}")
                    async with session.get(self.base_url, params=params) as resp:
                        if resp.status == 429:
                            retry_after = resp.headers.get("Retry-After", "1")
                            logging.warning(
                                f"⚠️ Last.fm rate limit hit. Retry after {retry_after} seconds."
                            )
                            await asyncio.sleep(int(retry_after))
                            continue
                        elif resp.status == 404:
                            logging.error(f"User {username} not found on Last.fm")
                            raise ValueError(f"User '{username}' not found on Last.fm")
                        elif resp.status != 200:
                            body = await resp.text()
                            logging.warning(
                                f"❌ Unexpected Last.fm status {resp.status} on page {page}: {body[:200]}"
                            )
                            break
                        try:
                            data = await resp.json()
                            return data
                        except Exception:
                            body = await resp.text()
                            logging.error(
                                f"❌ Invalid JSON from Last.fm page {page}. Body starts with: {body[:200]}"
                            )
                            break
            except Exception as e:
                logging.error(f"Error fetching page {page}: {e}")
            await asyncio.sleep(2**attempt)

        logging.error(f"All retries failed for page {page}")
        return None

    async def fetch_pages_batch_async(self, session, username, from_ts, to_ts, pages):
        logging.info(f"Starting batch fetch for pages {min(pages)} to {max(pages)}")
        tasks = [
            self.fetch_recent_tracks_page_async(session, username, from_ts, to_ts, p)
            for p in pages
        ]
        results = await asyncio.gather(*tasks)
        logging.info(
            f"Completed batch fetch for pages {min(pages)} to {max(pages)}, got {len(results)} results"
        )
        return results

    async def fetch_all_recent_tracks_async(self, username, from_ts, to_ts):
        async with aiohttp.ClientSession() as session:
            logging.info("Fetching first page to determine total pages")
            first = await self.fetch_recent_tracks_page_async(
                session, username, from_ts, to_ts, 1
            )
            if not first or "recenttracks" not in first:
                logging.error("Failed to fetch initial page from Last.fm")
                return []

            total_pages = int(first["recenttracks"]["@attr"]["totalPages"])
            logging.info(f"Total pages to fetch: {total_pages}")
            all_pages = [first]

            BATCH = 20
            logging.info(f"Will fetch remaining pages in batches of {BATCH}")

            for start in range(2, total_pages + 1, BATCH):
                end = min(start + BATCH, total_pages + 1)
                logging.info(f"Fetching batch of pages {start} to {end-1}")
                batch = await self.fetch_pages_batch_async(
                    session, username, from_ts, to_ts, range(start, end)
                )
                successful_pages = [b for b in batch if b]
                logging.info(f"Got {len(successful_pages)} successful pages in batch")
                all_pages.extend(successful_pages)

            logging.info(f"Fetched a total of {len(all_pages)}/{total_pages} pages")
            return all_pages

    async def fetch_top_albums_async(self, username, year, min_plays=10, min_tracks=3):
        """
        Fetches top albums for a given user and year from Last.fm,
        applying play count and unique track thresholds.
        (Moved from app_old_backup.py and adapted)
        """
        logging.debug(f"Start fetch_top_albums_async(user={username}, year={year})")
        from_ts = int(datetime(year, 1, 1).timestamp())
        to_ts = int(datetime(year, 12, 31, 23, 59, 59).timestamp())
        pages = await self.fetch_all_recent_tracks_async(username, from_ts, to_ts)
        logging.debug(f"Pages fetched: {len(pages)}")
        total_tracks = sum(
            len(p.get("recenttracks", {}).get("track", [])) for p in pages
        )
        logging.debug(f"Total tracks: {total_tracks}")

        albums = defaultdict(
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
                    key = normalize_name(
                        art, alb
                    )  # Using normalize_name from app.utils
                    if "original_artist" not in albums[key]:
                        albums[key]["original_artist"] = art
                        albums[key]["original_album"] = alb
                    albums[key]["play_count"] += 1
                    normalized = normalize_track_name(
                        name
                    )  # Using normalize_track_name from app.utils
                    albums[key]["track_counts"][normalized] += 1
        logging.debug(f"Unique albums: {len(albums)}")

        filtered = {
            k: v
            for k, v in albums.items()
            if v["play_count"] >= min_plays and len(v["track_counts"]) >= min_tracks
        }
        logging.debug(f"Albums after filter: {len(filtered)}")
        return filtered
