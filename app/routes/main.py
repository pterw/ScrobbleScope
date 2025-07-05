"""Flask blueprint containing the core routes."""
from copy import deepcopy

from flask import Blueprint, jsonify, render_template

from ..state import UNMATCHED, current_progress, progress_lock, unmatched_lock

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Render the home page."""

    return render_template("index.html")


@main_bp.route("/progress")
def progress():
    """Return JSON progress information for the front end."""

    with progress_lock:
        return jsonify(current_progress)


@main_bp.route("/unmatched")
def unmatched():
    """Expose unmatched album information as JSON."""

    with unmatched_lock:
        data = deepcopy(UNMATCHED)
        count = len(data)
    return jsonify({"count": count, "data": data})


@main_bp.route("/reset_progress", methods=["POST"])
def reset_progress():
    """Reset background task progress."""

    with progress_lock:
        current_progress.update(
            {"progress": 0, "message": "Reset successful", "error": False}
        )
    return jsonify({"status": "success"})
