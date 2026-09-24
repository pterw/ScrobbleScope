"""The heatmap job flow: the page, starting a job, and polling for results.

See ``scrobblescope/routes/__init__.py`` for why cross-cutting dependencies
that live on the facade (``_check_user_exists``, ``_check_profile_is_public``,
``_latest_heatmap_job``, ``acquire_job_slot``, ``start_job_thread``,
``get_job_context``) are read through the live ``routes`` module reference
(``_routes``) rather than imported directly.
"""

import logging

from flask import jsonify, render_template, request, session

from scrobblescope import routes as _routes
from scrobblescope.heatmap import heatmap_task
from scrobblescope.repositories import cleanup_expired_jobs, create_job, delete_job

bp = _routes.bp


@bp.route("/heatmap", methods=["GET"])
def heatmap():
    """Show this browser's latest heatmap or its dedicated empty state."""
    latest_job = _routes._latest_heatmap_job()
    if not latest_job:
        return render_template("heatmap_empty.html")
    return render_template(
        "index.html",
        initial_mode="heatmap",
        initial_heatmap_job=latest_job,
    )


@bp.route("/heatmap_loading", methods=["POST"])
def heatmap_loading():
    """Start a heatmap background job for the given Last.fm username.

    Accepts ``username`` from form data or a JSON body (for AJAX callers).
    Returns a JSON response with ``job_id`` on success (202) or an error
    payload with the appropriate HTTP status code on failure.
    """
    # Support both form-encoded and JSON request bodies.
    username = request.form.get("username")
    if not username and request.is_json:
        username = (request.get_json(silent=True) or {}).get("username")
    if username:
        username = username.strip()

    if not username:
        return (
            jsonify({"error": True, "message": "Username is required."}),
            400,
        )

    error = _validate_heatmap_user(username)
    if error is not None:
        return error
    return _dispatch_heatmap_job(username)


def _validate_heatmap_user(username):
    """Return a JSON validation error, or None for an existing public user.

    Keep lookup and privacy service failures retryable without reserving a
    worker slot or changing this browser's saved heatmap job.
    """
    try:
        user_info = _routes._check_user_exists(username)
    except Exception:
        logging.exception("User existence check failed for %s", username)
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Validation service unavailable. Try again.",
                    "retryable": True,
                }
            ),
            503,
        )

    if not user_info["exists"]:
        return (
            jsonify(
                {
                    "error": True,
                    "error_code": "user_not_found",
                    "message": f"User '{username}' was not found on Last.fm.",
                    "retryable": False,
                }
            ),
            404,
        )

    try:
        if not _routes._check_profile_is_public(username):
            return (
                jsonify(
                    {
                        "error": True,
                        "error_code": "private_profile",
                        "message": _routes._PRIVATE_PROFILE_MESSAGE,
                        "retryable": False,
                    }
                ),
                403,
            )
    except Exception:
        logging.exception("Profile privacy check failed for %s", username)
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Validation service unavailable. Try again.",
                    "retryable": True,
                }
            ),
            503,
        )
    return None


def _dispatch_heatmap_job(username):
    """Reserve and launch a heatmap job, saving its ID only after startup.

    Remove orphan job state if thread startup fails; the worker launcher
    owns releasing the reserved slot on that failure path.
    """
    cleanup_expired_jobs()

    if not _routes.acquire_job_slot():
        return (
            jsonify(
                {
                    "error": True,
                    "message": _routes._capacity_message(),
                    "retryable": True,
                }
            ),
            429,
        )

    job_id = create_job({"username": username, "mode": "heatmap"})

    try:
        _routes.start_job_thread(heatmap_task, args=(job_id, username))
    except Exception:
        logging.exception("Failed to start heatmap task thread")
        delete_job(job_id)
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Failed to start processing.",
                    "retryable": True,
                }
            ),
            500,
        )

    session[_routes._LATEST_HEATMAP_JOB] = job_id
    return jsonify({"job_id": job_id}), 202


@bp.route("/heatmap_data")
def heatmap_data():
    """Return heatmap results, error details, or a processing-in-progress marker.

    Callers poll this endpoint with a ``job_id`` query parameter until the
    response contains ``"ready": true`` (success) or ``"error": true``
    (terminal failure).
    """
    job_id = request.args.get("job_id")
    if not job_id:
        return (
            jsonify({"error": True, "message": "Missing job identifier."}),
            400,
        )

    ctx = _routes.get_job_context(job_id)
    if ctx is None:
        return (
            jsonify({"error": True, "message": "Job not found or expired."}),
            404,
        )

    progress = ctx["progress"]
    if progress.get("error"):
        return (
            jsonify(
                {
                    "error": True,
                    "message": progress.get("message"),
                    "error_code": progress.get("error_code"),
                    "retryable": progress.get("retryable", False),
                }
            ),
            200,
        )

    if ctx["results"] is not None:
        return jsonify({"ready": True, **ctx["results"]}), 200

    return jsonify({"ready": False}), 202
