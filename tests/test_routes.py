# tests/test_routes.py
import re
from unittest.mock import patch

from scrobblescope.orchestrator import background_task
from scrobblescope.repositories import (
    JOBS,
    add_job_unmatched,
    create_job,
    get_job_progress,
    get_job_unmatched,
    jobs_lock,
    set_job_error,
    set_job_progress,
    set_job_results,
)
from scrobblescope.routes import (
    _filter_results_for_display,
    _get_filter_description,
    _group_unmatched_by_reason,
)
from tests.helpers import TEST_JOB_PARAMS, VALID_FORM_DATA

HEATMAP_JOB_PARAMS = {"username": "testuser", "mode": "heatmap"}


#: Stands in for "the index page rendered" in the tests below.
#:
#: It used to be the form card's h2, "Filter Your Album Scrobbles!". WP-3
#: removed that heading: the design's card carries no title, and the
#: exclamation mark belongs to the old register. This is the page headline
#: instead -- copy the index would be wrong without, which is what a marker
#: has to be.
INDEX_HEADLINE = b"Your top albums,"


def test_home_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid and contains key content.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert INDEX_HEADLINE in response.data


def test_home_page_mode_tabs_are_real_buttons(client):
    """The mode tabs are buttons, in sentence case, with no span standing in.

    They were span[role="button"][tabindex="0"] before WP-3, which is one of
    the three defects in F-B21-5, and they had unequal widths, which is
    F-B18-12. A real button brings Enter and Space with it, so the keydown
    handler that used to fake them is gone from static/js/heatmap.js.
    """
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<button type="button" id="mode-tab-album"' in html
    assert '<button type="button" id="mode-tab-heatmap"' in html
    assert "Top albums" in html
    # Not only the tabs. A span standing in for a control anywhere on the page
    # is the same defect, and the next one would be added the same way.
    assert 'role="button"' not in html
    assert "Top Albums" not in html
    assert 'role="button"' not in html


def test_heatmap_page_without_saved_job_uses_dedicated_empty_state(client):
    """The Heatmap destination should explain how to create the first result."""
    response = client.get("/heatmap")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'data-empty-state="heatmap"' in html
    assert 'href="/?mode=heatmap"' in html
    assert 'href="/heatmap" aria-current="page"' in html


def test_home_heatmap_mode_starts_fresh_without_forgetting_latest_job(client):
    """The index selector opens a new form while navigation keeps the latest run."""
    job_id = create_job(HEATMAP_JOB_PARAMS)
    with client.session_transaction() as browser_session:
        browser_session["latest_heatmap_job_id"] = job_id

    response = client.get("/?mode=heatmap")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="mode-tab-heatmap" class="mode-pill active"' in html
    assert 'id="heatmap-form-section" class="mode-panel"' in html
    assert 'id="heatmap-session-config" type="application/json">null' in html
    assert 'href="/" aria-current="page"' in html
    with client.session_transaction() as browser_session:
        assert browser_session["latest_heatmap_job_id"] == job_id


def test_heatmap_page_embeds_latest_session_job_for_resume(client):
    """The Heatmap destination should resume this browser's latest run."""
    job_id = create_job(HEATMAP_JOB_PARAMS)
    with client.session_transaction() as browser_session:
        browser_session["latest_heatmap_job_id"] = job_id

    response = client.get("/heatmap")

    assert response.status_code == 200
    assert f'"job_id": "{job_id}"'.encode() in response.data
    assert b'"username": "testuser"' in response.data


def test_heatmap_page_accepts_explicit_job_then_saves_it(client):
    """An explicit compatibility ID should seed later clean Heatmap visits."""
    job_id = create_job(HEATMAP_JOB_PARAMS)

    response = client.get(f"/heatmap?job_id={job_id}")

    assert response.status_code == 200
    assert f'"job_id": "{job_id}"'.encode() in response.data
    with client.session_transaction() as browser_session:
        assert browser_session["latest_heatmap_job_id"] == job_id


def test_home_page_heatmap_loading_uses_unframed_panel(client):
    """The heatmap loading state should not render as a Bootstrap card."""
    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    _, loading_tail = html.split('id="heatmap-loading"', 1)
    loading_markup, _ = loading_tail.split('id="heatmap-result"', 1)
    assert "wait-panel" in loading_markup
    # This used to assert animateTransform, using the SMIL as a stand-in for
    # "the pinwheel is here". WP-3 stripped the SMIL, so the stand-in is now
    # ss-pinwheel: the wrapper class shell.css animates. A missing wrapper is
    # silent -- the blades render and simply never move.
    assert "ss-pinwheel" in loading_markup
    assert "pinwheel-blade" in loading_markup
    assert 'id="heatmap-progress-track"' in loading_markup
    assert 'id="heatmap-progress-bar"' in loading_markup
    assert "card shadow" not in loading_markup
    assert "card-body" not in loading_markup


def test_validate_user_success(client):
    """Validate endpoint should return valid=true with registered_year."""
    mock_result = {"exists": True, "registered_year": 2016}
    with patch("scrobblescope.routes.run_async_in_thread", return_value=mock_result):
        response = client.get("/validate_user", query_string={"username": "flounder14"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["valid"] is True
    assert payload["registered_year"] == 2016


def test_validate_user_private_profile_is_rejected(client):
    """The index validator must turn Last.fm's private-profile verdict into a block."""
    with patch(
        "scrobblescope.routes.run_async_in_thread",
        side_effect=[{"exists": True, "registered_year": 2016}, False],
    ):
        response = client.get(
            "/validate_user", query_string={"username": "private_user"}
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["valid"] is False
    assert "private" in payload["message"].lower()
    assert "public" in payload["message"].lower()


def test_validate_user_missing_username(client):
    """Validate endpoint should reject empty usernames."""
    response = client.get("/validate_user")
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["valid"] is False


def test_results_complete_renders_no_matches_for_empty_results(client):
    """A completed job with empty results should render the no-matches UI."""
    job_id = create_job(
        {
            "username": "flounder14",
            "year": 2025,
            "sort_mode": "playcount",
            "release_scope": "same",
            "decade": None,
            "release_year": None,
            "min_plays": 10,
            "min_tracks": 3,
            "limit_results": "10",
        }
    )
    set_job_results(job_id, [])
    set_job_progress(
        job_id,
        progress=100,
        message="No albums found for the specified criteria.",
        error=False,
    )

    response = client.post("/results_complete", data={"job_id": job_id})
    assert response.status_code == 200
    assert b"No Albums Found" in response.data


# --- Error classification tests ---


def test_results_complete_error_with_error_code(client):
    """
    GIVEN a job with a retryable classified error
    WHEN /results_complete is POSTed
    THEN the error page should mention the issue is temporary.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_error(job_id, "spotify_unavailable")
    response = client.post("/results_complete", data={"job_id": job_id})
    assert response.status_code == 200
    assert b"Processing Error" in response.data
    assert b"temporary issue" in response.data


def test_progress_endpoint_returns_error_metadata(client):
    """
    GIVEN a job with a classified error
    WHEN the /progress endpoint is queried
    THEN the JSON should include error classification fields.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_error(job_id, "lastfm_rate_limited")
    response = client.get(f"/progress?job_id={job_id}")
    data = response.get_json()
    assert data["error"] is True
    assert data["error_code"] == "lastfm_rate_limited"
    assert data["retryable"] is True
    assert data["error_source"] == "lastfm"


def test_progress_endpoint_no_error_metadata_on_success(client):
    """
    GIVEN a job with normal (non-error) progress
    WHEN the /progress endpoint is queried
    THEN the JSON should NOT include error classification fields.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_progress(job_id, progress=50, message="Working...", error=False)
    response = client.get(f"/progress?job_id={job_id}")
    data = response.get_json()
    assert data["error"] is False
    assert "error_code" not in data
    assert "retryable" not in data


def test_progress_endpoint_returns_phase_payload(client):
    """
    GIVEN a job with a phase set
    WHEN the /progress endpoint is queried
    THEN the exact JSON phase payload should survive the route.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    phase = {
        "key": "lastfm_fetch",
        "label": "Fetching scrobbles",
        "unit": "page",
        "current": 23,
        "total": 102,
    }
    set_job_progress(job_id, progress=20, message="Fetching scrobbles", phase=phase)
    response = client.get(f"/progress?job_id={job_id}")
    data = response.get_json()
    assert data["phase"] == {
        "key": "lastfm_fetch",
        "label": "Fetching scrobbles",
        "unit": "page",
        "current": 23,
        "total": 102,
    }


def test_progress_endpoint_no_phase_when_unset_or_error(client):
    """
    GIVEN a missing job, error job, or job with phase cleared
    WHEN GET /progress is requested
    THEN the response payload must not have a 'phase' key.
    """
    # 1. Missing job ID (400)
    res_400 = client.get("/progress")
    assert "phase" not in res_400.get_json()

    # 2. Nonexistent job ID (404)
    res_404 = client.get("/progress?job_id=does_not_exist")
    assert "phase" not in res_404.get_json()

    # 3. Classified error on existing job
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_error(job_id, "lastfm_unavailable")
    res_err = client.get(f"/progress?job_id={job_id}")
    assert "phase" not in res_err.get_json()


# --- Route coverage tests ---


def test_progress_missing_job_id_returns_400(client):
    """
    GIVEN no job_id query parameter
    WHEN GET /progress is requested
    THEN it should return 400 with an error payload.
    """
    response = client.get("/progress")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] is True
    assert "Missing" in data["message"]


def test_progress_invalid_job_id_returns_404(client):
    """
    GIVEN a nonexistent job_id
    WHEN GET /progress is requested
    THEN it should return 404 with an error payload.
    """
    response = client.get("/progress?job_id=does_not_exist")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] is True


def test_results_loading_capacity_exceeded_returns_error(client):
    """
    GIVEN the active job concurrency limit is already reached
    WHEN POST /results_loading is submitted with valid form data
    THEN it should re-render the index page with a capacity error (no thread spawned).
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)
    assert response.status_code == 200
    assert INDEX_HEADLINE in response.data
    assert b"window.SCROBBLE" not in response.data
    assert b"Too many requests" in response.data


def test_results_loading_thread_start_failure_renders_error(client):
    """
    GIVEN start_job_thread raises (e.g. OS resource exhaustion after slot acquire)
    WHEN POST /results_loading is processed
    THEN the route renders the index page gracefully and leaves no orphan job in JOBS.

    Previously this test patched delete_job and only asserted assert_called_once(),
    which verified the mock was called but not which job_id was passed, and left the
    actual JOBS dict containing the orphaned entry unchecked.  This version drops the
    mock and asserts directly on JOBS state: any regression in the cleanup path
    (wrong job_id, missing call, wrong branch) will cause the assertion to fail.
    """
    with jobs_lock:
        jobs_before = set(JOBS.keys())

    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch(
            "scrobblescope.routes.start_job_thread",
            side_effect=OSError("too many threads"),
        ),
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert response.status_code == 200
    assert INDEX_HEADLINE in response.data
    assert b"window.SCROBBLE" not in response.data
    # The route must have called delete_job on the job it created: JOBS must be
    # back to its pre-request size with no orphan entry left behind.
    with jobs_lock:
        assert set(JOBS.keys()) == jobs_before


def test_results_loading_valid_post(client):
    """
    GIVEN valid form data for a search
    WHEN POST /results_loading is submitted
    THEN it should start the job and redirect to its canonical loading URL.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)
    assert response.status_code == 303
    assert re.fullmatch(r"/loading\?job_id=[^&]+", response.location)
    job_id = response.location.split("job_id=", 1)[1]
    with client.session_transaction() as browser_session:
        assert browser_session["latest_album_job_id"] == job_id
    # Verify start_job_thread was called with background_task as the target
    mock_start.assert_called_once()
    assert mock_start.call_args[0][0] is background_task


def test_results_loading_private_profile_does_not_start_a_job(client):
    """A direct album POST cannot bypass the index's private-profile guard."""
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            side_effect=[{"exists": True, "registered_year": None}, False],
        ),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert response.status_code == 200
    assert b"private" in response.data.lower()
    mock_start.assert_not_called()


def test_results_loading_missing_username(client):
    """
    GIVEN a POST to /results_loading without a username
    WHEN the form is submitted
    THEN it should re-render the index page with an error message.
    """
    response = client.post(
        "/results_loading",
        data={"year": "2025"},
    )
    assert response.status_code == 200
    # Should render the index form, NOT the loading page
    assert INDEX_HEADLINE in response.data
    assert b"window.SCROBBLE" not in response.data
    # Error message should be rendered in the alert block
    assert b"Username and year are required." in response.data


def test_results_loading_year_out_of_bounds(client):
    """
    GIVEN a POST to /results_loading with year before Last.fm existed
    WHEN the form is submitted
    THEN it should re-render the index page with an error message.
    """
    response = client.post(
        "/results_loading",
        data={"username": "flounder14", "year": "1999"},
    )
    assert response.status_code == 200
    # Should render the index form, NOT the loading page
    assert INDEX_HEADLINE in response.data
    assert b"window.SCROBBLE" not in response.data
    # Error message should be rendered in the alert block
    assert b"Year must be between" in response.data


def test_results_complete_missing_job_id(client):
    """
    GIVEN a POST to /results_complete without job_id
    WHEN the form is submitted
    THEN it should render the error page with a missing-job message.
    """
    response = client.post("/results_complete", data={})
    assert response.status_code == 200
    assert b"Missing Job Identifier" in response.data


def test_results_complete_expired_job(client):
    """
    GIVEN a POST to /results_complete with a nonexistent job_id
    WHEN the form is submitted
    THEN it should render the error page indicating results not found.
    """
    response = client.post("/results_complete", data={"job_id": "expired_or_fake"})
    assert response.status_code == 200
    assert b"Results Not Found" in response.data


def test_results_complete_with_results_renders_data(client):
    """
    GIVEN a completed job with album results
    WHEN POST /results_complete is submitted
    THEN it should render the results page with album data and the tojson bridge.
    """
    job_id = create_job(
        {
            "username": "flounder14",
            "year": 2025,
            "sort_mode": "playcount",
            "release_scope": "same",
            "decade": None,
            "release_year": None,
            "min_plays": 10,
            "min_tracks": 3,
            "limit_results": "all",
        }
    )
    set_job_results(
        job_id,
        [
            {
                "artist": "Kendrick Lamar",
                "album": "GNX",
                "play_count": 312,
                "play_time": "18h 42m",
                "play_time_seconds": 67320,
                "release_date": "2025-02-07",
                "album_image": "https://example.com/gnx.jpg",
                "spotify_id": "abc123",
            },
        ],
    )
    set_job_progress(job_id, progress=100, message="Done!", error=False)

    response = client.post("/results_complete", data={"job_id": job_id})
    assert response.status_code == 200
    assert b"window.APP_DATA" in response.data
    assert b"Kendrick Lamar" in response.data
    assert b"GNX" in response.data


def test_validate_user_too_long_username(client):
    """
    GIVEN a username longer than 64 characters
    WHEN GET /validate_user is requested
    THEN it should return 400 with a rejection message.
    """
    long_name = "a" * 65
    response = client.get("/validate_user", query_string={"username": long_name})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["valid"] is False
    assert "too long" in payload["message"]


def test_validate_user_not_found(client):
    """
    GIVEN a username that does not exist on Last.fm
    WHEN GET /validate_user is requested
    THEN it should return valid=false with a not-found message.
    """
    mock_result = {"exists": False, "registered_year": None}
    with patch("scrobblescope.routes.run_async_in_thread", return_value=mock_result):
        response = client.get(
            "/validate_user", query_string={"username": "ghost_user_xyz"}
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["valid"] is False
    assert "not found" in payload["message"].lower()


def test_unmatched_api_missing_job_id(client):
    """
    GIVEN no job_id query parameter
    WHEN GET /api/unmatched is requested
    THEN it should return 400 with an error.
    """
    response = client.get("/api/unmatched")
    assert response.status_code == 400
    data = response.get_json()
    assert "Missing" in data.get("error", "")


def test_unmatched_api_returns_data(client):
    """
    GIVEN a job with unmatched album data
    WHEN GET /api/unmatched is requested with that job_id
    THEN it should return the unmatched albums and count.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    add_job_unmatched(
        job_id,
        "artist::album_key",
        {
            "artist": "Radiohead",
            "album": "OK Computer",
            "reason": "Released in 1997, outside filter year",
        },
    )

    response = client.get(f"/api/unmatched?job_id={job_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 1
    assert "artist::album_key" in data["data"]


# --- Reset progress route tests ---


def test_reset_progress_missing_job_id_returns_400(client):
    """
    GIVEN a POST to /reset_progress without a job_id
    WHEN the request is submitted
    THEN it should return 400 with a missing-job message.
    """
    response = client.post("/reset_progress", data={})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["status"] == "error"
    assert "Missing job identifier" in payload["message"]


def test_reset_progress_nonexistent_job_returns_404(client):
    """
    GIVEN a POST to /reset_progress with a nonexistent job_id
    WHEN the request is submitted
    THEN it should return 404 with a job-not-found message.
    """
    response = client.post("/reset_progress", data={"job_id": "does_not_exist"})
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["status"] == "error"
    assert "Job not found" in payload["message"]


def test_reset_progress_success_resets_job_state(client):
    """
    GIVEN an existing job with progress, results, and unmatched data
    WHEN /reset_progress is called with that job_id
    THEN progress, results, and unmatched state should reset successfully.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_results(job_id, [{"artist": "A", "album": "B"}])
    add_job_unmatched(
        job_id,
        "a|b",
        {"artist": "A", "album": "B", "reason": "No Spotify match"},
    )
    set_job_progress(job_id, progress=88, message="Before reset", error=True)

    response = client.post("/reset_progress", data={"job_id": job_id})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"

    progress = get_job_progress(job_id)
    assert progress["progress"] == 0
    assert progress["message"] == "Reset successful"
    assert progress["error"] is False

    unmatched = get_job_unmatched(job_id)
    assert unmatched == {}
    with jobs_lock:
        assert JOBS[job_id]["results"] is None


def test_unmatched_view_missing_job_id_renders_error_page(client):
    """
    GIVEN a POST to /unmatched_view without job_id
    WHEN the request is submitted
    THEN it should render the error page with a missing-job message.
    """
    response = client.post("/unmatched_view", data={})
    assert response.status_code == 200
    assert b"Missing Job Identifier" in response.data


def test_unmatched_view_job_not_found_renders_error_page(client):
    """
    GIVEN a POST to /unmatched_view with an unknown job_id
    WHEN the request is submitted
    THEN it should render the expired-job error page.
    """
    response = client.post("/unmatched_view", data={"job_id": "no_such_job"})
    assert response.status_code == 200
    assert b"Job Not Found" in response.data
    assert b"expired" in response.data


def test_unmatched_view_success_renders_grouped_reasons(client):
    """
    GIVEN a job with unmatched albums split across reasons
    WHEN POST /unmatched_view is submitted
    THEN it should render the unmatched report with grouped reason sections.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    add_job_unmatched(
        job_id,
        "a|one",
        {"artist": "Artist A", "album": "Album One", "reason": "No Spotify match"},
    )
    add_job_unmatched(
        job_id,
        "b|two",
        {"artist": "Artist B", "album": "Album Two", "reason": "No Spotify match"},
    )
    add_job_unmatched(
        job_id,
        "c|three",
        {
            "artist": "Artist C",
            "album": "Album Three",
            "reason": "Outside filter year",
        },
    )

    response = client.post("/unmatched_view", data={"job_id": job_id})
    assert response.status_code == 200
    assert b"Albums That Didn't Match Your Filter" in response.data
    assert b"No Spotify match" in response.data
    assert b"Outside filter year" in response.data
    assert b"Artist A" in response.data
    assert b"Artist C" in response.data


def test_loading_page_uses_job_context_at_canonical_url(client):
    """GET /loading should rebuild the loading view from the stored job."""
    job_id = create_job(TEST_JOB_PARAMS)

    response = client.get(f"/loading?job_id={job_id}")

    assert response.status_code == 200
    assert b"window.SCROBBLE" in response.data
    assert b"testuser" in response.data
    assert b">Loading</a>" not in response.data
    assert b'id="progress-track"' in response.data
    assert b'id="progress-bar"' in response.data
    assert b"progress-bar-striped" not in response.data
    with client.session_transaction() as browser_session:
        assert browser_session["latest_album_job_id"] == job_id


def test_results_page_uses_job_context_at_canonical_url(client):
    """GET /results should render completed data without a form resubmission."""
    job_id = create_job(TEST_JOB_PARAMS)
    set_job_results(
        job_id,
        [
            {
                "artist": "Kendrick Lamar",
                "album": "GNX",
                "play_count": 312,
                "play_time": "18h 42m",
                "play_time_seconds": 67320,
                "release_date": "2025-02-07",
                "album_image": "https://example.com/gnx.jpg",
                "spotify_id": "abc123",
            }
        ],
    )
    set_job_progress(job_id, progress=100, message="Done!", error=False)

    response = client.get(f"/results?job_id={job_id}")

    assert response.status_code == 200
    assert b"Kendrick Lamar" in response.data
    assert b'aria-current="page">Results</a>' in response.data

    resumed = client.get("/results")
    assert resumed.status_code == 200
    assert b"Kendrick Lamar" in resumed.data


def test_unmatched_page_uses_job_context_at_canonical_url(client):
    """GET /unmatched should render the report and a stable results link."""
    job_id = create_job(TEST_JOB_PARAMS)
    add_job_unmatched(
        job_id,
        "a|one",
        {"artist": "Artist A", "album": "Album One", "reason": "No match"},
    )

    response = client.get(f"/unmatched?job_id={job_id}")

    assert response.status_code == 200
    assert b"Artist A" in response.data
    assert b'href="/results"' in response.data
    assert b'aria-current="page">Unmatched</a>' in response.data

    resumed = client.get("/unmatched")
    assert resumed.status_code == 200
    assert b"Artist A" in resumed.data


def test_unmatched_page_with_zero_rows_renders_a_clear_empty_state(client):
    """A zero unmatched count must not be described as a populated report."""
    job_id = create_job(TEST_JOB_PARAMS)

    response = client.get(f"/unmatched?job_id={job_id}")

    assert response.status_code == 200
    assert b"No unmatched albums to review" in response.data
    assert b"These albums were found in your" not in response.data
    assert b"Total albums that didn&#39;t match" not in response.data
    assert b'href="/results"' in response.data


def test_job_backed_navigation_pages_have_friendly_empty_states(client):
    """Direct navigation before a search should guide the user home."""
    results_response = client.get("/results")
    assert results_response.status_code == 200
    assert b'data-empty-state="results"' in results_response.data
    assert b'href="/"' in results_response.data

    heatmap_response = client.get("/heatmap")
    assert heatmap_response.status_code == 200
    assert b'data-empty-state="heatmap"' in heatmap_response.data
    assert b'href="/?mode=heatmap"' in heatmap_response.data

    unmatched_response = client.get("/unmatched")
    assert unmatched_response.status_code == 200
    assert b"You haven&#39;t filtered your scrobbles yet." in unmatched_response.data
    assert (
        b' href="/" class="btn btn-primary">Start from Home</a>'
        in unmatched_response.data
    )
    assert b'class="error-code"' not in unmatched_response.data


def test_expired_saved_album_job_returns_to_friendly_empty_state(client):
    """A stale browser-session pointer should not become a dead-end error."""
    with client.session_transaction() as browser_session:
        browser_session["latest_album_job_id"] = "expired-job"

    response = client.get("/results")

    assert response.status_code == 200
    assert b"previous results have expired" in response.data
    with client.session_transaction() as browser_session:
        assert "latest_album_job_id" not in browser_session


def test_expired_saved_heatmap_job_returns_to_dedicated_empty_state(client):
    """A stale heatmap pointer should clear and offer a fresh heatmap run."""
    with client.session_transaction() as browser_session:
        browser_session["latest_heatmap_job_id"] = "expired-job"

    response = client.get("/heatmap")

    assert response.status_code == 200
    assert b'data-empty-state="heatmap"' in response.data
    assert b'href="/?mode=heatmap"' in response.data
    with client.session_transaction() as browser_session:
        assert "latest_heatmap_job_id" not in browser_session


def test_app_404_handler_renders_error_template(client):
    """
    GIVEN a nonexistent URL
    WHEN it is requested
    THEN the blueprint 404 handler should render the friendly error template.
    """
    response = client.get("/definitely-not-a-route")
    assert response.status_code == 404
    assert b"Page not found" in response.data
    assert b"doesn&#39;t exist" in response.data


def test_app_500_handler_renders_error_template(client):
    """
    GIVEN an unhandled exception raised by a route
    WHEN the route is requested in testing with propagation disabled
    THEN the blueprint 500 handler should render the friendly error template.
    """
    application = client.application
    application.config["PROPAGATE_EXCEPTIONS"] = False

    @application.route("/_boom_for_test")
    def _boom_for_test():
        raise RuntimeError("boom")

    response = client.get("/_boom_for_test")
    assert response.status_code == 500
    assert b"Server Error" in response.data
    assert b"Please try again later" in response.data


# --- CSRF protection tests ---


def test_csrf_rejects_post_without_token(csrf_app_client):
    """
    GIVEN CSRF protection is active (default)
    WHEN a POST to /results_loading is submitted without a csrf_token
    THEN the response should be 400 (CSRF validation failure).
    """
    response = csrf_app_client.post("/results_loading", data=VALID_FORM_DATA)
    assert response.status_code == 400


def test_heatmap_csrf_failure_is_json_and_fresh_token_can_retry(csrf_app_client):
    """The AJAX heatmap form can recover without reloading a long-lived tab."""
    rejected = csrf_app_client.post("/heatmap_loading", data={"username": "testuser"})
    assert rejected.status_code == 400
    assert rejected.is_json
    assert rejected.get_json()["error_code"] == "csrf_invalid"

    token_response = csrf_app_client.get("/csrf-token")
    assert token_response.status_code == 200
    token = token_response.get_json()["csrf_token"]

    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.start_job_thread"),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
    ):
        accepted = csrf_app_client.post(
            "/heatmap_loading",
            data={"username": "testuser", "csrf_token": token},
        )

    assert accepted.status_code == 202
    assert accepted.get_json()["job_id"]


def test_csrf_accepts_post_with_valid_token(csrf_app_client):
    """
    GIVEN CSRF protection is active (default)
    WHEN a POST to /results_loading includes the CSRF token from the index page
    THEN the request should be accepted (not rejected as 400).
    """
    get_resp = csrf_app_client.get("/")
    token_match = re.search(rb'name="csrf_token" value="([^"]+)"', get_resp.data)
    assert token_match, "CSRF token not found in index page HTML"
    token = token_match.group(1).decode()

    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.start_job_thread"),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
    ):
        response = csrf_app_client.post(
            "/results_loading",
            data={**VALID_FORM_DATA, "csrf_token": token},
        )
    assert response.status_code == 303
    assert response.location.startswith("/loading?job_id=")


def test_csrf_rejects_results_complete_without_token(csrf_app_client):
    """
    GIVEN CSRF protection is active (default)
    WHEN POST /results_complete is submitted without a csrf_token
    THEN the response should be 400 (CSRF validation failure).
    """
    response = csrf_app_client.post("/results_complete", data={"job_id": "any"})
    assert response.status_code == 400


def test_csrf_rejects_unmatched_view_without_token(csrf_app_client):
    """
    GIVEN CSRF protection is active (default)
    WHEN POST /unmatched_view is submitted without a csrf_token
    THEN the response should be 400 (CSRF validation failure).
    """
    response = csrf_app_client.post("/unmatched_view", data={"job_id": "any"})
    assert response.status_code == 400


def test_csrf_rejects_reset_progress_without_token(csrf_app_client):
    """
    GIVEN CSRF protection is active (default)
    WHEN POST /reset_progress is submitted without a csrf_token form field or X-CSRFToken header
    THEN the response should be 400 (CSRF validation failure).
    """
    response = csrf_app_client.post("/reset_progress", data={"job_id": "any"})
    assert response.status_code == 400


# --- Registration year validation tests (WP-5) ---


def test_results_loading_year_below_registration_year_rejected(client):
    """
    GIVEN a user whose Last.fm registration year is 2016
    WHEN POST /results_loading is submitted with year=2015
    THEN the route re-renders index with an error referencing the registration year.
    """
    with patch(
        "scrobblescope.routes.run_async_in_thread",
        return_value={"exists": True, "registered_year": 2016},
    ):
        response = client.post(
            "/results_loading", data={**VALID_FORM_DATA, "year": "2015"}
        )
    assert response.status_code == 200
    assert INDEX_HEADLINE in response.data
    assert b"window.SCROBBLE" not in response.data
    assert b"2016" in response.data
    assert b"registration year" in response.data


def test_results_loading_year_at_registration_year_allowed(client):
    """
    GIVEN a user whose Last.fm registration year is 2016
    WHEN POST /results_loading is submitted with year=2016 (boundary)
    THEN the route should proceed to the loading page (not rejected).
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": 2016},
        ),
        patch("scrobblescope.routes.start_job_thread"),
    ):
        response = client.post(
            "/results_loading", data={**VALID_FORM_DATA, "year": "2016"}
        )
    assert response.status_code == 303
    assert response.location.startswith("/loading?job_id=")


def test_results_loading_registration_check_unavailable_proceeds(client):
    """
    GIVEN the registration year check raises an exception (Last.fm unavailable)
    WHEN POST /results_loading is submitted
    THEN the route proceeds to start the job rather than blocking the user.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            side_effect=Exception("network error"),
        ),
        patch("scrobblescope.routes.start_job_thread"),
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)
    assert response.status_code == 303
    assert response.location.startswith("/loading?job_id=")


def test_results_loading_no_registered_year_proceeds(client):
    """
    GIVEN the registration year check returns registered_year=None (unknown)
    WHEN POST /results_loading is submitted
    THEN the route proceeds normally without a year-comparison error.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.start_job_thread"),
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)
    assert response.status_code == 303
    assert response.location.startswith("/loading?job_id=")


def test_csrf_accepts_reset_progress_with_header_token(csrf_app_client):
    """
    GIVEN CSRF protection is active (default)
    WHEN POST /reset_progress is submitted with a valid X-CSRFToken header (XHR path)
    THEN the request should pass CSRF validation and return a success response.
    """
    get_resp = csrf_app_client.get("/")
    token_match = re.search(rb'name="csrf_token" value="([^"]+)"', get_resp.data)
    assert token_match, "CSRF token not found in index page HTML"
    token = token_match.group(1).decode()

    job_id = create_job(TEST_JOB_PARAMS)
    response = csrf_app_client.post(
        "/reset_progress",
        data={"job_id": job_id},
        headers={"X-CSRFToken": token},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"


# --- Heatmap route tests ---


def test_heatmap_loading_valid_username(client):
    """POST /heatmap_loading with a valid user returns 202 and a job_id."""
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": 2016},
        ),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/heatmap_loading", data={"username": "flounder14"})
    assert response.status_code == 202
    data = response.get_json()
    assert "job_id" in data
    assert "error" not in data
    with client.session_transaction() as browser_session:
        assert browser_session["latest_heatmap_job_id"] == data["job_id"]
    # Verify the thread target is heatmap_task, not background_task.
    from scrobblescope.heatmap import heatmap_task

    mock_start.assert_called_once()
    assert mock_start.call_args[0][0] is heatmap_task


def test_heatmap_loading_missing_username(client):
    """POST /heatmap_loading without a username returns 400."""
    response = client.post("/heatmap_loading", data={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] is True
    assert "required" in data["message"].lower()


def test_heatmap_loading_nonexistent_user(client):
    """POST /heatmap_loading for a user that doesn't exist returns 404."""
    with patch(
        "scrobblescope.routes.run_async_in_thread",
        return_value={"exists": False, "registered_year": None},
    ):
        response = client.post("/heatmap_loading", data={"username": "ghost_user"})
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] is True
    assert data["error_code"] == "user_not_found"
    assert data["retryable"] is False


def test_heatmap_loading_private_profile_does_not_start_a_job(client):
    """The Heatmap mode on the index shares the same public-profile gate."""
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            side_effect=[{"exists": True, "registered_year": None}, False],
        ),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/heatmap_loading", data={"username": "private_user"})

    assert response.status_code == 403
    data = response.get_json()
    assert data["error_code"] == "private_profile"
    assert "public" in data["message"].lower()
    mock_start.assert_not_called()


def test_heatmap_loading_no_job_slot(client):
    """POST /heatmap_loading when all slots are busy returns 429."""
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
    ):
        response = client.post("/heatmap_loading", data={"username": "flounder14"})
    assert response.status_code == 429
    data = response.get_json()
    assert data["error"] is True
    assert data["retryable"] is True


def test_heatmap_loading_thread_failure_cleans_up(client):
    """POST /heatmap_loading returns 500 and deletes orphan job on thread failure."""
    with jobs_lock:
        jobs_before = set(JOBS.keys())

    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch(
            "scrobblescope.routes.start_job_thread",
            side_effect=OSError("too many threads"),
        ),
    ):
        response = client.post("/heatmap_loading", data={"username": "flounder14"})
    assert response.status_code == 500
    data = response.get_json()
    assert data["error"] is True
    assert data["retryable"] is True
    # Orphan job must have been cleaned up.
    with jobs_lock:
        assert set(JOBS.keys()) == jobs_before


def test_heatmap_loading_user_check_unavailable(client):
    """POST /heatmap_loading returns 503 when the user check raises."""
    with patch(
        "scrobblescope.routes.run_async_in_thread",
        side_effect=Exception("network error"),
    ):
        response = client.post("/heatmap_loading", data={"username": "flounder14"})
    assert response.status_code == 503
    data = response.get_json()
    assert data["error"] is True
    assert data["retryable"] is True


def test_heatmap_loading_json_body(client):
    """POST /heatmap_loading accepts username from a JSON body (AJAX path)."""
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.start_job_thread"),
    ):
        response = client.post(
            "/heatmap_loading",
            json={"username": "flounder14"},
        )
    assert response.status_code == 202
    assert "job_id" in response.get_json()


def test_heatmap_data_completed_with_results(client):
    """GET /heatmap_data for a completed job returns 200 with daily_counts."""
    job_id = create_job(HEATMAP_JOB_PARAMS)
    heatmap_results = {
        "username": "testuser",
        "from_date": "2024-01-01",
        "to_date": "2025-01-01",
        "total_scrobbles": 500,
        "daily_counts": {"2024-06-15": 12, "2024-06-16": 3},
    }
    set_job_results(job_id, heatmap_results)
    set_job_progress(job_id, progress=100, message="Done!", error=False)

    response = client.get(f"/heatmap_data?job_id={job_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["ready"] is True
    assert data["daily_counts"]["2024-06-15"] == 12
    assert data["username"] == "testuser"


def test_heatmap_data_completed_with_error(client):
    """GET /heatmap_data for a failed job returns 200 with error details."""
    job_id = create_job(HEATMAP_JOB_PARAMS)
    set_job_error(job_id, "lastfm_rate_limited")

    response = client.get(f"/heatmap_data?job_id={job_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["error"] is True
    assert data["error_code"] == "lastfm_rate_limited"
    assert data["retryable"] is True
    # Must NOT return ready:true with empty results.
    assert "ready" not in data


def test_heatmap_data_missing_job_id(client):
    """GET /heatmap_data without job_id returns 400."""
    response = client.get("/heatmap_data")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] is True
    assert "Missing" in data["message"]


def test_heatmap_data_expired_job(client):
    """GET /heatmap_data for a nonexistent job returns 404."""
    response = client.get("/heatmap_data?job_id=does_not_exist")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] is True


def test_heatmap_data_still_processing(client):
    """GET /heatmap_data for an in-progress job returns 202 with ready=false."""
    job_id = create_job(HEATMAP_JOB_PARAMS)
    set_job_progress(job_id, progress=45, message="Fetching page 3...", error=False)

    response = client.get(f"/heatmap_data?job_id={job_id}")
    assert response.status_code == 202
    data = response.get_json()
    assert data["ready"] is False


def test_heatmap_data_error_with_empty_results(client):
    """Error jobs have results=[] via set_job_error; must return error, not ready.

    set_job_error() calls set_job_results(job_id, []), which is truthy for
    ``is not None``. The error check must come before the results check to
    avoid returning ``{"ready": true, ...}`` with an empty list.
    """
    job_id = create_job(HEATMAP_JOB_PARAMS)
    set_job_error(job_id, "no_scrobbles_in_range", username="testuser")

    response = client.get(f"/heatmap_data?job_id={job_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["error"] is True
    assert "ready" not in data


def test_csrf_rejects_heatmap_loading_without_token(csrf_app_client):
    """CSRF protection rejects POST /heatmap_loading without a token."""
    response = csrf_app_client.post("/heatmap_loading", data={"username": "flounder14"})
    assert response.status_code == 400


def test_heatmap_loading_whitespace_username(client):
    """POST /heatmap_loading with a whitespace-only username returns 400.

    Adversarial: the route strips the username before the empty check.  Without
    the strip() call a whitespace string would be truthy and bypass validation,
    reaching the Last.fm user-existence check with an invalid username instead
    of failing fast with a 400.
    """
    response = client.post("/heatmap_loading", data={"username": "   "})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] is True


# --- Helper unit tests ---


def test_filter_results_for_display_removes_zero_playtime_when_sorting_by_playtime():
    """Albums with play_time_seconds=0 must be dropped when sort_mode='playtime'.

    This is the key business rule: sorting by playtime with zero-duration albums
    would produce misleading rankings. The filter must fire, not pass through.
    """
    albums = [
        {"artist": "A", "album": "X", "play_time_seconds": 0},
        {"artist": "B", "album": "Y", "play_time_seconds": 3600},
        {"artist": "C", "album": "Z"},  # missing key -- treated as 0
    ]
    result = _filter_results_for_display(albums, "playtime")
    assert len(result) == 1
    assert result[0]["artist"] == "B"


def test_filter_results_for_display_keeps_zero_playtime_for_non_playtime_sort():
    """Albums without playtime data must NOT be filtered for non-playtime sort modes."""
    albums = [
        {"artist": "A", "album": "X", "play_time_seconds": 0},
        {"artist": "B", "album": "Y"},  # missing key entirely
    ]
    result = _filter_results_for_display(albums, "playcount")
    assert len(result) == 2


def test_group_unmatched_by_reason_uses_fallback_for_missing_reason_key():
    """Items without a 'reason' key must be grouped under 'Unknown reason'."""
    data = {
        "key_one": {"artist": "A", "album": "X"},  # no reason key
    }
    reasons, reason_counts = _group_unmatched_by_reason(data)
    assert "Unknown reason" in reasons
    assert len(reasons["Unknown reason"]) == 1
    assert reason_counts["Unknown reason"] == 1


# --- _get_filter_description branch tests ---


import pytest


@pytest.mark.parametrize(
    "release_scope, decade, release_year, listening_year, expected",
    [
        ("all", None, None, 2025, "all albums (no release year filter)"),
        ("same", None, None, 2025, "albums released in 2025"),
        ("previous", None, None, 2025, "albums released in 2024"),
        ("decade", "2010s", None, 2025, "albums released in the 2010s"),
        ("custom", None, 2019, 2025, "albums released in 2019"),
        # Fallback: decade scope without a decade value
        ("decade", None, None, 2025, "albums matching your criteria"),
        # Fallback: custom scope without a release_year value
        ("custom", None, None, 2025, "albums matching your criteria"),
        # Fallback: unrecognised scope
        ("unknown_scope", None, None, 2025, "albums matching your criteria"),
    ],
)
def test_get_filter_description(
    release_scope, decade, release_year, listening_year, expected
):
    """Each release_scope branch produces the correct user-facing string."""
    assert (
        _get_filter_description(release_scope, decade, release_year, listening_year)
        == expected
    )
