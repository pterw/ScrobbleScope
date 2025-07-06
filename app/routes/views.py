# app/routes/views.py

import logging  # Added missing import
import threading

from flask import (  # jsonify not strictly needed for these routes but can stay
    Blueprint,
    jsonify,
    render_template,
    request,
)

# Import from state, tasks, and utils modules
from app.state import (
    UNMATCHED,
    completed_results,
    current_progress,
    progress_lock,
    unmatched_lock,
)
from app.tasks import background_task
from app.utils import (  # Ensure all needed utils are imported
    format_seconds,
    get_filter_description,
    normalize_name,
    normalize_track_name,
)

views_bp = Blueprint("views", __name__)


@views_bp.route("/results_complete", methods=["POST"])
def results_complete():
    username = request.form.get("username")
    year = int(request.form.get("year"))
    sort_mode = request.form.get("sort_by", "playcount")
    release_scope = request.form.get("release_scope", "same")
    decade = request.form.get("decade")
    release_year = request.form.get("release_year")
    min_plays = request.form.get("min_plays", "10")
    min_tracks = request.form.get("min_tracks", "3")
    if release_year:
        release_year = int(release_year)
    min_plays = int(min_plays)
    min_tracks = int(min_tracks)

    logging.info(f"Processing results for user {username} in year {year} with filters")

    cache_key = (
        username,
        year,
        sort_mode,
        release_scope,
        decade,
        release_year,
        min_plays,
        min_tracks,
    )

    with progress_lock:
        error = current_progress.get("error", False)
        if error:
            return render_template(
                "error.html",
                error="Processing Error",
                message=current_progress.get("message", "An unknown error occurred"),
                details="Please try again or try different parameters.",
            )
        if cache_key not in completed_results:
            logging.warning("No cached results found. Showing error page.")
            return render_template(
                "error.html",
                error="Results Not Found",
                message="We couldn't find your results.",
                details="The processing may have timed out or failed. Please try again.",
            )

    results_data = completed_results[cache_key]

    # The original app.py had this filter, preserving it.
    # It ensures only albums with playtime > 0 are shown, if relevant.
    filtered_results = [
        album for album in results_data if album.get("play_time_seconds", 0) > 0
    ]

    if not filtered_results:
        with unmatched_lock:
            unmatched_count = len(UNMATCHED)

        filter_description = get_filter_description(  # from app.utils
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
    )


@views_bp.route("/unmatched_view", methods=["POST"])
def unmatched_view():
    """Show a dedicated page of unmatched albums that didn't match the filters"""

    username = request.form.get("username")
    year = request.form.get("year")
    release_scope = request.form.get("release_scope", "same")
    decade = request.form.get("decade")
    release_year = request.form.get("release_year")

    min_plays = request.form.get("min_plays", "10")
    min_tracks = request.form.get("min_tracks", "3")

    # Get user-friendly filter description
    filter_desc = get_filter_description(
        release_scope, decade, release_year, int(year)
    )  # from app.utils

    with unmatched_lock:
        unmatched_data = dict(UNMATCHED)

    reasons = {}
    for key, item in unmatched_data.items():
        reason = item.get("reason", "Unknown reason")
        if reason not in reasons:
            reasons[reason] = []
        reasons[reason].append(item)

    reason_counts = {reason: len(albums) for reason, albums in reasons.items()}

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


@views_bp.route("/results_loading", methods=["POST"])
def results_loading():
    """Handle form submission and start the background task to fetch/process data"""
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

    # Validate required fields
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

    with progress_lock:
        current_progress["progress"] = 0
        current_progress["message"] = "Initializing..."
        current_progress["error"] = False

    task_thread = threading.Thread(
        target=background_task,  # from app.tasks
        args=(
            username,
            year,
            sort_mode,
            release_scope,
            decade,
            release_year,
            min_plays,
            min_tracks,
        ),
        daemon=True,
    )
    task_thread.start()

    with unmatched_lock:
        UNMATCHED.clear()  # Clear the unmatched dictionary for a new request

    return render_template(
        "loading.html",
        username=username,
        year=year,
        sort_by=sort_mode,
        release_scope=release_scope,
        decade=decade,
        release_year=release_year,
        min_plays=min_plays,
        min_tracks=min_tracks,
    )
