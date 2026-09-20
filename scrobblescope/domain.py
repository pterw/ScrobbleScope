import string
import unicodedata


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
    album_metadata_words = frozenset(
        {
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
    )

    def clean(text, remove_words: frozenset[str] = frozenset()):
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


def format_album_key(normalized_key):
    """Return the wire form of a ``(artist_norm, album_norm)`` pair.

    The release-check API names an album by this string and the results page
    carries the same value on each row's ``data-album-key``, so the two agree
    by construction rather than by two call sites spelling the join the same
    way.

    The separator is safe because ``normalize_name`` replaces every ASCII
    punctuation character with a space, so neither half can contain a pipe
    and the split back into two names is unambiguous.
    """
    artist_norm, album_norm = normalized_key
    return f"{artist_norm}|{album_norm}"


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
