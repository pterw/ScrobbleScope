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
