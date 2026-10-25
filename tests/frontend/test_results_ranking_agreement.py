"""The Results page ranks the same whether the server or the client did it (R6).

One seeded result (four albums: two with listening time, one with seconds 0,
one without the key) is rendered by the Flask test client twice: as a run
started in listening-time mode and as a run started in play-count mode. Each
HTML is loaded into Chromium with its static scripts served off disk, and the
play-count page is switched to listening time through the real toggle button.
The two pages must then show one leaderboard: same visible (album, rank)
sequence, same whole-result figures, same hidden-count note and same CSV rows.
"""

from __future__ import annotations

import mimetypes
import re

import pytest

from scrobblescope import jobs
from tests.frontend.conftest import REPO_ROOT
from tests.helpers import TEST_JOB_PARAMS

pytestmark = pytest.mark.browser

ORIGIN = "http://results.test"
STATIC_ROOT = REPO_ROOT / "static"

# (album, plays, listening seconds or None for "no key"). The two timed albums
# rank in opposite order by plays and by listening time, so a client that sorts
# by the wrong metric fails. In the listening-time run the durationless albums
# (Bravo at 0 seconds, Delta with no key) sort after the timed ones.
SEED = [
    ("Alpha", 30, 3000),
    ("Bravo", 40, 0),
    ("Charlie", 50, 1200),
    ("Delta", 20, None),
]
TIMED_RANKING = [("Alpha", "1"), ("Charlie", "2")]
PLAYS_RANKING = [("Charlie", "1"), ("Bravo", "2"), ("Alpha", "3"), ("Delta", "4")]

VISIBLE_ROWS_JS = """() => [...document.querySelectorAll('#results-table tbody tr')]
    .filter(row => !row.hidden)
    .map(row => [row.dataset.album, row.dataset.rank,
                 row.querySelector('.rank-num').textContent.trim()])"""


def _rows(sort_mode):
    """The seed as the orchestrator stores it: ordered by the run's own metric."""
    rows = []
    for album, plays, seconds in SEED:
        row = {
            "artist": "Shared Band",  # one artist for all rows: Top Artist follows the first row (F-B23-64)
            "album": album,
            "play_count": plays,
            "play_time": f"{(seconds or 0) // 60}m",
            "release_date": "2025-01-01",
            "album_image": "",
            "spotify_id": "",
            "provider": "spotify",
            "album_url": "",
        }
        if seconds is not None:
            row["play_time_seconds"] = seconds
        rows.append(row)
    key = "play_time_seconds" if sort_mode == "playtime" else "play_count"
    return sorted(rows, key=lambda row: row.get(key, 0), reverse=True)


def _render(client, sort_mode):
    job_id = jobs.create({**TEST_JOB_PARAMS, "sort_mode": sort_mode})
    jobs.succeed(job_id, _rows(sort_mode), "Done!")
    response = client.post("/results_complete", data={"job_id": job_id})
    assert response.status_code == 200
    return response.data.decode("utf-8")


def _open(js_browser, html):
    """Load rendered HTML; /static comes off disk, every other call is aborted."""
    page = js_browser.new_page()

    def handle(route):
        url = route.request.url
        if url == f"{ORIGIN}/results":
            route.fulfill(body=html, content_type="text/html")
        elif url.startswith(f"{ORIGIN}/static/"):
            path = STATIC_ROOT / url.split("/static/", 1)[1].split("?", 1)[0]
            if path.is_file():
                kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                route.fulfill(body=path.read_bytes(), content_type=kind)
                return
            route.abort()
        else:
            route.abort()

    page.route("**/*", handle)
    page.goto(f"{ORIGIN}/results")
    page.wait_for_function("() => document.getElementById('toggle-sort-plays')")
    # results.js attaches its handlers on DOMContentLoaded, before the load event
    page.wait_for_load_state("load")
    return page


def _figures(page):
    return page.evaluate(
        """() => ({
            total: document.getElementById('stat-total-albums').textContent.trim(),
            artist: document.getElementById('stat-top-artist').textContent.trim(),
            scrobbles: document.getElementById('stat-scrobbles').textContent.trim(),
        })"""
    )


def _note(page):
    return page.evaluate(
        """() => {
            const note = document.getElementById('playtime-hidden-note');
            return [note.hidden,
                    Number(document.getElementById('playtime-hidden-count').textContent)];
        }"""
    )


def _csv_rows(page):
    """Click the real export button and read the CSV the page built."""
    page.evaluate(
        """() => {
            window.__csv = null;
            URL.createObjectURL = blob => { window.__csv = blob; return 'blob:csv'; };
            HTMLAnchorElement.prototype.click = function () {};
        }"""
    )
    page.click("#export-csv")
    text = page.evaluate("async () => await window.__csv.text()")
    return text.split("\n")[1:]  # the header line is fixed


def _switch(page, button):
    page.click(f"#{button}")
    page.wait_for_function(
        "(id) => document.getElementById(id).getAttribute('aria-pressed') === 'true'",
        arg=button,
    )


@pytest.fixture
def pages(js_browser, client):
    """(playtime-started page, play-count page switched to listening time)."""
    started = _open(js_browser, _render(client, "playtime"))
    switched = _open(js_browser, _render(client, "playcount"))
    _switch(switched, "toggle-sort-playtime")
    yield started, switched
    started.close()
    switched.close()


def test_both_paths_show_the_same_listening_time_leaderboard(pages):
    """
    GIVEN a playtime run and a play-count run switched to listening time
    WHEN each page shows its leaderboard
    THEN the visible (album, rank) sequence, the whole-result figures and the
    hidden-count note agree, and the rank cell shows the same two-digit rank.

    Mutation: a server that renders the durationless rows without `hidden`, or
    a client that skips the renumber, makes the sequences differ.
    """
    started, switched = pages
    expected = [[album, rank, f"0{rank}"] for album, rank in TIMED_RANKING]
    assert started.evaluate(VISIBLE_ROWS_JS) == expected
    assert switched.evaluate(VISIBLE_ROWS_JS) == expected
    assert _figures(started) == _figures(switched)
    assert _figures(started)["total"] == "4"
    assert _note(started) == _note(switched) == [False, 2]


def test_playtime_run_restores_every_album_on_plays_and_back(pages):
    """
    GIVEN a run started in listening-time mode
    WHEN it is switched to track plays and back to listening time
    THEN all four albums come back ranked by plays, the note is hidden, and
    the first list is reproduced.

    Mutation: a server that renders the durationless rows without `hidden`
    shows them in the first list; a client that skips the renumber leaves gaps
    in the plays ranking.
    """
    started, _ = pages
    first = started.evaluate(VISIBLE_ROWS_JS)
    _switch(started, "toggle-sort-plays")
    shown = started.evaluate(VISIBLE_ROWS_JS)
    assert [(album, rank) for album, rank, _ in shown] == PLAYS_RANKING
    assert [cell for _, _, cell in shown] == ["01", "02", "03", "04"]
    assert _note(started)[0] is True
    _switch(started, "toggle-sort-playtime")
    assert started.evaluate(VISIBLE_ROWS_JS) == first
    assert _note(started) == [False, 2]


def test_csv_export_matches_across_both_paths(pages):
    """
    GIVEN a playtime run and a play-count run switched to listening time
    WHEN each exports its CSV
    THEN the rows are identical: the two timed albums, ranked 1 and 2.

    Mutation: a hidden durationless row left in the export, or a skipped
    renumber, changes the rows.
    """
    started, switched = pages
    rows = _csv_rows(started)
    assert rows == _csv_rows(switched)
    assert [re.match(r'"(\d+)","([^"]*)"', row).groups() for row in rows] == [
        (rank, album) for album, rank in TIMED_RANKING
    ]
