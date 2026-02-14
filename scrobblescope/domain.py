import string
import unicodedata
from datetime import datetime, timezone

# Error classification codes for upstream failures.
# Each code maps to a source, retryability flag, and user-facing message.
ERROR_CODES = {
    "lastfm_unavailable": {
        "source": "lastfm",
        "retryable": True,
        "message": "Last.fm is currently unavailable. Please try again in a few minutes.",
    },
    "spotify_unavailable": {
        "source": "spotify",
        "retryable": True,
        "message": "Spotify is currently unavailable. Please try again in a few minutes.",
    },
    "spotify_rate_limited": {
        "source": "spotify",
        "retryable": True,
        "message": "Spotify rate limit reached. Please try again in a few minutes.",
    },
    "lastfm_rate_limited": {
        "source": "lastfm",
        "retryable": True,
        "message": "Last.fm rate limit reached. Please try again in a few minutes.",
    },
    "user_not_found": {
        "source": "lastfm",
        "retryable": False,
        "message": "User '{username}' was not found on Last.fm.",
    },
}


class SpotifyUnavailableError(RuntimeError):
    """Raised when Spotify metadata is required but unavailable for cache misses."""


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


def normalize_track_name(name):
    """Return a simplified version of a track name for matching."""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    for char in [":", "-", "(", ")", "[", "]", "/", "\\", ".", ",", "!", "?", "'"]:
        n = n.replace(char, " ")
    n = " ".join(n.split())
    return n.strip()


def _extract_registered_year(data):
    """Extract the registration year from a Last.fm user.getinfo response."""
    try:
        ts = int(data["user"]["registered"]["unixtime"])
        return datetime.fromtimestamp(ts, tz=timezone.utc).year
    except (KeyError, TypeError, ValueError):
        return None
