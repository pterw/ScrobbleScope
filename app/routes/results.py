"""Routes related to processing and displaying results."""

from __future__ import annotations

import copy

from flask import Blueprint, render_template, request

from ..state import (
    UNMATCHED,
    completed_results,
    current_progress,
    progress_lock,
    unmatched_lock,
)
from ..tasks import background_task

results_bp = Blueprint("results", __name__)


@results_bp.route("/results_loading", methods=["POST"])
def results_loading():
    """Start the background task and render the loading page."""
    username = request.form.get("username")
    year = int(request.form.get("year"))
    sort_mode = request.form.get("sort_by", "playcount")
    release_scope = request.form.get("release_scope", "same")
    decade = request.form.get("decade") if release_scope == "decade" else None
    release_year = (
        int(request.form.get("release_year"))
        if release_scope == "custom" and request.form.get("release_year")
        else None
    )
    min_plays = int(request.form.get("min_plays", "10"))
    min_tracks = int(request.form.get("min_tracks", "3"))

    with progress_lock:
        current_progress.update(
            {"progress": 0, "message": "Initializing...", "error": False}
        )
    background_task(
        username,
        year,
        sort_mode,
        release_scope,
        decade,
        release_year,
        min_plays,
        min_tracks,
    )

    with unmatched_lock:
        UNMATCHED.clear()

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


@results_bp.route("/results_complete", methods=["POST"])
def results_complete():
    """Render the results page after processing."""
    username = request.form.get("username")
    year = int(request.form.get("year"))
    sort_mode = request.form.get("sort_by", "playcount")
    release_scope = request.form.get("release_scope", "same")
    decade = request.form.get("decade")
    release_year = request.form.get("release_year")
    if release_year:
        release_year = int(release_year)
    min_plays = int(request.form.get("min_plays", "10"))
    min_tracks = int(request.form.get("min_tracks", "3"))

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
    data = completed_results.get(cache_key, [])
    filtered = [album for album in data if album.get("play_time_seconds", 0) > 0]

    with unmatched_lock:
        unmatched_count = len(UNMATCHED)

    return render_template(
        "results.html",
        username=username,
        year=year,
        data=filtered,
        release_scope=release_scope,
        decade=decade,
        release_year=release_year,
        sort_by=sort_mode,
        min_plays=min_plays,
        min_tracks=min_tracks,
        unmatched_count=unmatched_count,
        no_matches=not filtered,
    )


@results_bp.route("/unmatched_view", methods=["POST"])
def unmatched_view():
    """Show details for unmatched albums."""
    username = request.form.get("username")
    year = request.form.get("year")
    with unmatched_lock:
        unmatched_data = copy.deepcopy(UNMATCHED)

    reasons = {}
    for item in unmatched_data.values():
        reasons.setdefault(item.get("reason", "Unknown"), []).append(item)
    reason_counts = {r: len(a) for r, a in reasons.items()}

    return render_template(
        "unmatched.html",
        username=username,
        year=year,
        unmatched_data=unmatched_data,
        reasons=reasons,
        reason_counts=reason_counts,
        total_count=len(unmatched_data),
    )
