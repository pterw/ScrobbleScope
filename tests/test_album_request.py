"""The album request module: a submitted form becomes a request or a refusal."""

import re
from pathlib import Path

import pytest

from scrobblescope import album_request as module
from scrobblescope import jobs
from scrobblescope.album_request import (
    AlbumRequest,
    Refusal,
    parse_album_request,
    registration_refusal,
)
from tests.helpers import VALID_FORM_DATA

CURRENT_YEAR = 2025
INDEX_HTML = (
    Path(__file__).resolve().parents[1] / "templates" / "index.html"
).read_text(encoding="utf-8")


def _form(**overrides):
    """VALID_FORM_DATA with *overrides* applied; a None value removes the field."""
    form = {**VALID_FORM_DATA, **overrides}
    return {key: value for key, value in form.items() if value is not None}


def _parse(**overrides):
    return parse_album_request(_form(**overrides), current_year=CURRENT_YEAR)


def test_a_complete_form_becomes_one_request():
    request = _parse(
        year="2023",
        sort_by="playtime",
        release_scope="decade",
        decade="1990s",
        release_year="1982",
        min_plays="7",
        min_tracks="4",
        limit_results="25",
    )

    assert request == AlbumRequest(
        username="flounder14",
        year=2023,
        sort_mode="playtime",
        include_unmatched=False,
        release_scope="decade",
        decade="1990s",
        release_year=None,
        min_plays=7,
        min_tracks=4,
        limit_results="25",
    )


def test_a_form_with_only_a_name_and_a_year_takes_the_form_defaults():
    """The defaults are the ones the form shows: play count, same year, 10, 3, all."""
    request = parse_album_request(
        {"username": "flounder14", "year": "2025"}, current_year=CURRENT_YEAR
    )

    assert request == AlbumRequest("flounder14", 2025)
    assert (
        request.sort_mode,
        request.release_scope,
        request.min_plays,
        request.min_tracks,
        request.limit_results,
        request.include_unmatched,
    ) == ("playcount", "same", 10, 3, "all", False)


def test_a_blank_optional_field_is_a_missing_one():
    blank = _parse(sort_by="", release_scope="", limit_results="", min_plays=" ")
    absent = _parse(
        sort_by=None, release_scope=None, limit_results=None, min_plays=None
    )

    assert blank == absent
    assert not isinstance(blank, Refusal)


@pytest.mark.parametrize(
    "overrides, field, message",
    [
        ({"username": None}, "username", "Username and year are required."),
        ({"username": "   "}, "username", "Username and year are required."),
        ({"year": None}, "year", "Username and year are required."),
        ({"username": "x" * 65}, "username", "Username is too long."),
        ({"year": "20x5"}, "year", "Year must be a valid number."),
        ({"year": "2001"}, "year", "Year must be between 2002 and 2025."),
        ({"year": "2026"}, "year", "Year must be between 2002 and 2025."),
        (
            {"release_scope": "forever"},
            "release_scope",
            "Choose a release filter from the list.",
        ),
        (
            {"release_scope": "decade", "decade": "2030s"},
            "decade",
            "Choose a decade from the list.",
        ),
        (
            {"release_scope": "decade", "decade": None},
            "decade",
            "Choose a decade from the list.",
        ),
        (
            {"release_scope": "custom", "release_year": None},
            "release_year",
            "Enter a release year.",
        ),
        (
            {"release_scope": "custom", "release_year": "19x0"},
            "release_year",
            "Release year must be a valid number.",
        ),
        (
            {"release_scope": "custom", "release_year": "1899"},
            "release_year",
            "Release year must be between 1900 and 2025.",
        ),
        (
            {"release_scope": "custom", "release_year": "2026"},
            "release_year",
            "Release year must be between 1900 and 2025.",
        ),
        (
            {"sort_by": "loudness"},
            "sort_by",
            "Choose Play count or Play time to rank by.",
        ),
        (
            {"limit_results": "7"},
            "limit_results",
            "Choose how many albums to show from the list.",
        ),
        (
            {"min_plays": "0"},
            "min_plays",
            "Minimum plays must be a whole number from 1 to 50.",
        ),
        (
            {"min_plays": "51"},
            "min_plays",
            "Minimum plays must be a whole number from 1 to 50.",
        ),
        (
            {"min_plays": "many"},
            "min_plays",
            "Minimum plays must be a whole number from 1 to 50.",
        ),
        (
            {"min_tracks": "0"},
            "min_tracks",
            "Minimum unique tracks must be a whole number from 1 to 10.",
        ),
        (
            {"min_tracks": "11"},
            "min_tracks",
            "Minimum unique tracks must be a whole number from 1 to 10.",
        ),
    ],
)
def test_an_unusable_field_is_refused_with_its_name_and_a_sentence(
    overrides, field, message
):
    assert _parse(**overrides) == Refusal(field, message)


@pytest.mark.parametrize(
    "overrides, attribute, expected",
    [
        ({"year": "2002"}, "year", 2002),
        ({"year": "2025"}, "year", 2025),
        ({"release_scope": "custom", "release_year": "1900"}, "release_year", 1900),
        ({"release_scope": "custom", "release_year": "2025"}, "release_year", 2025),
        ({"min_plays": "1"}, "min_plays", 1),
        ({"min_plays": "50"}, "min_plays", 50),
        ({"min_tracks": "1"}, "min_tracks", 1),
        ({"min_tracks": "10"}, "min_tracks", 10),
        ({"username": "x" * 64}, "username", "x" * 64),
        ({"username": "  flounder14  "}, "username", "flounder14"),
    ],
)
def test_the_edges_of_each_range_are_accepted(overrides, attribute, expected):
    assert getattr(_parse(**overrides), attribute) == expected


@pytest.mark.parametrize("limit", ["all", "10", "25", "50", "100"])
def test_every_limit_the_form_offers_is_accepted(limit):
    assert _parse(limit_results=limit).limit_results == limit


@pytest.mark.parametrize("sort_by", ["playcount", "playtime"])
def test_both_ranking_choices_are_accepted(sort_by):
    assert _parse(sort_by=sort_by).sort_mode == sort_by


@pytest.mark.parametrize(
    "scope, decade, release_year",
    [
        ("same", None, None),
        ("previous", None, None),
        ("all", None, None),
        ("decade", "1990s", None),
        ("custom", None, 1982),
    ],
)
def test_only_the_release_field_of_the_chosen_scope_survives(
    scope, decade, release_year
):
    request = _parse(release_scope=scope, decade="1990s", release_year="1982")

    assert (request.decade, request.release_year) == (decade, release_year)


@pytest.mark.parametrize(
    "include, sort_by, expected",
    [
        ("1", "playtime", (True, "playcount")),
        ("1", "playcount", (True, "playcount")),
        (None, "playtime", (False, "playtime")),
        ("0", "playtime", (False, "playtime")),
        ("true", "playcount", (False, "playcount")),
    ],
)
def test_an_include_run_is_always_a_play_count_run(include, sort_by, expected):
    """An unmatched album has no play time, so "All albums" cannot rank by it.

    Only the exact value "1" turns the choice on, as the form's radio sends it.
    """
    request = _parse(include_unmatched=include, sort_by=sort_by)

    assert (request.include_unmatched, request.sort_mode) == expected


def test_an_upload_form_has_no_username_to_require():
    """The export route (WP-4) has no Last.fm name and must not invent one."""
    request = parse_album_request(
        {"year": "2025"}, current_year=CURRENT_YEAR, require_username=False
    )

    assert request == AlbumRequest(None, 2025)
    assert parse_album_request(
        {}, current_year=CURRENT_YEAR, require_username=False
    ) == Refusal("year", "Year is required.")


@pytest.mark.parametrize(
    "year, registered_year, refused",
    [(2015, 2016, True), (2016, 2016, False), (2020, 2016, False)],
)
def test_a_year_before_the_account_existed_is_refused(year, registered_year, refused):
    refusal = registration_refusal(year, registered_year)

    assert (refusal is not None) is refused
    if refused:
        assert refusal == Refusal(
            "year",
            "Year 2015 is before your Last.fm registration year (2016). "
            "Please choose 2016 or later.",
        )


@pytest.mark.parametrize("unknown", [None, 0])
def test_an_unknown_registration_year_is_no_reason_to_refuse(unknown):
    """The registration year is a hint: without it the search proceeds."""
    assert registration_refusal(2003, unknown) is None


def test_a_request_survives_being_stored_on_the_job_record():
    request = _parse(release_scope="custom", release_year="1982", include_unmatched="1")

    params = request.to_params()

    assert params["mode"] == jobs.MODE_ALBUM == "album"
    assert set(params) == {
        "username",
        "year",
        "sort_mode",
        "include_unmatched",
        "release_scope",
        "decade",
        "release_year",
        "min_plays",
        "min_tracks",
        "limit_results",
        "mode",
    }
    assert AlbumRequest.from_params(params) == request


def test_a_job_record_without_a_name_or_year_is_not_a_request():
    with pytest.raises(TypeError):
        AlbumRequest.from_params({"year": 2025, "mode": "album"})


class _SpyForm(dict):
    """A form that records every key the parser asks for."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read = set()

    def get(self, key, default=None):
        self.read.add(key)
        return super().get(key, default)


def test_form_fields_lists_exactly_the_fields_the_parser_reads():
    """The Retry contract test trusts FORM_FIELDS, so it must be the real list.

    Mutation: make the parser read a new field (say `form.get("source")`), or
    delete "decade" from FORM_FIELDS, and this fails.
    """
    read = set()
    for scope in module.RELEASE_SCOPES:
        form = _SpyForm(_form(release_scope=scope, decade="1990s", release_year="1982"))
        parse_album_request(form, current_year=CURRENT_YEAR)
        read |= form.read

    assert read == set(module.FORM_FIELDS)


def test_every_scope_the_server_accepts_has_a_release_window_rule():
    """A scope added here but not to domain.release_window would filter nothing.

    Mutation: add "fortnight" to RELEASE_SCOPES and this fails.
    """
    from scrobblescope.domain import release_window

    for scope in module.RELEASE_SCOPES:
        window = release_window(scope, 2023, decade="1990s", release_year=1982)
        assert (window is None) is (scope == "all"), scope


def _select_values(select_id):
    block = re.search(rf'<select id="{select_id}".*?</select>', INDEX_HTML, re.S)
    return set(re.findall(r'<option value="([^"]+)"', block.group(0)))


def _input_numbers(field_id, *attributes):
    tag = re.search(rf'<input[^>]*id="{field_id}"[^>]*>', INDEX_HTML, re.S).group(0)
    return tuple(int(re.search(rf'{a}="(\d+)"', tag).group(1)) for a in attributes)


def test_the_server_accepts_exactly_what_the_form_offers():
    """A choice the form shows must be accepted; one it does not show, refused.

    Mutation: drop "100" from LIMIT_OPTIONS, or add a decade the form lacks,
    and this fails.
    """
    assert _select_values("release_scope") == set(module.RELEASE_SCOPES)
    assert _select_values("limit_results") == set(module.LIMIT_OPTIONS)
    assert set(re.findall(r'name="sort_by" value="(\w+)"', INDEX_HTML)) == set(
        module.SORT_MODES
    )
    loop = re.search(r"for decade in \[([^\]]+)\]", INDEX_HTML).group(1)
    assert tuple(re.findall(r"'(\d{4}s)'", loop)) == module.DECADES


def test_the_server_ranges_are_the_ranges_the_form_enforces():
    assert _input_numbers("year", "min") == (module.MIN_LISTENING_YEAR,)
    assert _input_numbers("release_year", "min") == (module.MIN_RELEASE_YEAR,)
    assert _input_numbers("min_plays", "min", "max") == module.MIN_PLAYS_BOUNDS
    assert _input_numbers("min_tracks", "min", "max") == module.MIN_TRACKS_BOUNDS
