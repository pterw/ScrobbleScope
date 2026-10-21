import contextlib
import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Standard form data for POST /results_loading tests (year as string, flounder14).
# Use {**VALID_FORM_DATA, "year": "2015"} to override individual fields.
VALID_FORM_DATA = {
    "username": "flounder14",
    "year": "2025",
    "sort_by": "playcount",
    "release_scope": "same",
    "min_plays": "10",
    "min_tracks": "3",
    "limit_results": "all",
}

TEST_JOB_PARAMS = {
    "username": "testuser",
    "year": 2025,
    "sort_mode": "playcount",
    "release_scope": "same",
    "decade": None,
    "release_year": None,
    "min_plays": 10,
    "min_tracks": 3,
    "limit_results": "all",
    "mode": "album",
}


#: The album object `fetch_spotify_album_details_batch` returns for "sp1" in
#: test_process_albums_persists_a_spotify_row_through_the_contract. Shared so
#: tests/test_provider_fixtures.py can check it for drift against the
#: doc-transcribed fixture without keeping its own stale copy (F-MAS-1).
SPOTIFY_ALBUM_DETAILS_MOCK = {
    "release_date": "2025-01-01",
    "images": [{"url": "https://img.example.com/a.jpg"}],
    "tracks": {"items": [{"name": "Track One", "duration_ms": 240000}]},
}


class NoopAsyncContext:
    """A no-op async context manager for patching rate limiters in tests."""

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_response_context(response):
    """Build an async context manager whose __aenter__ returns response."""
    cm = AsyncMock()
    cm.__aenter__.return_value = response
    return cm


# ---------------------------------------------------------------------------
# The Last.fm HTTP edge, for tests that run a whole pipeline
# ---------------------------------------------------------------------------


class FakeLastfm:
    """Scripted Last.fm answers, one per page number.

    ``pages`` maps a page number to the JSON body served for it with HTTP 200.
    ``statuses`` maps a page number to a non-200 status, which wins over a
    body. A page named in neither answers HTTP 500, as an outage would. The
    page numbers asked for are kept in ``requested``.
    """

    def __init__(self, pages, statuses=None):
        self.pages = pages
        self.statuses = statuses or {}
        self.requested = []

    def get(self, url, params=None, **kwargs):
        """Answer one ``session.get`` the way the page layer reads it."""
        page = params["page"]
        self.requested.append(page)
        resp = AsyncMock()
        resp.status = self.statuses.get(page, 200 if page in self.pages else 500)
        resp.json = AsyncMock(return_value=self.pages.get(page))
        resp.text = AsyncMock(return_value="")
        resp.content_type = "application/json"
        resp.headers = {}
        return make_response_context(resp)


@contextlib.contextmanager
def lastfm_edge(fake):
    """Route every Last.fm request to ``fake``; nothing else is patched.

    The session, the rate limiter, the request cache and ``asyncio.sleep`` (the
    retry back-off) are the network edge; the page layer, the pagination and
    everything above them run for real.
    """
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=fake)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    with (
        patch("scrobblescope.lastfm.create_optimized_session", return_value=session_cm),
        patch(
            "scrobblescope.lastfm.get_lastfm_limiter", return_value=NoopAsyncContext()
        ),
        patch("scrobblescope.lastfm.get_cached_response", return_value=None),
        patch("scrobblescope.lastfm.set_cached_response"),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        yield fake


def lastfm_page(tracks, number=1, total=1):
    """One ``user.getrecenttracks`` page; ``tracks`` is served exactly as given."""
    return {
        "recenttracks": {
            "@attr": {"page": str(number), "totalPages": str(total)},
            "track": tracks,
        }
    }


def lastfm_track(artist, album, name, when):
    """One dated scrobble; ``when`` is a tz-aware ``datetime``."""
    return {
        "artist": {"#text": artist},
        "album": {"#text": album},
        "name": name,
        "date": {"uts": str(int(when.timestamp()))},
    }


def lastfm_now_playing(artist, album, name):
    """The entry Last.fm adds for a track playing now: no ``date`` field."""
    return {
        "artist": {"#text": artist},
        "album": {"#text": album},
        "name": name,
        "@attr": {"nowplaying": "true"},
    }


def lastfm_albums(
    eligible=None,
    exclusions=None,
    *,
    pages_expected=1,
    pages_received=1,
    plays_seen=0,
    total_below_threshold=None,
):
    """What ``fetch_top_albums_async`` returns: ``(AlbumSelection, FetchSummary)``.

    For tests that patch ``scrobblescope.orchestrator.fetch_top_albums_async``.
    ``unique_albums`` is derived (eligible plus excluded); the count of albums
    below threshold is ``len(exclusions)`` unless a cap made it larger.
    """
    from scrobblescope.lastfm import FetchSummary
    from scrobblescope.plays import AlbumSelection

    eligible = eligible or {}
    exclusions = exclusions or {}
    selection = AlbumSelection(
        eligible=eligible,
        exclusions=exclusions,
        total_below_threshold=(
            len(exclusions) if total_below_threshold is None else total_below_threshold
        ),
        plays_seen=plays_seen,
        unique_albums=len(eligible) + len(exclusions),
    )
    return selection, FetchSummary(pages_expected, pages_received)


KPI_CASES_PATH = Path(__file__).parent / "fixtures" / "heatmap_kpi_cases.json"
KPI_WINDOW_DAYS = 365


def load_kpi_cases():
    """Return the heatmap KPI case table (``tests/fixtures/heatmap_kpi_cases.json``)."""
    return json.loads(KPI_CASES_PATH.read_text(encoding="utf-8"))


def kpi_window(case):
    """Expand *case* to ``(from_iso, to_iso, daily_counts)``.

    ``daily_counts`` is zero-filled and ascending, the shape the heatmap job
    publishes: one key per UTC day of a 365-day window ending on ``case["end"]``.
    """
    end = date.fromisoformat(case["end"])
    counts = {
        (end - timedelta(days=k)).isoformat(): 0
        for k in range(KPI_WINDOW_DAYS - 1, -1, -1)
    }
    if "every_day" in case:
        counts = {day: case["every_day"] for day in counts}
    for offset, count in case.get("plays", {}).items():
        counts[(end - timedelta(days=int(offset))).isoformat()] = count
    return next(iter(counts)), case["end"], counts


def kpi_payload(case):
    """Return the heatmap result dict a job would store for *case*, without statistics."""
    from_iso, to_iso, counts = kpi_window(case)
    return {
        "username": "kpi-user",
        "from_date": from_iso,
        "to_date": to_iso,
        "total_scrobbles": sum(counts.values()),
        "max_count": max(counts.values()),
        "daily_counts": counts,
    }


def expected_kpi_blocks(case):
    """Return the four KPI blocks the page must show for *case*, in order."""
    e = case["expected"]
    return [
        {"label": "SCROBBLES", "value": e["scrobbles"], "sub": ""},
        {"label": "DAILY AVERAGE", "value": e["daily_average"], "sub": ""},
        {"label": "BEST DAY", "value": e["best_count"], "sub": e["best_label"]},
        {"label": "CURRENT STREAK", "value": e["streak"], "sub": "DAYS"},
    ]
