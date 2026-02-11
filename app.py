# ==============================================================
#  app.py — Refactored Last.fm + Spotify Top Albums with Progress Bar
# ==============================================================

# Load environment variables once
from dotenv import load_dotenv

load_dotenv()

import asyncio
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
from uuid import uuid4
from weakref import WeakKeyDictionary

# Third-party imports
import aiohttp
from aiolimiter import AsyncLimiter
from flask import Flask, jsonify, redirect, render_template, request, url_for

sys.stderr.reconfigure(encoding="utf-8")

os.system("")

# Global state tracking
REQUEST_CACHE = {}  # Cache for API responses
REQUEST_CACHE_TIMEOUT = 3600  # Cache timeout in seconds (1 hour)
JOB_TTL_SECONDS = 2 * 60 * 60

# API Concurrency Configuration
# These values can be overridden via environment variables for tuning without code changes.
MAX_CONCURRENT_LASTFM = int(os.getenv("MAX_CONCURRENT_LASTFM", "10"))
LASTFM_REQUESTS_PER_SECOND = int(os.getenv("LASTFM_REQUESTS_PER_SECOND", "10"))

SPOTIFY_SEARCH_CONCURRENCY = int(os.getenv("SPOTIFY_SEARCH_CONCURRENCY", "10"))
SPOTIFY_BATCH_CONCURRENCY = int(os.getenv("SPOTIFY_BATCH_CONCURRENCY", "25"))
SPOTIFY_REQUESTS_PER_SECOND = int(os.getenv("SPOTIFY_REQUESTS_PER_SECOND", "10"))
SPOTIFY_SEARCH_RETRIES = int(os.getenv("SPOTIFY_SEARCH_RETRIES", "3"))
SPOTIFY_BATCH_RETRIES = int(os.getenv("SPOTIFY_BATCH_RETRIES", "3"))

# Rate limiters are scoped per running event loop.
# AsyncLimiter instances cannot be safely reused across loops.
_LASTFM_LIMITERS = WeakKeyDictionary()
_SPOTIFY_LIMITERS = WeakKeyDictionary()
_LIMITER_LOCK = threading.Lock()


def _get_loop_limiter(cache, rate, period):
    loop = asyncio.get_running_loop()
    with _LIMITER_LOCK:
        limiter = cache.get(loop)
        if limiter is None:
            limiter = AsyncLimiter(rate, period)
            cache[loop] = limiter
    return limiter


# Rate limiters for respective API calling
def get_lastfm_limiter():
    """
    Last.fm API Rate Limiter
    Official limit: 5 requests/second per IP (averaged over 5 minutes)
    Runtime value comes from LASTFM_REQUESTS_PER_SECOND.
    Source: https://www.last.fm/api/tos
    """
    return _get_loop_limiter(_LASTFM_LIMITERS, LASTFM_REQUESTS_PER_SECOND, 1)


def get_spotify_limiter():
    """
    Spotify API Rate Limiter
    Official limit: Undisclosed, based on 30-second rolling window
    Runtime value comes from SPOTIFY_REQUESTS_PER_SECOND.
    Source: https://developer.spotify.com/documentation/web-api/concepts/rate-limits
    """
    return _get_loop_limiter(_SPOTIFY_LIMITERS, SPOTIFY_REQUESTS_PER_SECOND, 1)


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
        # Main log file with rotation (1MB max size, keep 5 backup files)
        RotatingFileHandler(
            "logs/app_debug.log",
            maxBytes=1 * 1024 * 1024,  # 1MB Max Size
            backupCount=5,
            encoding="utf-8",
            mode="a",
        ),
        logging.StreamHandler(sys.stdout),
    ],
)

# Add start-up banner on application start
logging.info("=" * 80)
logging.info(f"ScrobbleScope Application Starting at {datetime.now().isoformat()}")
logging.info("=" * 80)

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

# Per-job state tracking
JOBS = {}
jobs_lock = threading.Lock()


def _initial_progress():
    return {
        "progress": 0,
        "message": "Initializing...",
        "error": False,
        "stats": {},
    }


def cleanup_expired_jobs():
    cutoff = time.time() - JOB_TTL_SECONDS
    with jobs_lock:
        expired_job_ids = [
            job_id
            for job_id, payload in JOBS.items()
            if payload.get("updated_at", payload.get("created_at", 0)) < cutoff
        ]
        for job_id in expired_job_ids:
            JOBS.pop(job_id, None)

    if expired_job_ids:
        logging.info(f"Cleaned up {len(expired_job_ids)} expired jobs")


def create_job(params):
    now = time.time()
    job_id = uuid4().hex
    with jobs_lock:
        JOBS[job_id] = {
            "created_at": now,
            "updated_at": now,
            "progress": _initial_progress(),
            "results": None,
            "unmatched": {},
            "params": params,
        }
    return job_id


def set_job_progress(
    job_id, progress=None, message=None, error=None, reset_stats=False
):
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        if reset_stats:
            job["progress"]["stats"] = {}
        if progress is not None:
            job["progress"]["progress"] = progress
        if message is not None:
            job["progress"]["message"] = message
        if error is not None:
            job["progress"]["error"] = error
        job["updated_at"] = time.time()
    return True


def set_job_stat(job_id, key, value):
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["progress"].setdefault("stats", {})[key] = value
        job["updated_at"] = time.time()
    return True


def set_job_results(job_id, results):
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["results"] = results
        job["updated_at"] = time.time()
    return True


def add_job_unmatched(job_id, unmatched_key, unmatched_payload):
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["unmatched"][unmatched_key] = unmatched_payload
        job["updated_at"] = time.time()
    return True


def reset_job_state(job_id):
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return False
        job["progress"] = _initial_progress()
        job["results"] = None
        job["unmatched"] = {}
        job["updated_at"] = time.time()
    return True


def get_job_progress(job_id):
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None
        job["updated_at"] = time.time()
        progress = dict(job["progress"])
        progress["stats"] = dict(progress.get("stats", {}))
        return progress


def get_job_unmatched(job_id):
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None
        job["updated_at"] = time.time()
        return dict(job["unmatched"])


def get_job_context(job_id):
    with jobs_lock:
        job = JOBS.get(job_id)
        if not job:
            return None
        job["updated_at"] = time.time()

        results = job.get("results")
        if isinstance(results, list):
            results = list(results)

        progress = dict(job["progress"])
        progress["stats"] = dict(progress.get("stats", {}))
        return {
            "progress": progress,
            "results": results,
            "unmatched": dict(job.get("unmatched", {})),
            "params": dict(job.get("params", {})),
        }


# API keys from .env file
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def ensure_api_keys():
    """Raise ``RuntimeError`` if required API keys are missing."""
    if not (LASTFM_API_KEY and SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        raise RuntimeError("Missing API keys! Check your .env file.")


spotify_token_cache = {"token": None, "expires_at": 0}


def create_optimized_session():
    """
    Create aiohttp session with production-ready connection pooling.

    This prevents:
    - Socket exhaustion from too many connections
    - DNS lookup overhead via caching
    - Timeout-related hangs

    Connection limits:
    - Total connections: 40 (across all hosts)
    - Per-host connections: 25 (for Spotify/Last.fm)
    - DNS cache: 5 minutes
    - Timeouts: 30s total, 10s connect, 20s read
    """
    connector = aiohttp.TCPConnector(
        limit=40,  # Max total connections across all hosts
        limit_per_host=25,  # Max connections per host (Spotify/Last.fm)
        ttl_dns_cache=300,  # Cache DNS for 5 minutes
        enable_cleanup_closed=True,
        force_close=False,  # Allow connection reuse
    )

    timeout = aiohttp.ClientTimeout(
        total=30,  # Total timeout for request
        connect=10,  # Connection establishment timeout
        sock_read=20,  # Socket read timeout
    )

    return aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        raise_for_status=False,  # Manual status handling
    )


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


def cleanup_expired_cache():
    """
    Remove expired entries from REQUEST_CACHE to prevent memory leaks.

    Called at the start of each background task to maintain bounded memory.
    This is critical for production deployment on Fly.io to avoid OOM errors.
    """
    current_time = time.time()
    expired_keys = [
        key
        for key, (timestamp, _) in REQUEST_CACHE.items()
        if current_time - timestamp >= REQUEST_CACHE_TIMEOUT
    ]

    for key in expired_keys:
        REQUEST_CACHE.pop(key, None)

    if expired_keys:
        logging.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")

    # Log current cache size for monitoring
    cache_size_mb = sum(len(str(v)) for v in REQUEST_CACHE.values()) / (1024 * 1024)
    logging.debug(
        f"📊 Cache status: {len(REQUEST_CACHE)} entries (~{cache_size_mb:.2f} MB)"
    )


def normalize_name(artist, album):
    """
    Normalizes artist and album names for more accurate matching by cleaning
    punctuation and non-essential metadata words while preserving Unicode characters.
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
        # 1. normalize Unicode characters for consistency (e.g., full-width to half-width forms).
        #    as of 2025/07/09 the ASCII encoding has been REMOVED to preserve non-Latin characters.
        cleaned_text = unicodedata.normalize("NFKC", text).lower()

        # 2. replace all punctuation with a space.
        translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
        cleaned_text = cleaned_text.translate(translator)

        # 3. split into words, filter out the safe-to-remove words, and rejoin.
        words = cleaned_text.split()
        filtered_words = [word for word in words if word not in safe_to_remove_words]

        # 4. re-join into a string and remove any excess whitespace.
        return " ".join(filtered_words).strip()

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


@app.route("/validate_user", methods=["GET"])
def validate_user():
    """Validate a Last.fm username for client-side blur checks."""
    username = (request.args.get("username") or "").strip()
    if not username:
        return jsonify({"valid": False, "message": "Username is required."}), 400
    if len(username) > 64:
        return jsonify({"valid": False, "message": "Username is too long."}), 400

    async def _check():
        return await check_user_exists(username)

    try:
        exists = run_async_in_thread(_check)
    except Exception:
        logging.exception("Username validation failed")
        return (
            jsonify(
                {
                    "valid": False,
                    "message": "Validation service unavailable. Try again.",
                }
            ),
            503,
        )

    if exists:
        return jsonify({"valid": True, "message": "Username found."})
    return jsonify({"valid": False, "message": "Username not found on Last.fm."})


@app.route("/progress")
def progress():
    """Return current progress for a specific job ID."""
    job_id = request.args.get("job_id")
    if not job_id:
        return (
            jsonify(
                {
                    "progress": 100,
                    "message": "Missing job identifier.",
                    "error": True,
                    "stats": {},
                }
            ),
            400,
        )

    progress_payload = get_job_progress(job_id)
    if progress_payload is None:
        return (
            jsonify(
                {
                    "progress": 100,
                    "message": "Job not found or expired.",
                    "error": True,
                    "stats": {},
                }
            ),
            404,
        )

    return jsonify(progress_payload)


@app.route("/unmatched")
def unmatched():
    """Return unmatched albums for a specific job ID."""
    job_id = request.args.get("job_id")
    if not job_id:
        return (
            jsonify({"count": 0, "data": {}, "error": "Missing job identifier."}),
            400,
        )

    unmatched_data = get_job_unmatched(job_id)
    if unmatched_data is None:
        return jsonify({"count": 0, "data": {}, "error": "Job not found."}), 404

    return jsonify({"count": len(unmatched_data), "data": unmatched_data})


@app.route("/reset_progress", methods=["POST"])
def reset_progress():
    """Reset progress state for a specific job ID."""
    job_id = request.form.get("job_id")
    if not job_id:
        return jsonify({"status": "error", "message": "Missing job identifier."}), 400

    if not reset_job_state(job_id):
        return jsonify({"status": "error", "message": "Job not found."}), 404

    set_job_progress(job_id, message="Reset successful", error=False)
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
    job_id,
    username,
    year,
    sort_mode,
    release_scope,
    decade=None,
    release_year=None,
    min_plays=10,
    min_tracks=3,
    limit_results="all",
):
    async def fetch_and_process():
        """Fetch and process albums in the background for a single job."""
        try:
            overall_start_time = time.time()
            cleanup_expired_cache()
            cleanup_expired_jobs()

            set_job_progress(
                job_id,
                progress=0,
                message="Initializing...",
                error=False,
                reset_stats=True,
            )

            await asyncio.sleep(0.5)

            step_start_time = time.time()
            set_job_progress(
                job_id,
                progress=5,
                message="Fetching your data from Last.fm...",
                error=False,
            )

            filtered_albums = await fetch_top_albums_async(
                job_id, username, year, min_plays=min_plays, min_tracks=min_tracks
            )
            step_elapsed = time.time() - step_start_time
            logging.info(f"Time elapsed (Last.fm data fetch): {step_elapsed:.1f}s")

            if not filtered_albums:
                set_job_results(job_id, [])
                set_job_progress(
                    job_id,
                    progress=100,
                    message="No albums found for the specified criteria.",
                    error=False,
                )
                return []

            set_job_progress(job_id, progress=20, message="Processing your albums...")

            await asyncio.sleep(0.5)
            set_job_progress(
                job_id, progress=30, message="Preparing to fetch album data..."
            )
            await asyncio.sleep(0.5)

            step_start_time = time.time()
            set_job_progress(
                job_id,
                progress=40,
                message="Processing album data from Spotify...",
            )

            results = await process_albums(
                job_id,
                filtered_albums,
                year,
                sort_mode,
                release_scope,
                decade,
                release_year,
            )
            step_elapsed = time.time() - step_start_time
            logging.info(
                f"Time elapsed (Spotify album processing): {step_elapsed:.1f}s"
            )

            set_job_progress(
                job_id, progress=60, message="Adding album art to your results..."
            )

            set_job_progress(
                job_id, progress=80, message="Compiling your top album list..."
            )

            await asyncio.sleep(0.5)

            set_job_progress(job_id, progress=90, message="Finalizing list...")

            await asyncio.sleep(0.5)

            if limit_results != "all":
                try:
                    limit = int(limit_results)
                    if len(results) > limit:
                        results = results[:limit]
                        logging.info(f"Limited results to top {limit} albums")
                except ValueError:
                    logging.warning(
                        f"Invalid limit_results value: {limit_results}, showing all results"
                    )

            overall_elapsed = time.time() - overall_start_time
            logging.info(f"Total time elapsed: {overall_elapsed:.1f}s")

            set_job_results(job_id, results)
            set_job_progress(
                job_id,
                progress=100,
                message=f"Done! Found {len(results)} albums matching your criteria.",
                error=False,
            )
            return results

        except Exception as exc:
            error_message = str(exc)
            if "Too Many Requests" in error_message:
                error_message = (
                    "API rate limit reached. Please try again in a few minutes."
                )
            elif (
                "not found" in error_message.lower() and "user" in error_message.lower()
            ):
                error_message = f"User '{username}' not found on Last.fm"

            set_job_results(job_id, [])
            set_job_progress(
                job_id, progress=100, message=f"Error: {error_message}", error=True
            )

            logging.exception(f"Error processing request for {username} in {year}")
            return []

    return run_async_in_thread(fetch_and_process)


# check if a Last.fm user exists
async def check_user_exists(username):
    """Verify if a Last.fm user exists before proceeding with album fetching"""
    url = "https://ws.audioscrobbler.com/2.0/"
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
    async with create_optimized_session() as session:
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
    session, username, from_ts, to_ts, page, retries=3, semaphore=None
):
    url = "https://ws.audioscrobbler.com/2.0/"
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

    limiter = get_lastfm_limiter()

    async def fetch_once():
        async with limiter:
            logging.debug(f"Requesting Last.fm page {page}")
            async with session.get(url, params=params) as resp:
                if resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", "1"))
                    logging.warning(
                        f"⚠️ LAST.FM RATE LIMIT (429) on page {page}! "
                        f"Retry after {retry_after}s. "
                        f"Current limiter: {LASTFM_REQUESTS_PER_SECOND} req/s, consider reducing concurrency."
                    )
                    return None, retry_after
                if resp.status == 404:
                    # User not found
                    logging.error(f"User {username} not found on Last.fm")
                    raise ValueError(f"User '{username}' not found on Last.fm")
                if resp.status != 200:
                    body = await resp.text()
                    logging.warning(
                        f"❌ Unexpected Last.fm status {resp.status} on page {page}: {body[:200]}"
                    )
                    return None, None
                try:
                    data = await resp.json()
                    # Cache the response for future use
                    set_cached_response(url, data, params)
                    return data, None
                except Exception:
                    body = await resp.text()
                    logging.error(
                        f"❌ Invalid JSON from Last.fm page {page}. Body starts with: {body[:200]}"
                    )
                    return None, None

    for attempt in range(retries):
        try:
            if semaphore is None:
                data, retry_after = await fetch_once()
            else:
                async with semaphore:
                    data, retry_after = await fetch_once()

            if data is not None:
                return data
            if retry_after is not None:
                await asyncio.sleep(retry_after)
                continue
        except ValueError:
            raise
        except Exception as e:
            logging.error(f"Error fetching page {page}: {e}")

        # Transient 5xx errors from Last.fm are common; short backoff recovers
        # faster without blocking concurrency slots.
        await asyncio.sleep(min(0.25 * (attempt + 1), 1.0))

    logging.error(f"All retries failed for page {page}")
    return None


# batch fetching for last.fm
async def fetch_pages_batch_async(session, username, from_ts, to_ts, pages):
    """
    Fetch Last.fm pages with controlled concurrency to respect rate limits.
    Semaphore (MAX_CONCURRENT_LASTFM) caps in-flight requests; rate limiter
    (_LASTFM_LIMITER) caps throughput. Called once with all pages rather than
    in sequential batches to avoid idle gaps.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LASTFM)

    async def fetch_with_semaphore(page):
        return await fetch_recent_tracks_page_async(
            session, username, from_ts, to_ts, page, semaphore=semaphore
        )

    tasks = [fetch_with_semaphore(p) for p in pages]
    results = await asyncio.gather(*tasks)

    successful = sum(1 for r in results if r is not None)
    logging.debug(f"Batch {min(pages)}-{max(pages)}: {successful}/{len(results)} pages")
    return results


# scrobble fetcher for last.fm, batch fetching
async def fetch_all_recent_tracks_async(username, from_ts, to_ts):
    fetch_start_time = time.time()
    async with create_optimized_session() as session:
        first = await fetch_recent_tracks_page_async(
            session, username, from_ts, to_ts, 1
        )
        if not first or "recenttracks" not in first:
            logging.error("Failed to fetch initial page from Last.fm")
            return []

        total_pages = int(first["recenttracks"]["@attr"]["totalPages"])
        logging.info(f"Last.fm: Fetching {total_pages} pages of scrobbles")
        all_pages = [first]

        # Launch all remaining page fetches at once — the semaphore
        # (MAX_CONCURRENT_LASTFM) and rate limiter (_LASTFM_LIMITER) control
        # throughput. Previous sequential batching of 50 created idle gaps
        # at batch boundaries when stragglers needed retries.
        if total_pages > 1:
            results = await fetch_pages_batch_async(
                session, username, from_ts, to_ts, range(2, total_pages + 1)
            )
            all_pages.extend([r for r in results if r])

        fetch_elapsed = time.time() - fetch_start_time
        logging.info(
            f"⏱️  Time elapsed (fetching {total_pages} Last.fm pages): {fetch_elapsed:.1f}s"
        )

        logging.info(f"Last.fm: Fetched {len(all_pages)}/{total_pages} pages")
        return all_pages


# albums with customizable play and track thresholds
async def fetch_top_albums_async(job_id, username, year, min_plays=10, min_tracks=3):
    logging.debug(f"Start fetch_top_albums_async(user={username}, year={year})")
    from_ts = int(datetime(year, 1, 1).timestamp())
    to_ts = int(datetime(year, 12, 31, 23, 59, 59).timestamp())
    pages = await fetch_all_recent_tracks_async(username, from_ts, to_ts)
    logging.debug(f"Pages fetched: {len(pages)}")
    total_tracks = sum(len(p.get("recenttracks", {}).get("track", [])) for p in pages)
    logging.debug(f"Total tracks: {total_tracks}")

    set_job_stat(job_id, "total_scrobbles", total_tracks)
    set_job_stat(job_id, "pages_fetched", len(pages))

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

    set_job_stat(job_id, "unique_albums", len(albums))
    set_job_stat(job_id, "albums_passing_filter", len(filtered))

    return filtered


# gets spotify api token
async def fetch_spotify_access_token():
    if spotify_token_cache["expires_at"] > time.time():
        return spotify_token_cache["token"]
    url = "https://accounts.spotify.com/api/token"
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

    for attempt in range(SPOTIFY_SEARCH_RETRIES):
        try:
            if semaphore is None:
                spotify_id, retry_after, done = await search_once()
            else:
                async with semaphore:
                    spotify_id, retry_after, done = await search_once()

            if done:
                return spotify_id
            if retry_after is not None:
                jitter = (abs(hash((artist, album, attempt))) % 200) / 1000.0
                await asyncio.sleep(retry_after + jitter)
                continue
        except Exception as e:
            logging.error(f"Spotify search error for {album} by {artist}: {e}")

        await asyncio.sleep(1)

    return None


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

    for attempt in range(retries):
        try:
            if semaphore is None:
                details, retry_after, done = await fetch_once()
            else:
                async with semaphore:
                    details, retry_after, done = await fetch_once()

            if done:
                return details
            if retry_after is not None:
                jitter = (abs(hash((tuple(album_ids), attempt))) % 200) / 1000.0
                await asyncio.sleep(retry_after + jitter)
                continue
        except Exception as e:
            logging.error(f"Exception in fetch_spotify_album_details_batch: {e}")

        await asyncio.sleep(2**attempt)

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
    job_id,
    filtered_albums,
    year,
    sort_mode,
    release_scope,
    decade=None,
    release_year=None,
):
    """Process albums using parallel Spotify search + batched detail requests."""
    logging.info(
        f"Processing {len(filtered_albums)} albums. "
        f"Filters: year={year}, release_scope={release_scope}, decade={decade}, release_year={release_year}"
    )

    token = await fetch_spotify_access_token()
    if not token:
        logging.error("Spotify token fetch failed. Cannot process albums.")
        return []

    def matches_release_criteria(release_date):
        if release_scope == "all":
            return True
        if not release_date:
            return False

        release_year_str = (
            release_date.split("-")[0] if "-" in release_date else release_date
        )
        try:
            rel_year = int(release_year_str)
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
        except ValueError:
            logging.warning(f"Couldn't parse release year from: {release_date}")
            return False

    def get_user_friendly_reason(release_date):
        if release_scope == "all":
            return "Should not be filtered (All Years selected)"

        release_year_str = (
            release_date.split("-")[0] if "-" in release_date else release_date
        )
        try:
            rel_year = int(release_year_str)
            if release_scope == "same":
                return f"Released in {rel_year} instead of {year}"
            if release_scope == "previous":
                return f"Released in {rel_year} instead of {year - 1}"
            if release_scope == "decade" and decade:
                decade_start = int(decade[:3] + "0")
                decade_end = decade_start + 9
                return f"Released in {rel_year}, outside of {decade_start}-{decade_end}"
            if release_scope == "custom" and release_year:
                return f"Released in {rel_year} instead of {release_year}"
            return f"Release year {rel_year} does not match filter"
        except ValueError:
            return f"Unknown release year: {release_date}"

    async with create_optimized_session() as session:
        search_semaphore = asyncio.Semaphore(SPOTIFY_SEARCH_CONCURRENCY)

        logging.info(
            f"Starting parallel search for {len(filtered_albums)} Spotify albums "
            f"(max {SPOTIFY_SEARCH_CONCURRENCY} concurrent, {SPOTIFY_REQUESTS_PER_SECOND} req/s limit)"
        )
        search_start_time = time.time()

        async def search_with_semaphore(key, data):
            artist, album = key
            spotify_id = await search_for_spotify_album_id(
                session, artist, album, token, semaphore=search_semaphore
            )
            return key, spotify_id, data

        search_tasks = [
            search_with_semaphore(key, data) for key, data in filtered_albums.items()
        ]
        search_results = await asyncio.gather(*search_tasks)

        spotify_id_to_original_data = {}
        for key, spotify_id, data in search_results:
            if spotify_id:
                spotify_id_to_original_data[spotify_id] = data
            else:
                original_artist = data["original_artist"]
                original_album = data["original_album"]
                unmatched_key = "|".join(
                    normalize_name(original_artist, original_album)
                )
                add_job_unmatched(
                    job_id,
                    unmatched_key,
                    {
                        "artist": original_artist,
                        "album": original_album,
                        "reason": "No Spotify match",
                    },
                )

        valid_spotify_ids = list(spotify_id_to_original_data.keys())
        search_duration = time.time() - search_start_time
        logging.info(
            f"Spotify search completed in {search_duration:.1f}s: "
            f"{len(valid_spotify_ids)}/{len(filtered_albums)} albums found on Spotify"
        )

        set_job_stat(job_id, "spotify_matched", len(valid_spotify_ids))
        set_job_stat(
            job_id,
            "spotify_unmatched",
            len(filtered_albums) - len(valid_spotify_ids),
        )

        batch_size = 20
        num_batches = ceil(len(valid_spotify_ids) / batch_size)
        logging.info(
            f"Fetching album details for {len(valid_spotify_ids)} albums "
            f"in {num_batches} parallel batches (batch size: {batch_size})"
        )
        batch_start_time = time.time()

        batch_groups = [
            valid_spotify_ids[i : i + batch_size]
            for i in range(0, len(valid_spotify_ids), batch_size)
        ]

        batch_semaphore = asyncio.Semaphore(SPOTIFY_BATCH_CONCURRENCY)

        async def fetch_batch_with_semaphore(batch_ids):
            return await fetch_spotify_album_details_batch(
                session, batch_ids, token, semaphore=batch_semaphore
            )

        batch_tasks = [fetch_batch_with_semaphore(batch) for batch in batch_groups]
        batch_results = await asyncio.gather(*batch_tasks)

        all_album_details = {}
        for batch_result in batch_results:
            all_album_details.update(batch_result)

        batch_duration = time.time() - batch_start_time
        logging.info(
            f"Album details fetch completed in {batch_duration:.1f}s: "
            f"Got details for {len(all_album_details)} albums"
        )

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
                reason = get_user_friendly_reason(release_date)
                logging.debug(f"Skipped '{album}' by '{artist}': {reason}")
                unmatched_key = "|".join(normalize_name(artist, album))
                add_job_unmatched(
                    job_id,
                    unmatched_key,
                    {"artist": artist, "album": album, "reason": reason},
                )
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
                    "spotify_id": spotify_id,
                }
            )

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

        for result in results:
            result["proportion_of_max"] = (result[key] / max_val) * 100
            result["proportion_of_total"] = (result[key] / total_val) * 100

    return results


# Route to handle form submission and start background processing
@app.route("/results_complete", methods=["POST"])
def results_complete():
    job_id = request.form.get("job_id")
    if not job_id:
        return render_template(
            "error.html",
            error="Missing Job Identifier",
            message="We could not identify your in-progress request.",
            details="Please start a new search.",
        )

    job_context = get_job_context(job_id)
    if not job_context:
        logging.warning(f"Job context not found for {job_id}")
        return render_template(
            "error.html",
            error="Results Not Found",
            message="We couldn't find your results.",
            details="The processing may have expired. Please try again.",
        )

    progress_payload = job_context["progress"]
    if progress_payload.get("error"):
        return render_template(
            "error.html",
            error="Processing Error",
            message=progress_payload.get("message", "An unknown error occurred"),
            details="Please try again or use different parameters.",
        )

    params = job_context.get("params", {})
    username = params.get("username") or request.form.get("username")
    year = params.get("year")
    if year is None:
        year = int(request.form.get("year", datetime.now().year))

    sort_mode = params.get("sort_mode") or request.form.get("sort_by", "playcount")
    release_scope = params.get("release_scope") or request.form.get(
        "release_scope", "same"
    )
    decade = params.get("decade")
    release_year = params.get("release_year")
    min_plays = params.get("min_plays", 10)
    min_tracks = params.get("min_tracks", 3)

    results_data = job_context.get("results")
    if results_data is None:
        return render_template(
            "error.html",
            error="Results Still Processing",
            message="Your results are not ready yet.",
            details="Please wait on the loading page and try again.",
        )

    filtered_results = [
        album
        for album in results_data
        if album.get("play_time_seconds", 0) > 0 or sort_mode != "playtime"
    ]

    if not filtered_results:
        unmatched_count = len(job_context.get("unmatched", {}))
        filter_description = get_filter_description(
            release_scope, decade, release_year, year
        )
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
            job_id=job_id,
        )

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
        job_id=job_id,
    )


# Helper function to generate filter description
def get_filter_description(release_scope, decade, release_year, listening_year):
    """Generate a readable description of the filter applied"""
    if release_scope == "all":
        return "all albums (no release year filter)"
    elif release_scope == "same":
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
    """Show a dedicated page of unmatched albums that didn't match the filters."""
    job_id = request.form.get("job_id")
    if not job_id:
        return render_template(
            "error.html",
            error="Missing Job Identifier",
            message="We could not find unmatched albums without a valid job ID.",
            details="Please return to your results page and try again.",
        )

    job_context = get_job_context(job_id)
    if not job_context:
        return render_template(
            "error.html",
            error="Job Not Found",
            message="Your unmatched album data has expired.",
            details="Please run a new search.",
        )

    params = job_context.get("params", {})
    username = params.get("username")
    year = params.get("year")
    release_scope = params.get("release_scope", "same")
    decade = params.get("decade")
    release_year = params.get("release_year")
    min_plays = params.get("min_plays", 10)
    min_tracks = params.get("min_tracks", 3)

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

    unmatched_data = dict(job_context.get("unmatched", {}))

    reasons = {}
    for _, item in unmatched_data.items():
        reason = item.get("reason", "Unknown reason")
        if reason not in reasons:
            reasons[reason] = []
        reasons[reason].append(item)

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
    limit_results = request.form.get("limit_results", "all")

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

    cleanup_expired_jobs()

    params = {
        "username": username,
        "year": year,
        "sort_mode": sort_mode,
        "release_scope": release_scope,
        "decade": decade,
        "release_year": release_year,
        "min_plays": min_plays,
        "min_tracks": min_tracks,
        "limit_results": limit_results,
    }

    job_id = create_job(params)

    task_thread = threading.Thread(
        target=background_task,
        args=(
            job_id,
            username,
            year,
            sort_mode,
            release_scope,
            decade,
            release_year,
            min_plays,
            min_tracks,
            limit_results,
        ),
        daemon=True,
    )
    task_thread.start()

    return render_template(
        "loading.html",
        job_id=job_id,
        username=username,
        year=year,
        sort_by=sort_mode,
        release_scope=release_scope,
        decade=decade,
        release_year=release_year,
        min_plays=min_plays,
        min_tracks=min_tracks,
        limit_results=limit_results,
    )


if __name__ == "__main__":
    import webbrowser

    ensure_api_keys()

    url = "http://127.0.0.1:5000/"
    print(f"Your app is live at: {url}")
    webbrowser.open(url)

    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
