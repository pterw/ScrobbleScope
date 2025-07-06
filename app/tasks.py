# app/tasks.py

import asyncio
import logging
import math
import threading
import time
import traceback
from collections import defaultdict
from datetime import datetime

# Import clients and utilities
from app.services.lastfm_client import LastFmClient
from app.services.spotify_client import SpotifyClient

# Import global state
from app.state import (
    UNMATCHED,
    completed_results,
    current_progress,
    progress_lock,
    unmatched_lock,
)
from app.utils import (
    format_seconds,
    get_filter_description,
    normalize_name,
    normalize_track_name,
)


# Async thread runner with improved error handling
# Now accepts the Flask app instance
def run_async_in_thread(app, coro):  # 'app' is passed directly
    result = []
    error = []

    def runner():
        # Push the application context within this new thread using the passed 'app' instance
        with app.app_context():  # Use the 'app' parameter directly
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # Pass the result of the coroutine (if any) to the result list
                coro_result = loop.run_until_complete(coro())
                result.append(coro_result)
            except Exception as e:
                error_traceback = traceback.format_exc()
                logging.error(f"Error in async thread: {e}\\n{error_traceback}")
                error.append(e)
            finally:
                loop.close()

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()

    if error:
        with progress_lock:
            current_progress["progress"] = 100
            current_progress["message"] = f"Error: {str(error[0])}"
            current_progress["error"] = True

        raise error[0]
    # Ensure result is not empty if the coroutine completed successfully but returned None
    if not result:
        logging.error(
            "run_async_in_thread: Coroutine finished without appending to result or raising an error."
        )
        raise RuntimeError(
            "Background task finished without a result or explicit error."
        )
    return result[0]


# Background task interface with improved error handling
# Now accepts the Flask app instance and is a synchronous function (`def`)
def background_task(  # Changed from `async def` to `def`
    app,  # 'app' is passed directly
    username,
    year,
    sort_mode,
    release_scope,
    decade=None,
    release_year=None,
    min_plays=10,
    min_tracks=3,
):
    async def fetch_and_process():
        # Instantiate clients (now within the app context due to run_async_in_thread fix)
        lastfm_client = LastFmClient()
        spotify_client = SpotifyClient()

        try:
            # ── STEP 0: INITIALIZING (0%)
            with progress_lock:
                current_progress["progress"] = 0
                current_progress["message"] = "Initializing..."
                current_progress["error"] = False

            await asyncio.sleep(1)  # Force the front-end to see 0%

            # ── STEP 1: VERIFY USER EXISTS (5%)
            with progress_lock:
                current_progress["progress"] = 5
                current_progress["message"] = "Verifying your profile..."
                current_progress["error"] = False

            user_exists = await lastfm_client.check_user_exists(username)
            if not user_exists:
                with progress_lock:
                    current_progress["progress"] = 100
                    current_progress["message"] = (
                        f"Error: User '{username}' not found on Last.fm"
                    )
                    current_progress["error"] = True
                return []

            # ── STEP 2: FETCH LAST.FM SCR0BBLES (10% → 20%)
            with progress_lock:
                current_progress["progress"] = 10
                current_progress["message"] = "Fetching your data from Last.fm..."
                current_progress["error"] = False

            filtered_albums = await lastfm_client.fetch_top_albums_async(
                username, year, min_plays=min_plays, min_tracks=min_tracks
            )

            if not filtered_albums:
                with progress_lock:
                    current_progress["progress"] = 100
                    current_progress["message"] = (
                        "No albums found for the specified criteria."
                    )
                    current_progress["error"] = False
                return []

            # ── STEP 3: Spoofing processing (20% → 40%)
            with progress_lock:
                current_progress["progress"] = 20
                current_progress["message"] = "Processing your albums..."
            await asyncio.sleep(1)
            with progress_lock:
                current_progress["progress"] = 30
                current_progress["message"] = "Preparing to fetch album data..."
            await asyncio.sleep(1)

            # ── STEP 4: PROCESS ALBUM METADATA (40% → 80%)
            with progress_lock:
                current_progress["progress"] = 40
                current_progress["message"] = "Processing album data from Spotify..."

            results = await process_albums(
                filtered_albums,
                year,
                sort_mode,
                release_scope,
                decade,
                release_year,
                spotify_client,
            )
            with progress_lock:
                current_progress["progress"] = 60
                current_progress["message"] = "Adding album art to your results..."

            # ── STEP 5: Simulate compiling (80%)
            with progress_lock:
                current_progress["progress"] = 80
                current_progress["message"] = "Compiling your top album list..."
            await asyncio.sleep(1)

            # ── STEP 6: Simulate finalizing work (e.g., sorting, formatting) (90% → 100%)
            with progress_lock:
                current_progress["progress"] = 90
                current_progress["message"] = "Finalizing list..."
            await asyncio.sleep(1)

            with progress_lock:
                current_progress["progress"] = 100
                current_progress["message"] = (
                    f"Done! Found {len(results)} albums matching your criteria."
                )
                current_progress["error"] = False

            cache_key = (
                username,
                year,
                sort_mode,
                release_scope,
                decade,
                release_year,
                min_plays,
                min_tracks,
            )
            completed_results[cache_key] = results
            return results

        except Exception as e:
            error_message = str(e)
            if "Too Many Requests" in error_message:
                error_message = (
                    "API rate limit reached. Please try again in a few minutes."
                )
            elif "Not Found" in error_message and "user" in error_message.lower():
                error_message = f"User '{username}' not found on Last.fm"

            with progress_lock:
                current_progress["progress"] = 100
                current_progress["message"] = f"Error: {error_message}"
                current_progress["error"] = True

            logging.exception(f"Error processing request for {username} in {year}")
            return []

    # Pass the app instance to run_async_in_thread
    return run_async_in_thread(app, fetch_and_process)  # Pass 'app' here


# Function for processing data from filtered albums, with filtering + sorting
async def process_albums(
    filtered_albums,
    year,
    sort_mode,
    release_scope,
    decade,
    release_year,
    spotify_client,
):
    logging.info(
        f"Processing {len(filtered_albums)} albums with filters: year={year}, "
        f"release_scope={release_scope}, decade={decade}, release_year={release_year}"
    )

    token = await spotify_client.fetch_spotify_access_token()
    if not token:
        logging.error("Spotify token fetch failed. Cannot process albums.")
        return []

    def matches_release_criteria(release_date):
        if not release_date:
            return False
        release_year_str = (
            release_date.split("-")[0] if "-" in release_date else release_date
        )
        try:
            rel_year = int(release_year_str)
            if release_scope == "same":
                return rel_year == year
            elif release_scope == "previous":
                return rel_year == year - 1
            elif release_scope == "decade" and decade:
                decade_start = int(decade[:3] + "0")
                return decade_start <= rel_year < decade_start + 10
            elif release_scope == "custom" and release_year:
                return rel_year == release_year
            return True
        except ValueError:
            logging.warning(f"Couldn't parse release year from: {release_date}")
            return False

    def get_user_friendly_reason(
        release_date, release_scope, decade=None, release_year=None
    ):
        release_year_str = (
            release_date.split("-")[0] if "-" in release_date else release_date
        )

        try:
            rel_year = int(release_year_str)
            if release_scope == "same":
                return f"Released in {rel_year} instead of {year}"
            elif release_scope == "previous":
                return f"Released in {rel_year} instead of {year-1}"
            elif release_scope == "decade" and decade:
                decade_start = int(decade[:3] + "0")
                decade_end = decade_start + 9
                return f"Released in {rel_year}, outside of {decade_start}-{decade_end}"
            elif release_scope == "custom" and release_year:
                return f"Released in {rel_year} instead of {release_year}"
            return f"Release year {rel_year} does not match filter"
        except ValueError:
            return f"Unknown release year: {release_date}"

    import aiohttp

    async with aiohttp.ClientSession() as session:
        results = []
        for (artist, album), data in filtered_albums.items():

            original_artist = data["original_artist"]
            original_album = data["original_album"]

            album_details = await spotify_client.fetch_spotify_album_release_date(
                session, artist, album, token
            )
            release = album_details.get("release_date", "")
            album_id = album_details.get("id")

            if album_details and matches_release_criteria(release) and album_id:
                track_durations = await spotify_client.fetch_spotify_track_durations(
                    session, album_id, token
                )
                play_time_sec = 0
                for track, count in data["track_counts"].items():
                    dur = track_durations.get(track)
                    if dur:
                        play_time_sec += dur * count
                formatted_time = format_seconds(play_time_sec)

                results.append(
                    {
                        "artist": original_artist,
                        "album": original_album,
                        "play_count": data["play_count"],
                        "play_time": formatted_time,
                        "play_time_seconds": play_time_sec,
                        "different_songs": len(data["track_counts"]),
                        "release_date": release,
                        "album_image": album_details.get("album_image"),
                    }
                )

            elif album_details and not matches_release_criteria(release):
                reason = get_user_friendly_reason(
                    release, release_scope, decade, release_year
                )
                logging.info(
                    f"⏩ Skipped '{original_album}' by '{original_artist}': {reason}"
                )

                with unmatched_lock:
                    key = "|".join(normalize_name(original_artist, original_album))
                    UNMATCHED[key] = {
                        "artist": original_artist,
                        "album": original_album,
                        "reason": reason,
                    }

            elif not album_details:
                logging.warning(
                    f"❌ No metadata found for '{original_album}' by '{original_artist}' (possibly unmatched)"
                )

                with unmatched_lock:
                    key = "|".join(normalize_name(original_artist, original_album))
                    UNMATCHED[key] = {
                        "artist": original_artist,
                        "album": original_album,
                        "reason": "No match found on Spotify",
                    }

        if sort_mode == "playtime":
            results.sort(key=lambda x: x["play_time_seconds"], reverse=True)

            if results:
                max_play_time = results[0]["play_time_seconds"] or 1
                total_play_time = (
                    sum(album["play_time_seconds"] for album in results) or 1
                )

                for album in results:
                    album["proportion_of_max"] = (
                        album["play_time_seconds"] / max_play_time * 100
                    )
                    album["proportion_of_total"] = (
                        album["play_time_seconds"] / total_play_time * 100
                    )
        else:
            results.sort(key=lambda x: x["play_count"], reverse=True)

            if results:
                max_play_count = results[0]["play_count"] or 1
                total_play_count = sum(album["play_count"] for album in results) or 1

                for album in results:
                    album["proportion_of_max"] = (
                        album["play_count"] / max_play_count * 100
                    )
                    album["proportion_of_total"] = (
                        album["play_count"] / total_play_count * 100
                    )

        return results
