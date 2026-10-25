"""Album metadata through the real cache module, end to end.

These tests drive ``process_albums`` (and the correction worker) against
``tests/fake_postgres.py``. They name no function of ``scrobblescope.cache``,
so they hold unchanged across the encoding change and the connection-ownership
change (AGENTS.md "Refactor requires parity tests"). What they pin:

* what a provider's album looks like once stored, and that reading it back
  answers a repeat search exactly as the live fetch did;
* that a stored row holds album facts only (``BATCH23_DEFINITION.md`` "Data
  handling": shared cache rows contain no listening facts);
* that the cache is optional: no database, a sleeping one, a failing read, a
  failing write all leave the search to the providers;
* the database traffic of one search, so a later change cannot add any (the
  hosting cost ceiling).
"""

import json
import os
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope import jobs, release_checks
from scrobblescope.domain import normalize_track_name
from scrobblescope.enrichment import AlbumMetadata
from scrobblescope.errors import SpotifyUnavailableError
from scrobblescope.orchestrator import process_albums
from tests.fake_postgres import METADATA_FIELDS, fake_postgres
from tests.helpers import TEST_JOB_PARAMS

ORCH = "scrobblescope.orchestrator."
KEY = ("radiohead", "ok computer")
SECOND_KEY = ("mitski", "laurel hell")
SPOTIFY_ID = "sp-radiohead"
SPOTIFY_URL = f"https://open.spotify.com/album/{SPOTIFY_ID}"
PLAY_COUNT = 4242
LISTENER = "listener_zq"
PARANOID = normalize_track_name("Paranoid Android")
KARMA = normalize_track_name("Karma Police")
DURATIONS = {PARANOID: 383, KARMA: 264}

SPOTIFY_DETAILS = {
    "release_date": "1997-06-16",
    "images": [{"url": "https://img.example.com/ok.jpg"}],
    "tracks": {
        "items": [
            {"name": "Paranoid Android", "duration_ms": 383000},
            {"name": "Karma Police", "duration_ms": 264000},
        ]
    },
}
DEEZER_ALBUM = AlbumMetadata(
    provider="deezer",
    album_id="9",
    url="https://www.deezer.com/album/9",
    release_date="1997-06-16",
    image_url="https://img.example.com/dz.jpg",
    track_durations=dict(DURATIONS),
)

#: The keys of one Results row. A change of encoding must not add, drop or
#: rename one: the page and the JSON endpoints read them by name.
RESULT_FIELDS = {
    "artist",
    "album",
    "play_count",
    "play_time",
    "play_time_mobile",
    "play_time_seconds",
    "different_songs",
    "release_date",
    "album_image",
    "spotify_id",
    "provider",
    "album_url",
    "_normalized_key",
    "proportion_of_max",
    "proportion_of_total",
}


def _entry(artist, album):
    """One album as the Last.fm stage hands it to enrichment."""
    return {
        "play_count": PLAY_COUNT,
        "track_counts": {PARANOID: 10, KARMA: 8},
        "original_artist": artist,
        "original_album": album,
    }


FILTERED = {KEY: _entry("Radiohead", "OK Computer")}
TWO_ALBUMS = {
    KEY: _entry("Radiohead", "OK Computer"),
    SECOND_KEY: _entry("Mitski", "Laurel Hell"),
}


def _session_ctx():
    """An async context manager standing in for an aiohttp session."""
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


@contextmanager
def _spotify(release_date="1997-06-16"):
    """Spotify matches every album (id ``sp-<artist>``) and details it."""
    details = {**SPOTIFY_DETAILS, "release_date": release_date}

    async def search(session, artist, album, token, semaphore=None):
        return f"sp-{artist}"

    async def batch(session, ids, token, semaphore=None, on_fallback=None):
        return {spotify_id: details for spotify_id in ids}

    with (
        patch(ORCH + "fetch_spotify_access_token", AsyncMock(return_value="tok")),
        patch(ORCH + "create_optimized_session", side_effect=lambda: _session_ctx()),
        patch(ORCH + "search_for_spotify_album_id", side_effect=search),
        patch(ORCH + "fetch_spotify_album_details_batch", side_effect=batch),
    ):
        yield


@contextmanager
def _deezer():
    """Spotify matches nothing; Deezer matches every album as ``DEEZER_ALBUM``."""
    with (
        patch(ORCH + "fetch_spotify_access_token", AsyncMock(return_value="tok")),
        patch(ORCH + "create_optimized_session", side_effect=lambda: _session_ctx()),
        patch(ORCH + "search_for_spotify_album_id", AsyncMock(return_value=None)),
        patch(ORCH + "search_deezer_album", AsyncMock(return_value="9")),
        patch(ORCH + "fetch_deezer_album", AsyncMock(return_value=DEEZER_ALBUM)),
    ):
        yield


@contextmanager
def _providers_forbidden():
    """A cache hit must reach no provider: any call fails the test."""
    fault = AssertionError("a provider was called on a cache hit")
    with (
        patch(ORCH + "fetch_spotify_access_token", AsyncMock(side_effect=fault)),
        patch(ORCH + "search_deezer_album", AsyncMock(side_effect=fault)),
    ):
        yield


async def _search(filtered=None, *, year=1997, scope="same", params=None):
    """Run ``process_albums`` for a fresh job; return ``(job_id, results)``."""
    job_id = jobs.create(params or TEST_JOB_PARAMS)
    results = await process_albums(
        job_id, filtered or FILTERED, year, "playcount", scope
    )
    return job_id, results


def _stats(job_id):
    """The job's recorded stats."""
    return jobs.progress(job_id)["stats"]


# ---------------------------------------------------------------------------
# Storage and read-back
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it():
    """
    GIVEN Spotify details an album that is not cached
    WHEN the search runs, then runs again with every provider forbidden
    THEN the stored row holds the album's facts under the provider columns,
    and the second search returns exactly the rows the first returned.
    """
    with fake_postgres() as db:
        with _spotify():
            _, first = await _search()
        stored = dict(db.metadata[KEY])
        durations = json.loads(stored.pop("track_durations"))
        with _providers_forbidden():
            _, second = await _search()

    assert durations == DURATIONS
    assert stored == {
        "spotify_id": SPOTIFY_ID,
        "release_date": "1997-06-16",
        "album_image_url": "https://img.example.com/ok.jpg",
        "provider": "spotify",
        "provider_album_id": SPOTIFY_ID,
        "provider_url": SPOTIFY_URL,
        "provider_artist": None,
        "provider_title": None,
    }
    assert second == first
    (row,) = first
    assert set(row) == RESULT_FIELDS
    assert (row["spotify_id"], row["provider"], row["album_url"]) == (
        SPOTIFY_ID,
        "spotify",
        SPOTIFY_URL,
    )
    assert row["play_time_seconds"] == 383 * 10 + 264 * 8


@pytest.mark.asyncio
async def test_a_deezer_album_is_stored_without_a_spotify_id_and_a_repeat_search_matches_it():
    """
    GIVEN Spotify has no match and Deezer details the album
    WHEN the search runs, then runs again with every provider forbidden
    THEN the legacy spotify_id column stays NULL, the Deezer id and link are
    stored under the provider columns, and the repeat search returns the
    same rows.
    """
    with fake_postgres() as db:
        with _deezer():
            _, first = await _search()
        stored = dict(db.metadata[KEY])
        with _providers_forbidden():
            _, second = await _search()

    assert stored["spotify_id"] is None
    assert (
        stored["provider"],
        stored["provider_album_id"],
        stored["provider_url"],
    ) == ("deezer", "9", "https://www.deezer.com/album/9")
    assert second == first
    (row,) = first
    assert set(row) == RESULT_FIELDS
    assert (row["spotify_id"], row["provider"], row["album_url"]) == (
        None,
        "deezer",
        "https://www.deezer.com/album/9",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "columns",
    [
        {"spotify_id": "sp9"},
        {"spotify_id": "sp9", "provider": "spotify", "provider_album_id": "sp9"},
    ],
    ids=["written_before_the_provider_columns", "backfilled_without_a_link"],
)
async def test_an_older_spotify_row_reads_as_a_spotify_album_with_the_classic_link(
    columns,
):
    """
    GIVEN a cached row from before the provider columns, or one the migration
    backfilled with no link
    WHEN a search reads it
    THEN it is a Spotify album and its link is Spotify's classic album page.
    """
    with fake_postgres() as db:
        db.seed_metadata(
            *KEY,
            release_date="1997-06-16",
            album_image_url="https://img.example.com/ok.jpg",
            track_durations=DURATIONS,
            **columns,
        )
        with _providers_forbidden():
            _, results = await _search()

    (row,) = results
    assert (row["provider"], row["spotify_id"], row["album_url"]) == (
        "spotify",
        "sp9",
        "https://open.spotify.com/album/sp9",
    )
    assert row["play_time_seconds"] == 383 * 10 + 264 * 8


@pytest.mark.asyncio
@pytest.mark.parametrize("providers", [_spotify, _deezer], ids=["spotify", "deezer"])
async def test_a_stored_row_carries_no_listening_fact(providers):
    """
    GIVEN an album entry that carries the listener's name next to the 4242
    plays the listener made
    WHEN the album is stored in the shared cache
    THEN the row has exactly the album-fact columns, its durations are track
    name to seconds and nothing else, and neither the play count nor the
    listener's name appears anywhere in it (BATCH23 Data handling).
    """
    entry = {**_entry("Radiohead", "OK Computer"), "listener": LISTENER}
    with fake_postgres() as db:
        with providers():
            await _search({KEY: entry})

    (row,) = db.metadata.values()
    assert set(row) == set(METADATA_FIELDS)
    assert json.loads(row["track_durations"]) == DURATIONS
    stored = json.dumps(row)
    assert str(PLAY_COUNT) not in stored
    assert LISTENER not in stored


# ---------------------------------------------------------------------------
# The cache is optional
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_search_with_no_database_configured_uses_the_providers_and_connects_to_nothing():
    """
    GIVEN no DATABASE_URL
    WHEN a search runs
    THEN the providers answer it, no connection is attempted, and the job
    records that the cache was off.
    """
    with fake_postgres(url=None) as db:
        with _spotify():
            job_id, results = await _search()

    assert [row["spotify_id"] for row in results] == [SPOTIFY_ID]
    assert db.connect_attempts == 0
    assert db.statements == []
    assert _stats(job_id)["db_cache_enabled"] is False
    assert "db_cache_warning" in _stats(job_id)


@pytest.mark.asyncio
async def test_a_search_while_the_database_is_asleep_uses_the_providers_after_bounded_attempts():
    """
    GIVEN a database that never answers (every connect times out)
    WHEN a search runs
    THEN it makes exactly DB_CONNECT_MAX_ATTEMPTS attempts, no more, then the
    providers answer it and the job records a cache warning. A sleeping
    database must cost one bounded wake-up attempt, not a failed job.
    """
    env = {"DB_CONNECT_MAX_ATTEMPTS": "3", "DB_CONNECT_BASE_DELAY_SECONDS": "0"}
    with fake_postgres(connect_error=TimeoutError()) as db:
        with patch.dict(os.environ, env), _spotify():
            job_id, results = await _search()

    assert [row["spotify_id"] for row in results] == [SPOTIFY_ID]
    assert db.connect_attempts == 3
    assert db.statements == []
    assert _stats(job_id)["db_cache_enabled"] is False
    assert "db_cache_warning" in _stats(job_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("statement", "warning"),
    [
        (("SELECT", "spotify_cache"), "DB lookup failed; cache bypassed."),
        (("INSERT", "spotify_cache"), "DB persist failed."),
        (("SELECT", "original_release_cache"), None),
    ],
    ids=["read", "write", "correction_read"],
)
async def test_a_failing_cache_statement_never_fails_the_search(statement, warning):
    """
    GIVEN one cache statement raises (a dropped connection)
    WHEN a search runs
    THEN the providers still answer it, the job carries the matching warning
    (none for the correction read), and the search used one connection, closed
    once: a failure never opens a second connection.
    """
    with fake_postgres() as db:
        db.fail(*statement, OSError("connection reset"))
        with _spotify():
            job_id, results = await _search()

    assert [row["spotify_id"] for row in results] == [SPOTIFY_ID]
    assert _stats(job_id).get("db_cache_warning") == warning
    assert (db.connect_attempts, db.closes) == (1, 1)


@pytest.mark.asyncio
async def test_the_connection_is_closed_once_when_the_search_succeeds():
    """A finished search leaves no connection open."""
    with fake_postgres() as db:
        with _spotify():
            await _search()

    assert (db.connect_attempts, db.closes) == (1, 1)


@pytest.mark.asyncio
async def test_the_connection_is_closed_once_when_no_provider_can_answer():
    """
    GIVEN Spotify cannot issue a token and Deezer finds nothing
    WHEN the search raises SpotifyUnavailableError
    THEN the connection was still closed, once.
    """
    with fake_postgres() as db:
        with (
            patch(ORCH + "fetch_spotify_access_token", AsyncMock(return_value=None)),
            patch(
                ORCH + "create_optimized_session", side_effect=lambda: _session_ctx()
            ),
            patch(ORCH + "search_deezer_album", AsyncMock(return_value=None)),
            pytest.raises(SpotifyUnavailableError),
        ):
            await _search()

    assert (db.connect_attempts, db.closes) == (1, 1)


# ---------------------------------------------------------------------------
# Database traffic: the hosting cost ceiling
# ---------------------------------------------------------------------------

SELECT_METADATA = ("SELECT", "spotify_cache")
DELETE_STALE = ("DELETE", "spotify_cache")
INSERT_METADATA = ("INSERT", "spotify_cache")
SELECT_CORRECTIONS = ("SELECT", "original_release_cache")


@pytest.mark.asyncio
async def test_a_search_costs_one_connection_and_a_fixed_statement_sequence():
    """
    GIVEN two albums, neither cached
    WHEN a search runs, then runs again with both cached
    THEN the first costs one connection and four statements (one batch read,
    one stale-row delete, ONE upsert for both albums, one correction read) and
    the second three (no upsert). A change that persists per album, retries,
    reconnects or adds a statement wakes the database more often than the
    hosting cost ceiling allows, and fails here.
    """
    with fake_postgres() as db:
        with _spotify():
            await _search(TWO_ALBUMS)
        assert db.statements == [
            SELECT_METADATA,
            DELETE_STALE,
            INSERT_METADATA,
            SELECT_CORRECTIONS,
        ]
        assert (db.connect_attempts, db.closes) == (1, 1)

        db.statements.clear()
        with _providers_forbidden():
            await _search(TWO_ALBUMS)
        assert db.statements == [SELECT_METADATA, DELETE_STALE, SELECT_CORRECTIONS]
        assert (db.connect_attempts, db.closes) == (2, 2)


# ---------------------------------------------------------------------------
# MusicBrainz year correction, and the exclusion record
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_musicbrainz_finding_is_stored_and_corrects_the_next_search():
    """
    GIVEN an album a provider dates 2011 (a reissue) and MusicBrainz dates 1977
    WHEN the correction worker checks the finished job, then a 1977 search runs
    THEN the finding is stored, and the later search shows the album under
    1977 while keeping the provider's date beside it.
    """
    first_params = {**TEST_JOB_PARAMS, "year": 2011, "release_scope": "same"}
    with fake_postgres() as db:
        with _spotify(release_date="2011-01-31"):
            job_id, results = await _search(year=2011, params=first_params)
        assert [row["release_date"] for row in results] == ["2011-01-31"]
        jobs.succeed(job_id, results, "done")

        with (
            patch.object(release_checks, "MUSICBRAINZ_ENABLED", True),
            patch.object(
                release_checks,
                "lookup_original_release",
                AsyncMock(return_value=("mbid-1", "1977-02-04")),
            ),
            patch.object(
                release_checks,
                "create_optimized_session",
                side_effect=lambda: _session_ctx(),
            ),
        ):
            await release_checks.run_release_checks(job_id)
        assert db.original_releases[KEY] == {
            "mb_release_group": "mbid-1",
            "original_release": "1977-02-04",
        }

        with _providers_forbidden():
            _, corrected = await _search(year=1977)

    (row,) = corrected
    assert row["release_date"] == "1977-02-04"
    assert row["provider_release_date"] == "2011-01-31"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("providers", "expected"),
    [
        (
            _spotify,
            {
                "spotify_id": SPOTIFY_ID,
                "provider": "spotify",
                "album_url": SPOTIFY_URL,
                "album_image": "https://img.example.com/ok.jpg",
            },
        ),
        (
            _deezer,
            {
                "spotify_id": None,
                "provider": "deezer",
                "album_url": "https://www.deezer.com/album/9",
                "album_image": "https://img.example.com/dz.jpg",
            },
        ),
    ],
    ids=["spotify", "deezer"],
)
async def test_an_album_outside_the_release_scope_is_listed_with_its_provider_facts(
    providers, expected
):
    """
    GIVEN an album released in 1997 and a 2024 search
    WHEN the release filter excludes it
    THEN the unmatched record carries the provider, link, cover and provider
    date, and exactly the fields the Unmatched page reads.
    """
    with fake_postgres():
        with providers():
            job_id, results = await _search(year=2024)

    assert results == []
    (entry,) = jobs.unmatched(job_id).values()
    assert entry["reason_code"] == "release_scope"
    assert {name: entry[name] for name in expected} == expected
    assert entry["provider_release_date"] == "1997-06-16"
    assert set(entry) == {
        "artist",
        "album",
        "reason",
        "reason_code",
        "album_image",
        "spotify_id",
        "provider",
        "album_url",
        "play_count",
        "provider_release_date",
    }
