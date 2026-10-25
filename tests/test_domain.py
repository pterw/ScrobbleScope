import pytest

from scrobblescope.domain import (
    COVER_WASH_COUNT,
    cover_wash_index,
    format_album_key,
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
    THEN the artist key retains 'ep' and the album, which would strip to
    nothing, keys on its own text instead of collapsing to ''.
    """
    artist, album = normalize_name("EP", "EP")
    assert artist == "ep"
    assert album == "ep"


def test_normalize_name_empty_remainder_keeps_distinct_pipe_free_identity():
    """
    GIVEN titles that normalize to nothing ('?', '!', 'EP', '||')
    WHEN normalize_name is called for one artist
    THEN each album half is non-empty, different titles get different keys,
    and no half contains the wire separator '|'.
    """
    keys = {t: normalize_name("bassvictim", t) for t in ("?", "!", "EP", "||")}
    assert all(album for _, album in keys.values())
    assert len({album for _, album in keys.values()}) == len(keys)
    assert all("|" not in half for key in keys.values() for half in key)
    assert normalize_name("a", "||")[1] == "^^"


@pytest.mark.parametrize(
    ("artist", "album"),
    [
        ("Radiohead", "OK Computer (Deluxe Edition)"),
        ("Bass", "Basspunk 2"),
        ("宇多田ヒカル", "初恋"),
        ("New Edition", "Heart Break"),
        ("New Edition", "Collector's Edition"),
        ("Artist", "|"),
        ("Artist", "EP |"),
        ("Artist", "||"),
        ("Artist", "?"),
        ("Artist", "EP"),
        ("Artist", "!!!"),
    ],
)
def test_normalize_name_is_idempotent(artist, album):
    """
    GIVEN any artist and album
    WHEN the normalized key is normalized again
    THEN it comes back unchanged, because both provider searches re-normalize
    the key they are given and a key that drifts can never match.
    """
    key = normalize_name(artist, album)
    assert normalize_name(*key) == key


@pytest.mark.parametrize(
    ("artist", "album", "expected"),
    [
        ("Radiohead", "OK Computer (Deluxe Edition)", ("radiohead", "ok computer")),
        ("Bass", "Basspunk 2", ("bass", "basspunk 2")),
        ("宇多田ヒカル", "初恋", ("宇多田ヒカル", "初恋")),
        ("New Edition", "Heart Break", ("new edition", "heart break")),
    ],
)
def test_normalize_name_nonempty_remainder_keys_unchanged(artist, album, expected):
    """
    GIVEN a title whose edition-word-stripped text is not empty
    WHEN normalize_name is called
    THEN the key is the cleaned, stripped text exactly as before.
    """
    assert normalize_name(artist, album) == expected


@pytest.mark.parametrize("album", ["?", "EP"])
def test_format_album_key_round_trips_empty_remainder_titles(album):
    """
    GIVEN an album whose title normalizes to nothing
    WHEN its key is formatted for the wire and split on '|'
    THEN the two halves come back unchanged.
    """
    key = normalize_name("gapyear", album)
    wire = format_album_key(key)
    assert wire.count("|") == 1
    assert tuple(wire.split("|")) == key


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
    title = "\u30ae\u30df\u30c1\u30e7\u30b3\uff01\uff01"
    expected = "\u30ae\u30df\u30c1\u30e7\u30b3"

    _, album_key = normalize_name("BABYMETAL", title)
    track_key = normalize_track_name(title)

    assert album_key == track_key == expected, (
        "Non-Latin album and track names must survive normalization and agree; "
        "a mismatch means the NFKD+ascii-encode regression has been reintroduced."
    )


def test_cover_wash_index_is_pinned_across_processes():
    """
    GIVEN albums whose wash was computed once with zlib.crc32
    WHEN cover_wash_index is called now, in this process
    THEN each gets that same index, which Python's salted hash() could not
    promise: a wash that changed between requests would flicker on reload.

    Mutation: swap zlib.crc32 for hash() and these literals stop matching
    from the second interpreter on.
    """
    assert cover_wash_index("Radiohead", "OK Computer") == 7
    assert cover_wash_index("Artist A", "Album One") == 4
    assert cover_wash_index("Artist B", "Album Two") == 2


def test_cover_wash_index_is_stable_and_ignores_spelling_noise():
    """
    GIVEN one album spelled with different case, punctuation and edition tags
    WHEN cover_wash_index is called repeatedly
    THEN it returns one index, so the Results and Unmatched pages agree.
    """
    plain = cover_wash_index("the beatles", "let it be")
    assert plain == cover_wash_index("The Beatles.", "Let It Be (Deluxe Edition)")
    assert {cover_wash_index("the beatles", "let it be") for _ in range(5)} == {plain}


def test_cover_wash_index_spreads_albums_over_every_wash():
    """
    GIVEN two hundred distinct albums
    WHEN cover_wash_index is called for each
    THEN every wash in range is used and none outside it, so a page of
    coverless rows is not one colour.
    """
    used = {cover_wash_index(f"Artist {n}", f"Album {n}") for n in range(200)}
    assert used == set(range(COVER_WASH_COUNT))


def test_cover_wash_index_accepts_missing_names():
    """
    GIVEN a row with no artist or album, or None for either
    WHEN cover_wash_index is called
    THEN it returns an in-range index rather than raising.
    """
    for artist, album in (("", ""), (None, None), ("Only Artist", None)):
        assert 0 <= cover_wash_index(artist, album) < COVER_WASH_COUNT
