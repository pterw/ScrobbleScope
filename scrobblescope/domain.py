import logging
import string
import unicodedata
import zlib


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


#: How many two-tone washes the stylesheet defines (``--ss-wash-N-a`` and
#: ``--ss-wash-N-b`` in tailwind.src.css, ``.cover-wash-N`` in results.css).
COVER_WASH_COUNT = 8


def cover_wash_index(artist, album):
    """Return which of the ``COVER_WASH_COUNT`` washes an album's cover wears.

    A missing cover is drawn as a muted two-tone wash, and the same album must
    wear the same one on every request and in every process. Python's built-in
    ``hash()`` is salted per process, so the pick is ``zlib.crc32`` of the
    normalised ``artist|album`` key, which is stable everywhere. Normalising
    first means "The Album (Deluxe Edition)" and "the album" share a wash.
    Missing or empty names are valid input: they hash as the empty key.
    """
    key = format_album_key(normalize_name(str(artist or ""), str(album or "")))
    return zlib.crc32(key.encode("utf-8")) % COVER_WASH_COUNT


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


def _matches_release_criteria(
    release_date, release_scope, year, decade=None, release_year=None
):
    """Check whether a release date matches the user's filter criteria.

    Pure function: data-in, bool-out.  Extracted from process_albums so it
    can be unit-tested in isolation without mocking the async I/O pipeline.
    The scope table itself lives in ``release_window``, the rule's one owner;
    this derives from it rather than restating it.
    """
    if release_scope == "all":
        return True
    if not release_date:
        return False

    release_year_str = (
        release_date.split("-")[0] if "-" in release_date else release_date
    )
    try:
        rel_year = int(release_year_str)
    except ValueError:
        logging.warning(f"Couldn't parse release year from: {release_date}")
        return False

    try:
        window = release_window(release_scope, year, decade, release_year)
    except ValueError:
        logging.warning(
            "Couldn't parse release window for scope=%r year=%r decade=%r "
            "release_year=%r",
            release_scope,
            year,
            decade,
            release_year,
        )
        return False

    if window is None:
        return True
    window_start, window_end = window
    return window_start <= rel_year <= window_end


def release_window(release_scope, year, decade=None, release_year=None):
    """Return the inclusive ``(first, last)`` years *release_scope* accepts.

    The one rule behind both consumers: the album filter's
    ``_matches_release_criteria`` and the correction worker's
    ``release_checks._window_end``. Each used to restate the same scope
    table (``same``, ``previous``, ``decade``, ``custom``); this is now the
    single place the machine rule is written (F-B23-5).

    The scope table, for a listening year ``Y``:

    ========== ===============================================
    scope      accepted release years
    ========== ===============================================
    all        every year (returns ``None``)
    same       ``Y``
    previous   ``Y - 1``
    decade     the ten years of ``decade`` (``"1990s"`` is 1990-1999)
    custom     the one year in ``release_year``
    ========== ===============================================

    The prose that describes a scope to a reader is separate wording, not a
    second copy of the rule. The main sites are
    ``_results._get_user_friendly_reason`` (why one album was excluded, with
    corrected and uncorrected phrasing), ``album_flow._get_filter_description``
    (the results header) and, in the browser, ``scopeTagText`` in
    ``index.js``, the filter bar in ``results.html`` and the scope line in
    ``loading.html``; ``docs/design/README.md`` lists the scope values too.
    The list is not exhaustive: a new scope changes this table first, then
    ``grep`` for the scope names (``same``, ``previous``) to find each wording.

    Returns ``None`` when the scope accepts every year: ``"all"``, an
    unrecognized scope, or a ``"decade"``/``"custom"`` scope whose companion
    parameter is falsy (``None``, ``""``, ``0``) -- there is nothing to
    bound the window with, not an error.

    Raises ``ValueError`` when a value needed to compute the window is
    present but cannot be parsed as a year: the base ``year`` for
    ``"same"``/``"previous"``, or a ``"decade"``/``"custom"`` companion
    parameter that is neither missing nor usable.
    """

    def _as_year(value):
        return int(str(value).split("-")[0])

    if release_scope == "same":
        same_year = _as_year(year)
        return (same_year, same_year)
    if release_scope == "previous":
        previous_year = _as_year(year) - 1
        return (previous_year, previous_year)
    if release_scope == "decade" and decade:
        decade_start = _as_year(str(decade)[:3] + "0")
        return (decade_start, decade_start + 9)
    if release_scope == "custom" and release_year:
        custom_year = _as_year(release_year)
        return (custom_year, custom_year)
    return None
