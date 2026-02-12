# tests/test_app.py
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Imports from your application
from app import (
    JOB_TTL_SECONDS,
    JOBS,
    _extract_registered_year,
    _fetch_and_process,
    add_job_unmatched,
    app,
    background_task,
    check_user_exists,
    cleanup_expired_jobs,
    create_job,
    fetch_recent_tracks_page_async,
    fetch_spotify_album_details_batch,
    get_job_progress,
    get_job_unmatched,
    jobs_lock,
    normalize_name,
    normalize_track_name,
    search_for_spotify_album_id,
    set_job_error,
    set_job_progress,
    set_job_results,
    set_job_stat,
)


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid and contains key content.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Filter Your Album Scrobbles!" in response.data


def test_normalize_name_simple():
    """
    GIVEN an artist and album with common suffixes and punctuation
    WHEN normalize_name is called
    THEN check that the names are correctly stripped and lowercased.
    """
    artist, album = normalize_name("The Beatles.", "Let It Be (Deluxe Edition)")
    assert artist == "the beatles"
    assert album == "let it be"


@pytest.mark.asyncio
async def test_check_user_exists_success():
    """
    GIVEN a username that exists
    WHEN check_user_exists is called
    THEN it should return exists=True with a registered_year.
    """
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "user": {
                "name": "testuser",
                "registered": {"unixtime": "1451606400", "#text": "2016-01-01 00:00"},
            }
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await check_user_exists("any_user")
        assert result["exists"] is True
        assert result["registered_year"] == 2016


@pytest.mark.asyncio
async def test_check_user_does_not_exist():
    """
    GIVEN a username that does NOT exist
    WHEN check_user_exists is called
    THEN it should return exists=False.
    """
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await check_user_exists("nonexistent_user")
        assert result["exists"] is False
        assert result["registered_year"] is None


def test_validate_user_success(client):
    """Validate endpoint should return valid=true with registered_year."""
    mock_result = {"exists": True, "registered_year": 2016}
    with patch("app.run_async_in_thread", return_value=mock_result):
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

_TEST_JOB_PARAMS = {
    "username": "testuser",
    "year": 2025,
    "sort_mode": "playcount",
    "release_scope": "same",
    "decade": None,
    "release_year": None,
    "min_plays": 10,
    "min_tracks": 3,
    "limit_results": "all",
}


def test_set_job_error_sets_classified_fields():
    """
    GIVEN a job
    WHEN set_job_error is called with a retryable error code
    THEN the progress payload should contain error_code, error_source, and retryable fields.
    """
    job_id = create_job(_TEST_JOB_PARAMS)
    set_job_error(job_id, "lastfm_unavailable")
    progress = get_job_progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "lastfm_unavailable"
    assert progress["error_source"] == "lastfm"
    assert progress["retryable"] is True
    assert progress["progress"] == 100


def test_set_job_error_user_not_found_not_retryable():
    """
    GIVEN a job
    WHEN set_job_error is called with user_not_found and a username
    THEN the error should not be retryable and the message should include the username.
    """
    job_id = create_job(_TEST_JOB_PARAMS)
    set_job_error(job_id, "user_not_found", username="ghost")
    progress = get_job_progress(job_id)
    assert progress["retryable"] is False
    assert "ghost" in progress["message"]
    assert progress["error_code"] == "user_not_found"


def test_results_complete_error_with_error_code(client):
    """
    GIVEN a job with a retryable classified error
    WHEN /results_complete is POSTed
    THEN the error page should mention the issue is temporary.
    """
    job_id = create_job(_TEST_JOB_PARAMS)
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
    job_id = create_job(_TEST_JOB_PARAMS)
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
    job_id = create_job(_TEST_JOB_PARAMS)
    set_job_progress(job_id, progress=50, message="Working...", error=False)
    response = client.get(f"/progress?job_id={job_id}")
    data = response.get_json()
    assert data["error"] is False
    assert "error_code" not in data
    assert "retryable" not in data


# --- Job lifecycle tests ---


def test_create_job_returns_unique_ids():
    """
    GIVEN two calls to create_job
    WHEN both use identical params
    THEN each should return a different job ID.
    """
    id_a = create_job(_TEST_JOB_PARAMS)
    id_b = create_job(_TEST_JOB_PARAMS)
    assert id_a != id_b


def test_job_isolation_separate_progress():
    """
    GIVEN two independent jobs
    WHEN progress is updated on one
    THEN the other job's progress should be unaffected.
    """
    id_a = create_job(_TEST_JOB_PARAMS)
    id_b = create_job(_TEST_JOB_PARAMS)

    set_job_progress(id_a, progress=75, message="Almost done", error=False)
    set_job_progress(id_b, progress=10, message="Starting", error=False)

    progress_a = get_job_progress(id_a)
    progress_b = get_job_progress(id_b)

    assert progress_a["progress"] == 75
    assert progress_a["message"] == "Almost done"
    assert progress_b["progress"] == 10
    assert progress_b["message"] == "Starting"


def test_set_job_progress_missing_job_returns_false():
    """
    GIVEN a nonexistent job ID
    WHEN set_job_progress is called
    THEN it should return False.
    """
    result = set_job_progress("nonexistent_job_id", progress=50, message="test")
    assert result is False


def test_set_job_stat_stores_and_retrieves():
    """
    GIVEN a job
    WHEN set_job_stat is called with a key/value
    THEN get_job_progress should include that stat.
    """
    job_id = create_job(_TEST_JOB_PARAMS)
    set_job_stat(job_id, "scrobbles_fetched", 1234)
    set_job_stat(job_id, "albums_found", 42)

    progress = get_job_progress(job_id)
    assert progress["stats"]["scrobbles_fetched"] == 1234
    assert progress["stats"]["albums_found"] == 42


def test_expired_job_cleanup():
    """
    GIVEN a job whose timestamps are older than JOB_TTL_SECONDS
    WHEN cleanup_expired_jobs is called
    THEN the expired job should be removed.
    """
    job_id = create_job(_TEST_JOB_PARAMS)

    # Manually backdate the job timestamps so it looks expired
    expired_time = time.time() - JOB_TTL_SECONDS - 60
    with jobs_lock:
        JOBS[job_id]["created_at"] = expired_time
        JOBS[job_id]["updated_at"] = expired_time

    cleanup_expired_jobs()

    assert get_job_progress(job_id) is None


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
    with patch("app.threading.Thread") as mock_thread:
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
    with patch("app.run_async_in_thread", return_value=mock_result):
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
    job_id = create_job(_TEST_JOB_PARAMS)
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


# --- Normalization tests ---


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


# --- Registration year extraction tests ---


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


# --- Background task structural tests ---


def test_background_task_runs_single_event_loop():
    """
    GIVEN a job ID and valid parameters
    WHEN background_task is called
    THEN it should create one event loop, run _fetch_and_process via that loop,
    and NOT spawn a second thread (Batch 3 regression guard).
    """
    job_id = create_job(_TEST_JOB_PARAMS)

    with patch("app._fetch_and_process", new_callable=AsyncMock) as mock_fp, patch(
        "app.threading.Thread"
    ) as mock_inner_thread:
        background_task(
            job_id,
            "flounder14",
            2025,
            "playcount",
            "same",
        )

        # _fetch_and_process should have been awaited exactly once
        mock_fp.assert_awaited_once()
        call_args = mock_fp.call_args
        assert call_args[0][0] == job_id
        assert call_args[0][1] == "flounder14"

        # No inner thread should have been created (the Batch 3 fix)
        mock_inner_thread.assert_not_called()


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
    job_id = create_job(_TEST_JOB_PARAMS)
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


# --- Service-level retry/error mapping tests ---


class _NoopAsyncContext:
    """A no-op async context manager for patching rate limiters in tests."""

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _make_response_context(response):
    """Build an async context manager whose __aenter__ returns response."""
    cm = AsyncMock()
    cm.__aenter__.return_value = response
    return cm


@pytest.mark.asyncio
async def test_fetch_recent_tracks_page_retries_429_then_succeeds():
    """
    GIVEN Last.fm page fetch receives a 429 then a 200 response
    WHEN fetch_recent_tracks_page_async runs
    THEN it should retry once and return the successful payload.
    """
    session = MagicMock()

    resp_429 = AsyncMock()
    resp_429.status = 429
    resp_429.headers = {"Retry-After": "1"}

    payload = {"recenttracks": {"track": [], "@attr": {"totalPages": "1"}}}
    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(return_value=payload)

    session.get.side_effect = [
        _make_response_context(resp_429),
        _make_response_context(resp_200),
    ]

    with patch("app.get_cached_response", return_value=None), patch(
        "app.get_lastfm_limiter", return_value=_NoopAsyncContext()
    ), patch("app.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await fetch_recent_tracks_page_async(
            session, "flounder14", 1, 2, page=1, retries=3
        )

    assert result == payload
    assert session.get.call_count == 2
    assert mock_sleep.await_count >= 1


@pytest.mark.asyncio
async def test_fetch_recent_tracks_page_404_raises_user_not_found():
    """
    GIVEN Last.fm responds with 404 for a page fetch
    WHEN fetch_recent_tracks_page_async runs
    THEN it should raise ValueError for user-not-found classification.
    """
    session = MagicMock()
    resp_404 = AsyncMock()
    resp_404.status = 404
    session.get.return_value = _make_response_context(resp_404)

    with patch("app.get_cached_response", return_value=None), patch(
        "app.get_lastfm_limiter", return_value=_NoopAsyncContext()
    ):
        with pytest.raises(ValueError, match="not found"):
            await fetch_recent_tracks_page_async(
                session, "ghost_user_xyz", 1, 2, page=1, retries=1
            )


@pytest.mark.asyncio
async def test_search_for_spotify_album_id_retries_429_then_returns_id():
    """
    GIVEN Spotify search returns 429 and then a valid 200 payload
    WHEN search_for_spotify_album_id runs
    THEN it should retry and return the matched album ID.
    """
    session = MagicMock()

    resp_429 = AsyncMock()
    resp_429.status = 429
    resp_429.headers = {"Retry-After": "1"}

    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(
        return_value={"albums": {"items": [{"id": "spotify_album_123"}]}}
    )

    session.get.side_effect = [
        _make_response_context(resp_429),
        _make_response_context(resp_200),
    ]

    with patch("app.get_spotify_limiter", return_value=_NoopAsyncContext()), patch(
        "app.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        result = await search_for_spotify_album_id(session, "Artist", "Album", "token")

    assert result == "spotify_album_123"
    assert session.get.call_count == 2
    assert mock_sleep.await_count >= 1


@pytest.mark.asyncio
async def test_fetch_spotify_album_details_batch_retries_429_then_succeeds():
    """
    GIVEN Spotify album-details batch fetch returns 429 then 200
    WHEN fetch_spotify_album_details_batch runs
    THEN it should retry and return album details keyed by Spotify ID.
    """
    session = MagicMock()

    resp_429 = AsyncMock()
    resp_429.status = 429
    resp_429.headers = {"Retry-After": "1"}

    resp_200 = AsyncMock()
    resp_200.status = 200
    resp_200.json = AsyncMock(
        return_value={"albums": [{"id": "id_1", "name": "Album One"}]}
    )

    session.get.side_effect = [
        _make_response_context(resp_429),
        _make_response_context(resp_200),
    ]

    with patch("app.get_spotify_limiter", return_value=_NoopAsyncContext()), patch(
        "app.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        result = await fetch_spotify_album_details_batch(
            session, ["id_1"], "token", retries=2
        )

    assert result == {"id_1": {"id": "id_1", "name": "Album One"}}
    assert session.get.call_count == 2
    assert mock_sleep.await_count >= 1


@pytest.mark.asyncio
async def test_fetch_spotify_album_details_batch_non_200_returns_empty_dict():
    """
    GIVEN Spotify album-details batch fetch returns a non-200 non-429 status
    WHEN fetch_spotify_album_details_batch runs
    THEN it should return an empty dict without retry sleep.
    """
    session = MagicMock()

    resp_500 = AsyncMock()
    resp_500.status = 500
    resp_500.text = AsyncMock(return_value="upstream failure")
    session.get.return_value = _make_response_context(resp_500)

    with patch("app.get_spotify_limiter", return_value=_NoopAsyncContext()), patch(
        "app.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        result = await fetch_spotify_album_details_batch(
            session, ["id_1"], "token", retries=2
        )

    assert result == {}
    assert mock_sleep.await_count == 0
