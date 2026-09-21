"""The album job flow: loading, results, unmatched, and starting a new job.

See ``scrobblescope/routes/__init__.py`` for why cross-cutting dependencies
that live on the facade (``_check_user_exists``, ``_check_profile_is_public``,
``_get_validated_job_context``, ``_request_or_session_job_id``,
``acquire_job_slot``, ``start_job_thread``) are read through the live
``routes`` module reference (``_routes``) rather than imported directly.
"""

import logging
from datetime import datetime

from flask import jsonify, redirect, render_template, request, session, url_for

from scrobblescope import routes as _routes
from scrobblescope.orchestrator import background_task
from scrobblescope.repositories import (
    cleanup_expired_jobs,
    create_job,
    delete_job,
    reset_job_state,
    set_job_progress,
)
from scrobblescope.spotlight import select_spotlight_artists

bp = _routes.bp


def _extract_job_params(job_context):
    """Return a dict of job parameters stored in *job_context*."""
    params = job_context.get("params", {})
    return {
        "username": params.get("username"),
        "year": params.get("year"),
        "sort_mode": params.get("sort_mode"),
        "release_scope": params.get("release_scope", "same"),
        "decade": params.get("decade"),
        "release_year": params.get("release_year"),
        "min_plays": params.get("min_plays", 10),
        "min_tracks": params.get("min_tracks", 3),
        "limit_results": params.get("limit_results", "all"),
        "mode": params.get("mode", "album"),
    }


def _filter_results_for_display(results_data, sort_mode):
    """Remove albums with no play-time data when sorting by playtime.

    Albums without ``play_time_seconds`` would sort to zero and produce
    misleading playtime rankings. All albums are kept for every other
    sort mode.
    """
    return [
        album
        for album in results_data
        if album.get("play_time_seconds", 0) > 0 or sort_mode != "playtime"
    ]


def _get_filter_description(release_scope, decade, release_year, listening_year):
    """Generate a readable description of the active release-year filter."""
    if release_scope == "all":
        return "all albums (no release year filter)"
    elif release_scope == "same":
        return f"albums released in {listening_year}"
    elif release_scope == "previous":
        return f"albums released in {listening_year - 1}"
    elif release_scope == "decade" and decade:
        return f"albums released in the {decade}"
    elif release_scope == "custom" and release_year:
        return f"albums released in {release_year}"
    else:
        return "albums matching your criteria"


def _render_loading_page():
    """Render the canonical loading page for an existing job."""
    job_id, job_context, err = _routes._get_validated_job_context(
        missing_id_message="We could not identify your in-progress request.",
        expired_error="Job Not Found",
        expired_message="Your loading session has expired.",
        expired_details="Please start a new search.",
        session_key=_routes._LATEST_ALBUM_JOB,
        expected_mode="album",
    )
    if err:
        return err

    assert job_context is not None
    p = _extract_job_params(job_context)
    return render_template(
        "loading.html",
        job_id=job_id,
        username=p["username"],
        year=p["year"],
        sort_by=p["sort_mode"],
        release_scope=p["release_scope"],
        decade=p["decade"],
        release_year=p["release_year"],
        min_plays=p["min_plays"],
        min_tracks=p["min_tracks"],
        limit_results=p["limit_results"],
    )


@bp.route("/loading", methods=["GET"])
def loading_page():
    """Show the canonical loading URL for the current job."""
    return _render_loading_page()


@bp.route("/reset_progress", methods=["POST"])
def reset_progress():
    """Reset progress state for a specific job ID."""
    job_id = request.form.get("job_id")
    if not job_id:
        return jsonify({"status": "error", "message": "Missing job identifier."}), 400

    if not reset_job_state(job_id):
        return jsonify({"status": "error", "message": "Job not found."}), 404

    set_job_progress(job_id, message="Reset successful", error=False)
    return jsonify({"status": "success"})


def _render_results_page():
    """Render the results page for a completed job, or an error page on failure."""
    used_saved_job = request.method == "GET" and not request.values.get("job_id")
    if request.method == "GET" and not _routes._request_or_session_job_id(
        _routes._LATEST_ALBUM_JOB
    ):
        return render_template("results_empty.html")

    job_id, job_context, err = _routes._get_validated_job_context(
        missing_id_message="We could not identify your in-progress request.",
        expired_error="Results Not Found",
        expired_message="We couldn't find your results.",
        expired_details="The processing may have expired. Please try again.",
        session_key=_routes._LATEST_ALBUM_JOB,
        expected_mode="album",
    )
    if err:
        if used_saved_job:
            return render_template(
                "results_empty.html",
                empty_message=(
                    "Your previous results have expired. Run an album search "
                    "to build a new ranking."
                ),
            )
        return err

    # Type narrowing: after the err guard, job_context is guaranteed non-None.
    assert job_context is not None

    progress_payload = job_context["progress"]
    if progress_payload.get("error"):
        error_code = progress_payload.get("error_code")
        retryable = progress_payload.get("retryable", False)
        details = "Please try again or use different parameters."
        status_code = 500
        if retryable:
            details = "This appears to be a temporary issue. Please try again."
            status_code = 503
        if error_code == "user_not_found":
            details = "Please check the username and try again."
            status_code = 404
        return (
            render_template(
                "error.html",
                error="Processing Error",
                status_code=status_code,
                message=progress_payload.get("message", "An unknown error occurred"),
                details=details,
            ),
            status_code,
        )

    p = _extract_job_params(job_context)
    username = p["username"] or request.values.get("username")
    year = p["year"]
    if year is None:
        year = int(request.values.get("year", datetime.now().year))
    sort_mode = p["sort_mode"] or request.values.get("sort_by", "playcount")
    release_scope = p["release_scope"] or request.values.get("release_scope", "same")
    decade = p["decade"]
    release_year = p["release_year"]
    min_plays = p["min_plays"]
    min_tracks = p["min_tracks"]

    results_data = job_context.get("results")
    if results_data is None:
        return (
            render_template(
                "error.html",
                error="Results Still Processing",
                status_code=202,
                message="Your results are not ready yet.",
                details="Please wait on the loading page and try again.",
            ),
            202,
        )

    filtered_results = _filter_results_for_display(results_data, sort_mode)

    unmatched_count = len(job_context.get("unmatched", {}))
    has_durations = any(a.get("play_time_seconds", 0) > 0 for a in (results_data or []))

    if not filtered_results:
        filter_description = _get_filter_description(
            release_scope, decade, release_year, year
        )
        return render_template(
            "results.html",
            username=username,
            year=year,
            data=[],
            release_scope=release_scope,
            decade=decade,
            release_year=release_year,
            sort_by=sort_mode,
            min_plays=min_plays,
            min_tracks=min_tracks,
            no_matches=True,
            unmatched_count=unmatched_count,
            has_durations=has_durations,
            filter_description=filter_description,
            job_id=job_id,
        )

    # Passed so the release-check status line renders with the page. It sits
    # above the table, so creating it on the first poll reply would push every
    # row down -- the one move the owner's progressive-disclosure ruling
    # forbids. A skipped pass reserves nothing, because nothing will report.
    release_check = progress_payload.get("stats", {}).get("release_check")

    spotlight_artists = select_spotlight_artists(filtered_results, job_id)
    spotlight_artist = spotlight_artists[0] if spotlight_artists else {}
    top_artist_name = spotlight_artist.get("name", "")
    top_artist_scrobbles = spotlight_artist.get("scrobbles", 0)
    top_artist_album_count = spotlight_artist.get("album_count", 0)
    top_artist_play_time = spotlight_artist.get("play_time", "")
    top_artist_image = spotlight_artist.get("image_url", "")

    return render_template(
        "results.html",
        username=username,
        year=year,
        data=filtered_results,
        release_scope=release_scope,
        decade=decade,
        release_year=release_year,
        sort_by=sort_mode,
        min_plays=min_plays,
        min_tracks=min_tracks,
        no_matches=False,
        unmatched_count=unmatched_count,
        has_durations=has_durations,
        job_id=job_id,
        top_artist_name=top_artist_name,
        top_artist_scrobbles=top_artist_scrobbles,
        top_artist_album_count=top_artist_album_count,
        top_artist_play_time=top_artist_play_time,
        top_artist_image=top_artist_image,
        spotlight_artists=spotlight_artists,
        release_check=release_check,
    )


@bp.route("/results", methods=["GET"])
def results():
    """Show completed results at their canonical URL."""
    return _render_results_page()


@bp.route("/results_complete", methods=["POST"])
def results_complete():
    """Keep the legacy completion POST working while callers move to GET."""
    return _render_results_page()


def _render_unmatched_page():
    """Render the unmatched-album report for an existing job."""
    used_saved_job = request.method == "GET" and not request.values.get("job_id")
    if request.method == "GET" and not _routes._request_or_session_job_id(
        _routes._LATEST_ALBUM_JOB
    ):
        return render_template("unmatched_empty.html")

    job_id, job_context, err = _routes._get_validated_job_context(
        missing_id_message="We could not find unmatched albums without a valid job ID.",
        expired_error="Job Not Found",
        expired_message="Your unmatched album data has expired.",
        expired_details="Please run a new search.",
        session_key=_routes._LATEST_ALBUM_JOB,
        expected_mode="album",
    )
    if err:
        if used_saved_job:
            return render_template(
                "unmatched_empty.html",
                empty_message=(
                    "Your previous results have expired. Run a new album search."
                ),
            )
        return err

    # Type narrowing: after the err guard, job_context is guaranteed non-None.
    assert job_context is not None

    p = _extract_job_params(job_context)
    username = p["username"]
    year = p["year"]
    release_scope = p["release_scope"]
    decade = p["decade"]
    release_year = p["release_year"]
    min_plays = p["min_plays"]
    min_tracks = p["min_tracks"]

    filter_desc = _get_filter_description(
        release_scope, decade, release_year, int(year)
    )

    unmatched_data = dict(job_context.get("unmatched", {}))
    reasons, reason_counts, reason_metadata = _routes.group_unmatched_albums(
        unmatched_data
    )

    return render_template(
        "unmatched.html",
        username=username,
        year=year,
        filter_desc=filter_desc,
        unmatched_data=unmatched_data,
        reasons=reasons,
        reason_counts=reason_counts,
        reason_metadata=reason_metadata,
        total_count=len(unmatched_data),
        min_plays=min_plays,
        min_tracks=min_tracks,
        job_id=job_id,
    )


@bp.route("/unmatched", methods=["GET"])
def unmatched_page():
    """Show the unmatched-album report at its canonical URL."""
    return _render_unmatched_page()


@bp.route("/unmatched_view", methods=["POST"])
def unmatched_view():
    """Keep the legacy unmatched POST working while callers move to GET."""
    return _render_unmatched_page()


@bp.route("/results_loading", methods=["POST"])
def results_loading():
    """
    Handles form submission, performs the main Last.fm fetch,
    and prepares the session for lazy loading.
    """
    username = request.form.get("username")
    year = request.form.get("year")
    sort_mode = request.form.get("sort_by", "playcount")
    release_scope = request.form.get("release_scope", "same")
    decade = request.form.get("decade") if release_scope == "decade" else None
    release_year = (
        request.form.get("release_year") if release_scope == "custom" else None
    )
    min_plays = request.form.get("min_plays", "10")
    min_tracks = request.form.get("min_tracks", "3")
    limit_results = request.form.get("limit_results", "all")

    if not username or not year:
        logging.warning("Missing username or year in form submission.")
        return render_template("index.html", error="Username and year are required.")

    try:
        year = int(year)
        if release_year:
            release_year = int(release_year)
        min_plays = int(min_plays)
        min_tracks = int(min_tracks)
    except ValueError:
        logging.warning("Invalid year format.")
        return render_template("index.html", error="Year must be a valid number.")

    current_year = datetime.now().year
    if year < 2002 or year > current_year:
        return render_template(
            "index.html", error=f"Year must be between 2002 and {current_year}."
        )

    try:
        user_info = _routes._check_user_exists(username)
        if not _routes._check_profile_is_public(username):
            return render_template("index.html", error=_routes._PRIVATE_PROFILE_MESSAGE)
        registered_year = user_info.get("registered_year")
        if registered_year and year < registered_year:
            return render_template(
                "index.html",
                error=(
                    f"Year {year} is before your Last.fm registration year"
                    f" ({registered_year}). Please choose {registered_year} or later."
                ),
            )
    # The registration-year hint is optional; the search proceeds without it.
    except Exception as exc:  # noqa: BLE001
        logging.warning(
            "Registration year check failed for %s; proceeding without it: %s: %s",
            username,
            type(exc).__name__,
            exc,
        )

    cleanup_expired_jobs()

    if not _routes.acquire_job_slot():
        return render_template(
            "index.html",
            error="Too many requests in progress. Please try again in a moment.",
        )

    params = {
        "username": username,
        "year": year,
        "sort_mode": sort_mode,
        "release_scope": release_scope,
        "decade": decade,
        "release_year": release_year,
        "min_plays": min_plays,
        "min_tracks": min_tracks,
        "limit_results": limit_results,
    }

    job_id = create_job(params)

    try:
        _routes.start_job_thread(
            background_task,
            args=(
                job_id,
                username,
                year,
                sort_mode,
                release_scope,
                decade,
                release_year,
                min_plays,
                min_tracks,
                limit_results,
            ),
        )
    except Exception:
        logging.exception("Failed to start background task thread")
        delete_job(job_id)
        return render_template(
            "index.html",
            error="Failed to start processing. Please try again.",
        )

    session[_routes._LATEST_ALBUM_JOB] = job_id

    return redirect(url_for(".loading_page", job_id=job_id), code=303)
