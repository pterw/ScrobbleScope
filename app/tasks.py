"""Background job helpers for ScrobbleScope."""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, List, Optional

import aiohttp

from .services.lastfm_service import fetch_top_albums_async
from .services.spotify_service import (
    fetch_spotify_access_token,
    fetch_spotify_album_release_date,
    fetch_spotify_track_durations,
)
from .state import (
    UNMATCHED,
    completed_results,
    current_progress,
    progress_lock,
    unmatched_lock,
)
from .utils import format_seconds, normalize_name


def run_async_in_thread(coro: Any) -> Any:
    """Run an async coroutine in a background thread."""
    result: List[Any] = []
    error: List[Exception] = []

    def runner() -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result.append(loop.run_until_complete(coro()))
        except Exception as exc:  # pragma: no cover - unexpected errors
            error.append(exc)
        finally:
            loop.close()

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()

    if error:
        raise error[0]
    return result[0]


def process_albums(
    filtered_albums: Dict[tuple[str, str], Dict[str, Any]],
    year: int,
    sort_mode: str,
    release_scope: str,
    decade: Optional[str] = None,
    release_year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Enrich albums with Spotify metadata and calculate totals.

    Returns the processed album list.
    """

    async def inner() -> List[Dict[str, Any]]:
        token = await fetch_spotify_access_token()
        if not token:
            return []

        def matches_release(release_date: str) -> bool:
            if not release_date:
                return False
            rel_year = int(release_date.split("-")[0])
            if release_scope == "same":
                return rel_year == year
            if release_scope == "previous":
                return rel_year == year - 1
            if release_scope == "decade" and decade:
                decade_start = int(decade[:3] + "0")
                return decade_start <= rel_year < decade_start + 10
            if release_scope == "custom" and release_year:
                return rel_year == release_year
            return True

        async with aiohttp.ClientSession() as session:
            results: List[Dict[str, Any]] = []
            for (artist, album), data in filtered_albums.items():
                details = await fetch_spotify_album_release_date(
                    session, artist, album, token
                )
                release = details.get("release_date", "")
                album_id = details.get("id")
                if details and matches_release(release) and album_id:
                    durations = await fetch_spotify_track_durations(
                        session, album_id, token
                    )
                    play_time_sec = sum(
                        durations.get(t, 0) * c for t, c in data["track_counts"].items()
                    )
                    results.append(
                        {
                            "artist": data["original_artist"],
                            "album": data["original_album"],
                            "play_count": data["play_count"],
                            "play_time": format_seconds(play_time_sec),
                            "play_time_seconds": play_time_sec,
                            "different_songs": len(data["track_counts"]),
                            "release_date": release,
                            "album_image": details.get("album_image"),
                        }
                    )
                elif details and not matches_release(release):
                    reason = (
                        f"Released in {release.split('-')[0]} does not match filter"
                    )
                    with unmatched_lock:
                        key = "|".join(
                            normalize_name(
                                data["original_artist"], data["original_album"]
                            )
                        )
                        UNMATCHED[key] = {
                            "artist": data["original_artist"],
                            "album": data["original_album"],
                            "reason": reason,
                        }
                else:
                    with unmatched_lock:
                        key = "|".join(
                            normalize_name(
                                data["original_artist"], data["original_album"]
                            )
                        )
                        UNMATCHED[key] = {
                            "artist": data["original_artist"],
                            "album": data["original_album"],
                            "reason": "No match found on Spotify",
                        }

            if sort_mode == "playtime":
                results.sort(key=lambda x: x["play_time_seconds"], reverse=True)
            else:
                results.sort(key=lambda x: x["play_count"], reverse=True)
            return results

    return run_async_in_thread(inner)


def background_task(
    username: str,
    year: int,
    sort_mode: str,
    release_scope: str,
    decade: Optional[str] = None,
    release_year: Optional[int] = None,
    min_plays: int = 10,
    min_tracks: int = 3,
) -> List[Dict[str, Any]]:
    """Run the full processing flow in a background thread."""

    async def fetch_and_process() -> List[Dict[str, Any]]:
        with progress_lock:
            current_progress.update(
                {"progress": 5, "message": "Fetching scrobbles...", "error": False}
            )
        albums = await fetch_top_albums_async(username, year, min_plays, min_tracks)
        with progress_lock:
            current_progress.update({"progress": 40, "message": "Processing albums..."})
        results = process_albums(
            albums, year, sort_mode, release_scope, decade, release_year
        )
        with progress_lock:
            current_progress.update({"progress": 100, "message": "Done"})
        key = (
            username,
            year,
            sort_mode,
            release_scope,
            decade,
            release_year,
            min_plays,
            min_tracks,
        )
        completed_results[key] = results
        return results

    return run_async_in_thread(fetch_and_process)
