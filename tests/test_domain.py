from scrobblescope.domain import (
    _extract_registered_year,
    normalize_name,
    normalize_track_name,
)


def test_normalize_name_simple():
    """
    GIVEN an artist and album with common suffixes and punctuation
    WHEN normalize_name is called
    THEN check that the names are correctly stripped and lowercased.
    """
    artist, album = normalize_name("The Beatles.", "Let It Be (Deluxe Edition)")
    assert artist == "the beatles"
    assert album == "let it be"


def test_normalize_name_remastered_suffix():
    """
    GIVEN an album name containing 'Remastered'
    WHEN normalize_name is called
    THEN 'remastered' should be stripped from the result.
    """
    artist, album = normalize_name("Pink Floyd", "Wish You Were Here (Remastered)")
    assert "remastered" not in album
    assert "wish you were here" in album


def test_normalize_name_unicode_preserved():
    """
    GIVEN artist/album names with non-Latin characters
    WHEN normalize_name is called
    THEN the Unicode characters should be preserved (not stripped to ASCII).
    """
    artist, album = normalize_name("Björk", "Homogenic")
    assert "björk" in artist


def test_normalize_track_name_strips_punctuation():
    """
    GIVEN a track name with colons, dashes, and parentheses
    WHEN normalize_track_name is called
    THEN punctuation should be replaced with spaces and result lowercased.
    """
    result = normalize_track_name("Everything In Its Right Place (Live)")
    assert "everything in its right place" in result
    assert "(" not in result
    assert ")" not in result


def test_normalize_track_name_preserves_japanese():
    """
    GIVEN a track name composed entirely of Japanese katakana
    WHEN normalize_track_name is called
    THEN the characters are preserved (not collapsed to an empty string).

    Regression test: the previous NFKD + encode('ascii', 'ignore') path stripped
    all non-Latin characters, producing '' for any Japanese track name. This
    caused the min_tracks filter to silently fail for non-Latin albums and made
    playtime calculations return zero for every such album.
    """
    result = normalize_track_name("\u30e1\u30ae\u30c4\u30cd")  # "Megitsune" in katakana
    assert result == "\u30e1\u30ae\u30c4\u30cd"


def test_normalize_track_name_preserves_cyrillic():
    """
    GIVEN a track name in Cyrillic script
    WHEN normalize_track_name is called
    THEN the characters are preserved in their lowercased form.
    """
    result = normalize_track_name(
        "\u0421\u043e\u043f\u0440\u0430\u043d\u043e"
    )  # "Soprano"
    assert result == "\u0441\u043e\u043f\u0440\u0430\u043d\u043e"  # lowercased


def test_normalize_track_name_fullwidth_punctuation_converted():
    """
    GIVEN a track name containing a full-width exclamation mark (Japanese '!')
    WHEN normalize_track_name is called
    THEN NFKC maps the full-width char to its ASCII equivalent, which is then
    stripped, leaving the surrounding non-Latin text intact.
    """
    # Katakana + full-width '!!' -- NFKC converts full-width '!' to ASCII '!'
    result = normalize_track_name("\u30ae\u30df\u30c1\u30e7\u30b3\uff01\uff01")
    assert "\uff01" not in result  # full-width '!' gone
    assert "!" not in result  # ASCII '!' also stripped
    assert "\u30ae\u30df\u30c1\u30e7\u30b3" in result  # katakana preserved


def test_normalize_track_name_strips_ampersand():
    """
    GIVEN a track name containing '&'
    WHEN normalize_track_name is called
    THEN '&' is replaced with a space (consistent with normalize_name behavior).

    The previous hardcoded list of 13 punctuation characters omitted '&', '@',
    '#', and others present in string.punctuation, producing inconsistent
    normalization relative to normalize_name.
    """
    result = normalize_track_name("Tom & Jerry")
    assert "&" not in result
    assert "tom" in result
    assert "jerry" in result


def test_normalize_name_preserves_artist_edition_word():
    """
    GIVEN an artist whose name contains the word 'edition'
    WHEN normalize_name is called
    THEN 'edition' is retained in the artist key.

    'New Edition' is a real R&B group. The previous implementation applied the
    same metadata-stripping word set to both the artist and album strings,
    reducing 'New Edition' to 'new' and increasing key-collision risk.
    """
    artist, _ = normalize_name("New Edition", "New Edition")
    assert "edition" in artist
    assert "new" in artist


def test_normalize_name_strips_edition_from_album_not_artist():
    """
    GIVEN the word 'edition' in both the artist name and the album name
    WHEN normalize_name is called
    THEN 'edition' is stripped from the album but retained in the artist.
    """
    artist, album = normalize_name("New Edition", "Collector's Edition")
    assert "edition" in artist  # preserved for artist proper noun
    assert "edition" not in album  # stripped as album metadata


def test_normalize_name_ep_preserved_in_artist_stripped_from_album():
    """
    GIVEN an artist literally named 'EP' and an album literally titled 'EP'
    WHEN normalize_name is called
    THEN the artist key retains 'ep' while the album key is stripped to ''.
    """
    artist, album = normalize_name("EP", "EP")
    assert artist == "ep"
    assert album == ""


def test_normalize_name_no_collision_after_artist_fix():
    """
    GIVEN two artist/album pairs where both artist names are metadata words
    WHEN normalize_name is called on each
    THEN the resulting keys are distinct and do not collide.

    Before the fix, normalize_name('Bonus', 'Tracks') and
    normalize_name('Special', 'Edition') both returned ('', '') because the
    metadata-stripping word set was applied to the artist string. This caused a
    dictionary collision that silently merged two unrelated artists into one
    album entry during scrobble aggregation.
    """
    key_bonus = normalize_name("Bonus", "Tracks")
    key_special = normalize_name("Special", "Edition")
    assert key_bonus != key_special


def test_normalize_name_and_track_name_agree_on_non_latin():
    """
    GIVEN a non-Latin album and track name (Japanese katakana)
    WHEN normalize_name and normalize_track_name are both called
    THEN both produce non-empty output using the same NFKC code path.

    The previous mismatch -- normalize_name used NFKC (preserving non-Latin)
    while normalize_track_name used NFKD + encode('ascii', 'ignore') (stripping
    them) -- meant a Japanese album could be keyed correctly but every one of
    its tracks would normalize to '', causing playtime to be 0 and the album
    to be excluded by the min_tracks filter.
    """
    artist_key, album_key = normalize_name("BABYMETAL", "BABYMETAL")
    assert len(artist_key) > 0

    track_key = normalize_track_name("\u30ae\u30df\u30c1\u30e7\u30b3\uff01\uff01")
    assert len(track_key) > 0, (
        "Non-Latin track names must survive normalization; "
        "empty string means NFKD+ascii-encode regression has been reintroduced."
    )


def test_extract_registered_year_valid():
    """
    GIVEN a Last.fm user.getinfo response with a valid registration timestamp
    WHEN _extract_registered_year is called
    THEN it should return the correct year (2016 for flounder14's timestamp).
    """
    data = {
        "user": {"registered": {"unixtime": "1451606400", "#text": "2016-01-01 00:00"}}
    }
    assert _extract_registered_year(data) == 2016


def test_extract_registered_year_missing_key():
    """
    GIVEN a response missing the registered field
    WHEN _extract_registered_year is called
    THEN it should return None without raising an exception.
    """
    assert _extract_registered_year({}) is None
    assert _extract_registered_year({"user": {}}) is None
    assert _extract_registered_year({"user": {"registered": {}}}) is None
