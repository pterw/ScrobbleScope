# app/routes/api.py

from flask import Blueprint, jsonify, request

from app.state import UNMATCHED, current_progress, progress_lock, unmatched_lock

api_bp = Blueprint("api", __name__)


@api_bp.route("/progress")
def progress():
    """Return current progress as JSON"""
    with progress_lock:
        return jsonify(current_progress)


@api_bp.route("/unmatched")
def unmatched():
    with unmatched_lock:
        unmatched_data = dict(
            UNMATCHED
        )  # Create a copy to avoid potential race conditions
        count = len(unmatched_data)
    return jsonify({"count": count, "data": unmatched_data})


@api_bp.route("/reset_progress", methods=["POST"])
def reset_progress():
    """Reset progress state - useful if a task gets stuck"""
    with progress_lock:
        current_progress["progress"] = 0
        current_progress["message"] = "Reset successful"
        current_progress["error"] = False
    return jsonify({"status": "success"})
