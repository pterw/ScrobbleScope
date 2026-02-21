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

    Album-level metadata words ('deluxe', 'edition', etc.) are stripped from
    the album string only. The artist string receives only punctuation
    normalization so that proper nouns like 'New Edition' or 'Bonus' are
    not corrupted by the metadata filter.
    """
    # Applied to album only -- these are release-metadata suffixes, not artist names.
    # Applying them to the artist string would corrupt proper nouns (e.g. the R&B
    # group "New Edition" would reduce to "new", and "Special" or "Bonus" to "").
    album_metadata_words = {
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

    def clean(text, remove_words=frozenset()):
        # 1. normalize Unicode characters for consistency (e.g., full-width to half-width).
        #    NFKC is used (not NFKD + ascii-encode) to preserve non-Latin characters.
        cleaned_text = unicodedata.normalize("NFKC", text).lower()

        # 2. replace all ASCII punctuation with spaces.
        translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
        cleaned_text = cleaned_text.translate(translator)

        # 3. split into words, filter out caller-specified words, and rejoin.
        words = cleaned_text.split()
        filtered_words = [word for word in words if word not in remove_words]

        # 4. re-join into a string and remove any excess whitespace.
        return " ".join(filtered_words).strip()

    return clean(artist), clean(album, album_metadata_words)


def normalize_track_name(name):
    """Return a simplified version of a track name for matching.

    Uses NFKC normalization (same as normalize_name) to preserve non-Latin
    characters such as Japanese kana/kanji and Cyrillic script. All ASCII
    punctuation is replaced with spaces for consistent matching with Spotify
    track titles.

    The previous implementation used NFKD + encode('ascii', 'ignore'), which
    silently collapsed every non-Latin track name to an empty string. That broke
    the min_tracks filter and playtime calculation for any foreign-language album.
    """
    n = unicodedata.normalize("NFKC", name).lower()
    translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
    n = n.translate(translator)
    n = " ".join(n.split())
    return n.strip()


def _extract_registered_year(data):
    """Extract the registration year from a Last.fm user.getinfo response."""
    try:
        ts = int(data["user"]["registered"]["unixtime"])
        return datetime.fromtimestamp(ts, tz=timezone.utc).year
    except (KeyError, TypeError, ValueError):
        return None
