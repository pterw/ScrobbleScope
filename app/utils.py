# app/utils.py

import logging
import math
import string
import time
import unicodedata

# Global state for caching (moved from app_old_backup.py)
REQUEST_CACHE = {}
REQUEST_CACHE_TIMEOUT = 3600  # Cache timeout in seconds (1 hour)


# Request caching helper functions (moved from app_old_backup.py)
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
        cleaned_text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("utf-8")
            .lower()
        )
        translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
        cleaned_text = cleaned_text.translate(translator)
        words = cleaned_text.split()
        filtered_words = [word for word in words if word not in safe_to_remove_words]
        return " ".join(filtered_words)

    return clean(artist), clean(album)


def normalize_track_name(name):
    """Return a simplified version of a track name for matching."""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    for char in [":", "-", "(", ")", "[", "]", "/", "\\", ".", ",", "!", "?", "'"]:
        n = n.replace(char, " ")
    n = " ".join(n.split())
    return n.strip()


def format_seconds(seconds):
    """Format seconds into a user-friendly string for sorting by playtime."""
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
