# tests/test_routes.py
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
from tests.helpers import TEST_JOB_PARAMS


def test_home_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid and contains key content.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Filter Your Album Scrobbles!" in response.data


def test_validate_user_success(client):
    """Validate endpoint should return valid=true with registered_year."""
    mock_result = {"exists": True, "registered_year": 2016}
    with patch("scrobblescope.routes.run_async_in_thread", return_value=mock_result):
        response = client.get("/validate_user", query_string={"username": "flounder14"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["valid"] is True
    assert payload["registered_year"] == 2016


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


def test_results_loading_valid_post(client):
    """
    GIVEN valid form data for a search
    WHEN POST /results_loading is submitted
    THEN it should create a thread targeting background_task and render the loading page.
    """
    with patch("scrobblescope.routes.threading.Thread") as mock_thread:
        mock_thread.return_value.start = lambda: None
        response = client.post(
            "/results_loading",
            data={
                "username": "flounder14",
                "year": "2025",
                "sort_by": "playcount",
                "release_scope": "same",
                "min_plays": "10",
                "min_tracks": "3",
                "limit_results": "all",
            },
        )
    assert response.status_code == 200
    assert b"window.SCROBBLE" in response.data
    assert b"flounder14" in response.data
    # Verify a thread was created targeting background_task
    mock_thread.assert_called_once()
    call_kwargs = mock_thread.call_args
    assert call_kwargs[1]["target"] is background_task
    assert call_kwargs[1]["daemon"] is True


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
    assert b"Filter Your Album Scrobbles!" in response.data
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
    assert b"Filter Your Album Scrobbles!" in response.data
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


def test_unmatched_endpoint_missing_job_id(client):
    """
    GIVEN no job_id query parameter
    WHEN GET /unmatched is requested
    THEN it should return 400 with an error.
    """
    response = client.get("/unmatched")
    assert response.status_code == 400
    data = response.get_json()
    assert "Missing" in data.get("error", "")


def test_unmatched_endpoint_returns_data(client):
    """
    GIVEN a job with unmatched album data
    WHEN GET /unmatched is requested with that job_id
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

    response = client.get(f"/unmatched?job_id={job_id}")
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
