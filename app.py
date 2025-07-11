# ==============================================================
#  app.py — Refactored Last.fm + Spotify Top Albums with Progress Bar
# ==============================================================

# Load environment variables once
from dotenv import load_dotenv

load_dotenv()

import asyncio
import contextvars
import logging

# Standard library imports
import os
import string

# Enable ANSI escape codes on Windows cmd
import sys
import threading
import time
import traceback
import unicodedata
from collections import defaultdict
from datetime import datetime
from logging.handlers import RotatingFileHandler
from math import ceil

# Third-party imports
import aiohttp
from aiolimiter import AsyncLimiter
from flask import Flask, jsonify, redirect, render_template, request, url_for

sys.stderr.reconfigure(encoding="utf-8")

os.system("")

# Context-bound limiter containers
_lastfm_limiter = contextvars.ContextVar("lastfm_limiter", default=None)
_spotify_limiter = contextvars.ContextVar("spotify_limiter", default=None)

# Global state tracking
UNMATCHED = {}  # Track unmatched artist/album pairs
REQUEST_CACHE = {}  # Cache for API responses
REQUEST_CACHE_TIMEOUT = 3600  # Cache timeout in seconds (1 hour)


# Rate limiters for respective API calling
def get_lastfm_limiter():
    limiter = _lastfm_limiter.get()
    if limiter is None:
        limiter = AsyncLimiter(20, 1)
        _lastfm_limiter.set(limiter)
    return limiter


def get_spotify_limiter():
    limiter = _spotify_limiter.get()
    if limiter is None:
        # Conservative rate limit
        limiter = AsyncLimiter(20, 1)
        _spotify_limiter.set(limiter)
    return limiter


# Async thread runner with improved error handling
def run_async_in_thread(coro):
    result = []
    error = []

    def runner():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result.append(loop.run_until_complete(coro()))
        except Exception as e:
            error_traceback = traceback.format_exc()
            logging.error(f"Error in async thread: {e}\n{error_traceback}")
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
    return result[0]


# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")  # Default to 'dev' if not set


# Make {{ current_year }} available globally in all templates.
@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Setup logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
    handlers=[
        # Main log file with rotation (10MB max size, keep 5 backup files)
        RotatingFileHandler(
            "logs/app_debug.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
            mode="a",
        ),
        logging.StreamHandler(sys.stdout),
    ],
)

# Add an environment variable check for debug mode
debug_mode = os.getenv("DEBUG_MODE", "0") == "1"

# Adjust log levels based on debug mode
if not debug_mode:
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
else:
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.client").setLevel(logging.INFO)

# Log application start
logging.info(f"ScrobbleScope starting up, debug mode: {debug_mode}")

# Progress tracking
current_progress = {"progress": 0, "message": "Initializing...", "error": False}
progress_lock = threading.Lock()
unmatched_lock = threading.Lock()
# Shared cache
completed_results = {}

# API keys from .env file
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def ensure_api_keys():
    """Raise ``RuntimeError`` if required API keys are missing."""
    if not (LASTFM_API_KEY and SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        raise RuntimeError("Missing API keys! Check your .env file.")


spotify_token_cache = {"token": None, "expires_at": 0}


# Request caching helper functions
def get_cache_key(url, params=None):
    """Generate a cache key from URL and params"""
    key = url
    if params:
        key += "_" + "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
    return key


def get_cached_response(url, params=None):
    """Get cached response if available and not expired"""
    key = get_cache_key(url, params)
    if key in REQUEST_CACHE:
        timestamp, data = REQUEST_CACHE[key]
        if time.time() - timestamp < REQUEST_CACHE_TIMEOUT:
            logging.debug(f"Cache hit for {key}")
            return data
    return None


def set_cached_response(url, data, params=None):
    """Cache a response with current timestamp"""
    key = get_cache_key(url, params)
    REQUEST_CACHE[key] = (time.time(), data)


def normalize_name(artist, album):
    """
    Normalizes artist and album names for more accurate matching by cleaning
    unicode, punctuation, and non-essential metadata words.
    """
    # This set contains ONLY words that are metadata and not part of a name.
    # Articles like "a", "an", "the" have been intentionally removed.
    safe_to_remove_words = {
        "deluxe",
        "edition",
        "remastered",
        "version",
        "expanded",
        "anniversary",
        "special",
        "bonus",
        "tracks",
        "ep",
        "remaster",
    }

    def clean(text):
        # 1. Normalize unicode characters and convert to lowercase.
        # The 'unicodedata' module is available from the top of app.py
        cleaned_text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("utf-8")
            .lower()
        )

        # 2. Replace all punctuation with a space.
        translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
        cleaned_text = cleaned_text.translate(translator)

        # 3. Split into words, filter out the safe-to-remove words, and rejoin.
        words = cleaned_text.split()
        filtered_words = [word for word in words if word not in safe_to_remove_words]

        # 4. Join back into a string and remove any leading/trailing whitespace.
        return " ".join(filtered_words)

    return clean(artist), clean(album)


# Track name normalization for cross-service comparisons
def normalize_track_name(name):
    """Return a simplified version of a track name for matching."""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    for char in [":", "-", "(", ")", "[", "]", "/", "\\", ".", ",", "!", "?", "'"]:
        n = n.replace(char, " ")
    n = " ".join(n.split())
    return n.strip()


@app.route("/", methods=["GET"])
def home():
    """Serve the home page"""
    logging.info("Serving index.html as the homepage.")
    return render_template("index.html")


# Function to track loading bar progress
@app.route("/progress")
def progress():
    """Return current progress as JSON"""
    with progress_lock:
        return jsonify(current_progress)


@app.route("/unmatched")
def unmatched():
    with unmatched_lock:
        unmatched_data = dict(
            UNMATCHED
        )  # Create a copy to avoid potential race conditions
        count = len(unmatched_data)
    return jsonify({"count": count, "data": unmatched_data})


@app.route("/reset_progress", methods=["POST"])
def reset_progress():
    """Reset progress state - useful if a task gets stuck"""
    with progress_lock:
        current_progress["progress"] = 0
        current_progress["message"] = "Reset successful"
        current_progress["error"] = False
    return jsonify({"status": "success"})


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with a nice error page"""
    return (
        render_template(
            "error.html",
            error="Page not found",
            message="The page you're looking for doesn't exist.",
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors with a nice error page"""
    return (
        render_template(
            "error.html",
            error="Server Error",
            message="Something went wrong on our end. Please try again later.",
        ),
        500,
    )


# Background task interface with improved error handling


def background_task(
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
        """Fetch and process albums in the background with spoofed progress tracking."""
        try:
            # STEP 0: INITIALIZING (0%)
            with progress_lock:
                current_progress["progress"] = 0
                current_progress["message"] = "Initializing..."
                current_progress["error"] = False

            # Force the front-end to see 0% for one second:
            await asyncio.sleep(1)

            # STEP 1: VERIFY USER EXISTS (5%)
            with progress_lock:
                current_progress["progress"] = 5
                current_progress["message"] = "Verifying your profile..."
                current_progress["error"] = False

            user_exists = await check_user_exists(username)
            if not user_exists:
                with progress_lock:
                    current_progress["progress"] = 100
                    current_progress["message"] = (
                        f"Error: User '{username}' not found on Last.fm"
                    )
                    current_progress["error"] = True
                return []

            # STEP 2: FETCH LAST.FM SCR0BBLES (10% → 20%)
            with progress_lock:
                current_progress["progress"] = 10
                current_progress["message"] = "Fetching your data from Last.fm..."
                current_progress["error"] = False

            filtered_albums = await fetch_top_albums_async(
                username, year, min_plays=min_plays, min_tracks=min_tracks
            )

            if not filtered_albums:
                # No albums matched the basic criteria. Show “no results” but not a technical error.
                with progress_lock:
                    current_progress["progress"] = 100
                    current_progress["message"] = (
                        "No albums found for the specified criteria."
                    )
                    current_progress["error"] = False
                return []

            # STEP 3: Spoofing processing (20% → 40%)
            # Here we just bump the progress.
            with progress_lock:
                current_progress["progress"] = 20
                current_progress["message"] = "Processing your albums..."

            # Small sleep to let front-end pick up 20%
            await asyncio.sleep(1)
            with progress_lock:
                current_progress["progress"] = 30
                current_progress["message"] = "Preparing to fetch album data..."
            await asyncio.sleep(1)
            # Now we’re ready to hand off to process_albums for real Spotify logic—let that occupy 40-60%:

            # STEP 4: PROCESS ALBUM METADATA (40% → 80%)
            with progress_lock:
                current_progress["progress"] = 40
                current_progress["message"] = "Processing album data from Spotify..."

            # This single call does all the cover art + Spotify calls.
            results = await process_albums(
                filtered_albums, year, sort_mode, release_scope, decade, release_year
            )
            # Immediately after it returns spoof “adding album art” and move to 60%:
            with progress_lock:
                current_progress["progress"] = 60
                current_progress["message"] = "Adding album art to your results..."

            # STEP 5: Simulate compiling (80%)
            with progress_lock:
                current_progress["progress"] = 80
                current_progress["message"] = "Compiling your top album list..."

            # Small delay so front-end sees 80% for a moment
            await asyncio.sleep(1)

            # STEP 6: Simulate finalizing work (e.g., sorting, formatting) (90% → 100%)
            with progress_lock:
                current_progress["progress"] = 90
                current_progress["message"] = "Finalizing list..."

            # Small delay so front-end sees 90% for a moment
            await asyncio.sleep(1)

            # Now fully done:
            with progress_lock:
                current_progress["progress"] = 100
                current_progress["message"] = (
                    f"Done! Found {len(results)} albums matching your criteria."
                )
                current_progress["error"] = False

            # Cache the results for results_complete
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
            # Map certain errors to a friendlier string:
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
            return []  # return an empty list on failure

    # actually spawn the coroutine in a background thread
    return run_async_in_thread(fetch_and_process)


# check if a Last.fm user exists
async def check_user_exists(username):
    """Verify if a Last.fm user exists before proceeding with album fetching"""
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }
    # check cache first
    cached_response = get_cached_response(url, params)
    if cached_response:
        return True
    # If not cached, proceed with the request
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    set_cached_response(url, data, params)
                    return True
                elif resp.status == 404:
                    return False
                else:
                    # let the error propagate for other status codes
                    resp.raise_for_status()
                    return False
        except Exception as e:
            logging.error(f"Error checking user existence: {e}")
            # return True to continue processing - we'll get a more specific error later
            return True


# last.fm track fetching with backoff & debug logs
async def fetch_recent_tracks_page_async(
    session, username, from_ts, to_ts, page, retries=3
):
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getrecenttracks",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "from": from_ts,
        "to": to_ts,
        "limit": 200,
        "page": page,
    }

    # check cache first
    cached_response = get_cached_response(url, params)
    if cached_response:
        return cached_response
    # if not cached, proceed with the request
    limiter = get_lastfm_limiter()
    for attempt in range(retries):
        try:
            async with limiter:
                logging.debug(f"Requesting Last.fm page {page}")
                async with session.get(url, params=params) as resp:
                    if resp.status == 429:
                        retry_after = resp.headers.get("Retry-After", "1")
                        logging.warning(
                            f"⚠️ Last.fm rate limit hit. Retry after {retry_after} seconds."
                        )
                        await asyncio.sleep(int(retry_after))
                        continue
                    elif resp.status == 404:
                        # User not found
                        logging.error(f"User {username} not found on Last.fm")
                        raise ValueError(f"User '{username}' not found on Last.fm")
                    elif resp.status != 200:
                        body = await resp.text()
                        logging.warning(
                            f"❌ Unexpected Last.fm status {resp.status} on page {page}: {body[:200]}"
                        )
                        continue
                    try:
                        data = await resp.json()
                        # Cache the response for future use
                        set_cached_response(url, data, params)
                        return data
                    except Exception:
                        body = await resp.text()
                        logging.error(
                            f"❌ Invalid JSON from Last.fm page {page}. Body starts with: {body[:200]}"
                        )
                        continue
        except Exception as e:
            logging.error(f"Error fetching page {page}: {e}")
        await asyncio.sleep(2**attempt)

    logging.error(f"All retries failed for page {page}")
    return None


# batch fetching for last.fm
async def fetch_pages_batch_async(session, username, from_ts, to_ts, pages):
    logging.info(f"Starting batch fetch for pages {min(pages)} to {max(pages)}")
    tasks = [
        fetch_recent_tracks_page_async(session, username, from_ts, to_ts, p)
        for p in pages
    ]
    results = await asyncio.gather(*tasks)
    logging.info(
        f"Completed batch fetch for pages {min(pages)} to {max(pages)}, got {len(results)} results"
    )
    return results


# scrobble fetcher for last.fm, batch fetching
async def fetch_all_recent_tracks_async(username, from_ts, to_ts):
    async with aiohttp.ClientSession() as session:
        logging.info("Fetching first page to determine total pages")
        first = await fetch_recent_tracks_page_async(
            session, username, from_ts, to_ts, 1
        )
        if not first or "recenttracks" not in first:
            logging.error("Failed to fetch initial page from Last.fm")
            return []

        total_pages = int(first["recenttracks"]["@attr"]["totalPages"])
        logging.info(f"Total pages to fetch: {total_pages}")
        all_pages = [first]

        BATCH = 40
        logging.info(f"Will fetch remaining pages in batches of {BATCH}")

        for start in range(2, total_pages + 1, BATCH):
            end = min(start + BATCH, total_pages + 1)
            logging.info(f"Fetching batch of pages {start} to {end-1}")
            batch = await fetch_pages_batch_async(
                session, username, from_ts, to_ts, range(start, end)
            )
            successful_pages = [b for b in batch if b]
            logging.info(f"Got {len(successful_pages)} successful pages in batch")
            all_pages.extend(successful_pages)

        logging.info(f"Fetched a total of {len(all_pages)}/{total_pages} pages")
        return all_pages


# albums with customizable play and track thresholds
async def fetch_top_albums_async(username, year, min_plays=10, min_tracks=3):
    logging.debug(f"Start fetch_top_albums_async(user={username}, year={year})")
    from_ts = int(datetime(year, 1, 1).timestamp())
    to_ts = int(datetime(year, 12, 31, 23, 59, 59).timestamp())
    pages = await fetch_all_recent_tracks_async(username, from_ts, to_ts)
    logging.debug(f"Pages fetched: {len(pages)}")
    total_tracks = sum(len(p.get("recenttracks", {}).get("track", [])) for p in pages)
    logging.debug(f"Total tracks: {total_tracks}")
    albums = defaultdict(lambda: {"play_count": 0, "track_counts": defaultdict(int)})
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
                normalized = normalize_track_name(name)
                albums[key]["track_counts"][normalized] += 1
    logging.debug(f"Unique albums: {len(albums)}")
    filtered = {
        k: v
        for k, v in albums.items()
        if v["play_count"] >= min_plays and len(v["track_counts"]) >= min_tracks
    }
    logging.debug(f"Albums after filter: {len(filtered)}")
    return filtered


# gets spotify api token
async def fetch_spotify_access_token():
    if spotify_token_cache["expires_at"] > time.time():
        return spotify_token_cache["token"]
    url = "https://accounts.spotify.com/api/token"
    auth = aiohttp.BasicAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}
    async with aiohttp.ClientSession() as s:
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


async def search_for_spotify_album_id(session, artist, album, token):
    """
    Searches Spotify for a single album and returns its Spotify ID.
    This function is intended to be run sequentially to avoid rate limits.
    """
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": f"artist:{artist} album:{album}", "type": "album", "limit": 1}
    limiter = get_spotify_limiter()

    for attempt in range(4):
        try:
            async with limiter:
                logging.debug(
                    f"[Attempt {attempt+1}/3] Searching for ID: {album} by {artist}"
                )
                async with session.get(
                    "https://api.spotify.com/v1/search", params=params, headers=headers
                ) as response:
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", "1"))
                        logging.warning(
                            f"⚠️ Spotify Search 429 rate limit hit. Retrying after {retry_after}s."
                        )
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status != 200:
                        body = await response.text()
                        logging.warning(
                            f"❌ Spotify search error {response.status} for {album} by {artist}. Body: {body[:200]}"
                        )
                        break

                    data = await response.json()
                    items = data.get("albums", {}).get("items", [])
                    if items:
                        return items[0].get("id")

                    # if no direct match, try a more relaxed query
                    logging.debug(f"🎯 Retrying with relaxed query: {artist} {album}")
                    relaxed_params = {
                        "q": f"{artist} {album}",
                        "type": "album",
                        "limit": 1,
                    }
                    async with session.get(
                        "https://api.spotify.com/v1/search",
                        params=relaxed_params,
                        headers=headers,
                    ) as fallback_resp:
                        if fallback_resp.status == 200:
                            relaxed_data = await fallback_resp.json()
                            relaxed_items = relaxed_data.get("albums", {}).get(
                                "items", []
                            )
                            if relaxed_items:
                                return relaxed_items[0].get("id")

                    # if still no match after fallback
                    logging.info(f"🔎 No Spotify ID found for {album} by {artist}")
                    return None

        except Exception as e:
            logging.error(
                f"Spotify search exception on attempt {attempt+1} for {album} by {artist}: {e}"
            )

        await asyncio.sleep(2**attempt)  # Exponential backoff

    return None


async def fetch_spotify_album_details_batch(session, album_ids, token):
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
    async with limiter:
        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # response is a dict with an 'albums' key, which is a list.
                    # converts this list into a dict keyed by album ID for easy lookup.
                    return {
                        album["id"]: album for album in data.get("albums", []) if album
                    }
                elif response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    logging.warning(
                        f"⚠️ Batch fetch 429 hit. Retrying after {retry_after}s."
                    )
                    await asyncio.sleep(retry_after)
                    # need to retry the batch call itself
                    return await fetch_spotify_album_details_batch(
                        session, album_ids, token
                    )
                else:
                    logging.error(
                        f"Failed to fetch batch album details. Status: {response.status}, Body: {await response.text()}"
                    )
                    return {}
        except Exception as e:
            logging.error(f"Exception in fetch_spotify_album_details_batch: {e}")
            return {}


def format_seconds(seconds):
    """Format seconds into a user-friendly string for sorting by playtime."""
    import math

    seconds = int(math.ceil(seconds))

    if seconds < 60:
        return f"{seconds} secs"

    minutes, sec_remainder = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} mins, {sec_remainder} secs"

    hours, min_remainder = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} hrs, {min_remainder} mins"

    days, hour_remainder = divmod(hours, 24)
    return f"{days} day{'s' if days != 1 else ''}, {hour_remainder} hrs, {min_remainder} mins"


async def process_albums(
    filtered_albums, year, sort_mode, release_scope, decade=None, release_year=None
):
    """
    Processes albums using a reliable sequential search and efficient batching strategy.
    1. Sequentially searches for all Spotify IDs to avoid rate limits.
    2. Fetches album details in batches of 20.
    3. Processes the results.
    """
    logging.info(
        f"Processing {len(filtered_albums)} albums with sequential search and batching. "
        f"Filters: year={year}, release_scope={release_scope}, decade={decade}, release_year={release_year}"
    )

    token = await fetch_spotify_access_token()
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

    async with aiohttp.ClientSession() as session:
        # step 1: sequentially search for all Spotify album IDs
        logging.info("Starting sequential search for Spotify album IDs.")
        spotify_id_to_original_data = {}

        for key, data in filtered_albums.items():
            artist, album = key
            spotify_id = await search_for_spotify_album_id(
                session, artist, album, token
            )

            if spotify_id:
                spotify_id_to_original_data[spotify_id] = data
            else:
                # This album couldn't be found on Spotify, add to unmatched
                original_artist = data["original_artist"]
                original_album = data["original_album"]
                unmatched_key = "|".join(
                    normalize_name(original_artist, original_album)
                )
                with unmatched_lock:
                    UNMATCHED[unmatched_key] = {
                        "artist": original_artist,
                        "album": original_album,
                        "reason": "No Spotify match",
                    }

        valid_spotify_ids = list(spotify_id_to_original_data.keys())

        # step 2: fetch full album details in batches of 20
        logging.info(
            f"Fetching details for {len(valid_spotify_ids)} valid Spotify IDs."
        )
        all_album_details = {}
        BATCH_SIZE = 20
        for i in range(0, len(valid_spotify_ids), BATCH_SIZE):
            batch_ids = valid_spotify_ids[i : i + BATCH_SIZE]
            logging.info(f"Fetching details for batch of {len(batch_ids)} albums.")
            batch_details = await fetch_spotify_album_details_batch(
                session, batch_ids, token
            )
            all_album_details.update(batch_details)

        # step 3: process the batch results
        results = []
        for spotify_id, album_details in all_album_details.items():
            if not album_details:
                continue

            original_data = spotify_id_to_original_data.get(spotify_id)
            if not original_data:
                continue

            release_date = album_details.get("release_date", "")

            if not matches_release_criteria(release_date):
                artist = original_data["original_artist"]
                album = original_data["original_album"]
                reason = get_user_friendly_reason(
                    release_date, release_scope, decade, release_year
                )
                logging.info(f"⏩ Skipped '{album}' by '{artist}': {reason}")
                unmatched_key = "|".join(normalize_name(artist, album))
                with unmatched_lock:
                    UNMATCHED[unmatched_key] = {
                        "artist": artist,
                        "album": album,
                        "reason": reason,
                    }
                continue

            track_durations = {
                normalize_track_name(t.get("name", "")): t.get("duration_ms", 0) // 1000
                for t in album_details.get("tracks", {}).get("items", [])
            }

            play_time_sec = sum(
                track_durations.get(track, 0) * count
                for track, count in original_data["track_counts"].items()
            )

            results.append(
                {
                    "artist": original_data["original_artist"],
                    "album": original_data["original_album"],
                    "play_count": original_data["play_count"],
                    "play_time": format_seconds(play_time_sec),
                    "play_time_seconds": play_time_sec,
                    "different_songs": len(original_data["track_counts"]),
                    "release_date": release_date,
                    "album_image": (
                        album_details.get("images", [{}])[0].get("url")
                        if album_details.get("images")
                        else None
                    ),
                }
            )

    # --- Final Sorting ---
    if sort_mode == "playtime":
        results.sort(key=lambda x: x["play_time_seconds"], reverse=True)
    else:
        results.sort(key=lambda x: x["play_count"], reverse=True)

    if results:
        if sort_mode == "playtime":
            max_val = results[0]["play_time_seconds"] or 1
            total_val = sum(r["play_time_seconds"] for r in results) or 1
            key = "play_time_seconds"
        else:
            max_val = results[0]["play_count"] or 1
            total_val = sum(r["play_count"] for r in results) or 1
            key = "play_count"

        for r in results:
            r["proportion_of_max"] = (r[key] / max_val) * 100
            r["proportion_of_total"] = (r[key] / total_val) * 100

    return results


# Route to handle form submission and start background processing
@app.route("/results_complete", methods=["POST"])
def results_complete():
    username = request.form.get("username")
    year = int(request.form.get("year"))
    sort_mode = request.form.get("sort_by", "playcount")
    release_scope = request.form.get("release_scope", "same")
    decade = request.form.get("decade")
    release_year = request.form.get("release_year")
    min_plays = request.form.get("min_plays", "10")
    min_tracks = request.form.get("min_tracks", "3")
    if release_year:
        release_year = int(release_year)
    min_plays = int(min_plays)
    min_tracks = int(min_tracks)

    logging.info(f"Processing results for user {username} in year {year} with filters")
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

    with progress_lock:
        error = current_progress.get("error", False)
        if error:
            # If there was an error during processing, show the error page
            return render_template(
                "error.html",
                error="Processing Error",
                message=current_progress.get("message", "An unknown error occurred"),
                details="Please try again or try different parameters.",
            )
        # Check if results are already cached
        if cache_key not in completed_results:
            logging.warning("No cached results found. Showing error page.")
            return render_template(
                "error.html",
                error="Results Not Found",
                message="We couldn't find your results.",
                details="The processing may have timed out or failed. Please try again.",
            )

    results_data = completed_results[cache_key]

    filtered_results = [
        album
        for album in results_data
        if album.get("play_time_seconds", 0) > 0 or sort_mode != "playtime"
    ]

    if not filtered_results:
        # No albums matched the filters
        with unmatched_lock:
            unmatched_count = len(UNMATCHED)

        filter_description = get_filter_description(
            release_scope, decade, release_year, year
        )
        # Render results page with no matches
        return render_template(
            "results.html",
            username=username,
            year=year,
            data=[],
            release_scope=release_scope,
            decade=decade,
            release_year=release_year,
            sort_by=sort_mode,
            min_plays=min_plays,
            min_tracks=min_tracks,
            no_matches=True,
            unmatched_count=unmatched_count,
            filter_description=filter_description,
        )
    # Render results page with cached data
    return render_template(
        "results.html",
        username=username,
        year=year,
        data=filtered_results,
        release_scope=release_scope,
        decade=decade,
        release_year=release_year,
        sort_by=sort_mode,
        min_plays=min_plays,
        min_tracks=min_tracks,
        no_matches=False,
    )


# Helper function to generate filter description
def get_filter_description(release_scope, decade, release_year, listening_year):
    """Generate a readable description of the filter applied"""
    if release_scope == "same":
        return f"albums released in {listening_year}"
    elif release_scope == "previous":
        return f"albums released in {listening_year - 1}"
    elif release_scope == "decade" and decade:
        return f"albums released in the {decade}"
    elif release_scope == "custom" and release_year:
        return f"albums released in {release_year}"
    else:
        return "albums matching your criteria"


# Update the unmatched_view route to organize unmatched albums by reason
@app.route("/unmatched_view", methods=["POST"])
def unmatched_view():
    """Show a dedicated page of unmatched albums that didn't match the filters"""

    # Get form parameters
    username = request.form.get("username")
    year = request.form.get("year")
    release_scope = request.form.get("release_scope", "same")
    decade = request.form.get("decade")
    release_year = request.form.get("release_year")

    # Get threshold parameters
    min_plays = request.form.get("min_plays", "10")
    min_tracks = request.form.get("min_tracks", "3")

    # Get user-friendly filter description
    if release_scope == "same":
        filter_desc = f"same year as listening ({year})"
    elif release_scope == "previous":
        filter_desc = f"previous year ({int(year) - 1})"
    elif release_scope == "decade" and decade:
        filter_desc = f"{decade}"
    elif release_scope == "custom" and release_year:
        filter_desc = f"specific year ({release_year})"
    else:
        filter_desc = "unknown filter"

    with unmatched_lock:
        unmatched_data = dict(UNMATCHED)  # Create a copy to avoid race conditions

    # Group unmatched albums by reason
    reasons = {}
    for key, item in unmatched_data.items():
        reason = item.get("reason", "Unknown reason")
        if reason not in reasons:
            reasons[reason] = []
        reasons[reason].append(item)

    # Count albums by reason
    reason_counts = {reason: len(albums) for reason, albums in reasons.items()}

    return render_template(
        "unmatched.html",
        username=username,
        year=year,
        filter_desc=filter_desc,
        unmatched_data=unmatched_data,
        reasons=reasons,
        reason_counts=reason_counts,
        total_count=len(unmatched_data),
        min_plays=min_plays,
        min_tracks=min_tracks,
    )


# Results loading route to handle form submission and start background task
@app.route("/results_loading", methods=["POST"])
def results_loading():
    """
    Handles form submission, performs the main Last.fm fetch,
    and prepares the session for lazy loading.
    """
    username = request.form.get("username")
    year = request.form.get("year")
    sort_mode = request.form.get("sort_by", "playcount")
    release_scope = request.form.get("release_scope", "same")
    decade = request.form.get("decade") if release_scope == "decade" else None
    release_year = (
        request.form.get("release_year") if release_scope == "custom" else None
    )
    min_plays = request.form.get("min_plays", "10")
    min_tracks = request.form.get("min_tracks", "3")

    # Validate required fields
    if not username or not year:
        logging.warning("Missing username or year in form submission.")
        return render_template("index.html", error="Username and year are required.")

    try:
        year = int(year)
        if release_year:
            release_year = int(release_year)
        min_plays = int(min_plays)
        min_tracks = int(min_tracks)
    except ValueError:
        logging.warning("Invalid year format.")
        return render_template("index.html", error="Year must be a valid number.")

    # Reset progress to 0% and “Initializing…”
    with progress_lock:
        current_progress["progress"] = 0
        current_progress["message"] = "Initializing..."
        current_progress["error"] = False

    # Launch the background thread that actually fetches/processes data
    task_thread = threading.Thread(
        target=background_task,
        args=(
            username,
            year,
            sort_mode,
            release_scope,
            decade,
            release_year,
            min_plays,
            min_tracks,
        ),
        daemon=True,
    )
    task_thread.start()

    # Clear unmatched albums for new request
    with unmatched_lock:
        global UNMATCHED
        UNMATCHED = {}

    # Return the loading page with the current parameters
    return render_template(
        "loading.html",
        username=username,
        year=year,
        sort_by=sort_mode,
        release_scope=release_scope,
        decade=decade,
        release_year=release_year,
        min_plays=min_plays,
        min_tracks=min_tracks,
    )


if __name__ == "__main__":
    import webbrowser

    ensure_api_keys()

    url = "http://127.0.0.1:5000/"
    print(f"🌐 Your app is live at: {url}")
    webbrowser.open(url)

    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
