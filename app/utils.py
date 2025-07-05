"""Utility helpers used across the application."""

import string
import unicodedata


def normalize_name(artist: str, album: str) -> tuple[str, str]:
    """Return normalized artist and album names for reliable matching."""

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

    def clean(text: str) -> str:
        cleaned = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("utf-8")
            .lower()
        )
        translator = str.maketrans(string.punctuation, " " * len(string.punctuation))
        cleaned = cleaned.translate(translator)
        words = cleaned.split()
        filtered = [w for w in words if w not in safe_to_remove_words]
        return " ".join(filtered).strip()

    return clean(artist), clean(album)


def normalize_track_name(name: str) -> str:
    """Simplify a track name for fuzzy matching across services."""

    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    translator = str.maketrans(
        {
            c: " "
            for c in [":", "-", "(", ")", "[", "]", "/", "\\", ".", ",", "!", "?", "'"]
        }
    )
    n = n.translate(translator)
    return " ".join(n.split()).strip()


def format_seconds(seconds: int) -> str:
    """Convert a duration in seconds to a human-readable string."""

    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:d}h {minutes:02d}m {sec:02d}s"
    return f"{minutes:d}m {sec:02d}s"
