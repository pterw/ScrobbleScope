import logging
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from scrobblescope.lastfm import check_user_exists
from scrobblescope.orchestrator import background_task
from scrobblescope.repositories import (
    cleanup_expired_jobs,
    create_job,
    delete_job,
    get_job_context,
    get_job_progress,
    get_job_unmatched,
    reset_job_state,
    set_job_progress,
)
from scrobblescope.utils import run_async_in_thread
from scrobblescope.worker import acquire_job_slot, start_job_thread

bp = Blueprint("main", __name__)


def _check_user_exists(username):
    """Call check_user_exists in a dedicated async thread."""

    async def _check():
        return await check_user_exists(username)

    return run_async_in_thread(_check)


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


def _group_unmatched_by_reason(unmatched_data):
    """Group unmatched-album items by their ``reason`` string.

    Returns a tuple of (reasons, reason_counts) where *reasons* maps each
    reason string to a list of items and *reason_counts* maps each reason
    string to the length of that list.
    """
    reasons = {}
    for item in unmatched_data.values():
        reason = item.get("reason", "Unknown reason")
        reasons.setdefault(reason, []).append(item)
    reason_counts = {reason: len(albums) for reason, albums in reasons.items()}
    return reasons, reason_counts


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


def _get_validated_job_context(
    missing_id_message, expired_error, expired_message, expired_details
):
    """Validate ``job_id`` from the current request form.

    Returns ``(job_id, job_context, None)`` on success, or
    ``(None, None, error_response)`` when validation fails.
    """
    job_id = request.form.get("job_id")
    if not job_id:
        return (
            None,
            None,
            render_template(
                "error.html",
                error="Missing Job Identifier",
                message=missing_id_message,
                details="Please start a new search.",
            ),
        )

    job_context = get_job_context(job_id)
    if not job_context:
        logging.warning(f"Job context not found for {job_id}")
        return (
            None,
            None,
            render_template(
                "error.html",
                error=expired_error,
                message=expired_message,
                details=expired_details,
            ),
        )

    return job_id, job_context, None


@bp.app_context_processor
def inject_current_year():
    """Inject ``current_year`` into all Jinja2 templates."""
    return {"current_year": datetime.now().year}


@bp.route("/", methods=["GET"])
def home():
    """Serve the home page"""
    logging.info("Serving index.html as the homepage.")
    return render_template("index.html")


@bp.route("/validate_user", methods=["GET"])
def validate_user():
    """Validate a Last.fm username for client-side blur checks."""
    username = (request.args.get("username") or "").strip()
    if not username:
        return jsonify({"valid": False, "message": "Username is required."}), 400
    if len(username) > 64:
        return jsonify({"valid": False, "message": "Username is too long."}), 400

    try:
        result = _check_user_exists(username)
    except Exception:
        logging.exception("Username validation failed")
        return (
            jsonify(
                {
                    "valid": False,
                    "message": "Validation service unavailable. Try again.",
                }
            ),
            503,
        )

    if result["exists"]:
        payload = {"valid": True, "message": "Username found."}
        if result.get("registered_year"):
            payload["registered_year"] = result["registered_year"]
        return jsonify(payload)
    return jsonify({"valid": False, "message": "Username not found on Last.fm."})


@bp.route("/progress")
def progress():
    """Return current progress for a specific job ID."""
    job_id = request.args.get("job_id")
    if not job_id:
        return (
            jsonify(
                {
                    "progress": 100,
                    "message": "Missing job identifier.",
                    "error": True,
                    "stats": {},
                }
            ),
            400,
        )

    progress_payload = get_job_progress(job_id)
    if progress_payload is None:
        return (
            jsonify(
                {
                    "progress": 100,
                    "message": "Job not found or expired.",
                    "error": True,
                    "stats": {},
                }
            ),
            404,
        )

    return jsonify(progress_payload)


@bp.route("/unmatched")
def unmatched():
    """Return unmatched albums for a specific job ID."""
    job_id = request.args.get("job_id")
    if not job_id:
        return (
            jsonify({"count": 0, "data": {}, "error": "Missing job identifier."}),
            400,
        )

    unmatched_data = get_job_unmatched(job_id)
    if unmatched_data is None:
        return jsonify({"count": 0, "data": {}, "error": "Job not found."}), 404

    return jsonify({"count": len(unmatched_data), "data": unmatched_data})


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


@bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with a nice error page"""
    return (
        render_template(
            "error.html",
            error="Page not found",
            message="The page you're looking for doesn't exist.",
        ),
        404,
    )


@bp.app_errorhandler(500)
def internal_error(e):
    """Handle 500 errors with a nice error page"""
    return (
        render_template(
            "error.html",
            error="Server Error",
            message="Something went wrong on our end. Please try again later.",
        ),
        500,
    )


@bp.route("/results_complete", methods=["POST"])
def results_complete():
    """Render the results page for a completed job, or an error page on failure."""
    job_id, job_context, err = _get_validated_job_context(
        missing_id_message="We could not identify your in-progress request.",
        expired_error="Results Not Found",
        expired_message="We couldn't find your results.",
        expired_details="The processing may have expired. Please try again.",
    )
    if err:
        return err

    # Type narrowing: after the err guard, job_context is guaranteed non-None.
    assert job_context is not None

    progress_payload = job_context["progress"]
    if progress_payload.get("error"):
        error_code = progress_payload.get("error_code")
        retryable = progress_payload.get("retryable", False)
        details = "Please try again or use different parameters."
        if retryable:
            details = "This appears to be a temporary issue. Please try again."
        if error_code == "user_not_found":
            details = "Please check the username and try again."
        return render_template(
            "error.html",
            error="Processing Error",
            message=progress_payload.get("message", "An unknown error occurred"),
            details=details,
        )

    p = _extract_job_params(job_context)
    username = p["username"] or request.form.get("username")
    year = p["year"]
    if year is None:
        year = int(request.form.get("year", datetime.now().year))
    sort_mode = p["sort_mode"] or request.form.get("sort_by", "playcount")
    release_scope = p["release_scope"] or request.form.get("release_scope", "same")
    decade = p["decade"]
    release_year = p["release_year"]
    min_plays = p["min_plays"]
    min_tracks = p["min_tracks"]

    results_data = job_context.get("results")
    if results_data is None:
        return render_template(
            "error.html",
            error="Results Still Processing",
            message="Your results are not ready yet.",
            details="Please wait on the loading page and try again.",
        )

    filtered_results = _filter_results_for_display(results_data, sort_mode)

    if not filtered_results:
        unmatched_count = len(job_context.get("unmatched", {}))
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
            filter_description=filter_description,
            job_id=job_id,
        )

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
        job_id=job_id,
    )


@bp.route("/unmatched_view", methods=["POST"])
def unmatched_view():
    """Show a dedicated page of unmatched albums that didn't match the filters."""
    job_id, job_context, err = _get_validated_job_context(
        missing_id_message="We could not find unmatched albums without a valid job ID.",
        expired_error="Job Not Found",
        expired_message="Your unmatched album data has expired.",
        expired_details="Please run a new search.",
    )
    if err:
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
    reasons, reason_counts = _group_unmatched_by_reason(unmatched_data)

    return render_template(
        "unmatched.html",
        username=username,
        year=year,
        filter_desc=filter_desc,
        unmatched_data=unmatched_data,
        reasons=reasons,
        reason_counts=reason_counts,
        total_count=len(unmatched_data),
        min_plays=min_plays,
        min_tracks=min_tracks,
    )


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
        user_info = _check_user_exists(username)
        registered_year = user_info.get("registered_year")
        if registered_year and year < registered_year:
            return render_template(
                "index.html",
                error=(
                    f"Year {year} is before your Last.fm registration year"
                    f" ({registered_year}). Please choose {registered_year} or later."
                ),
            )
    except Exception:
        logging.warning(
            "Registration year check failed for %s; proceeding without it", username
        )

    cleanup_expired_jobs()

    if not acquire_job_slot():
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
        start_job_thread(
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

    return render_template(
        "loading.html",
        job_id=job_id,
        username=username,
        year=year,
        sort_by=sort_mode,
        release_scope=release_scope,
        decade=decade,
        release_year=release_year,
        min_plays=min_plays,
        min_tracks=min_tracks,
        limit_results=limit_results,
    )
