"""The heatmap job flow: the page, starting a job, and polling for results.

See ``scrobblescope/routes/__init__.py`` for why cross-cutting dependencies
that live on the facade (``_check_user_exists``, ``_check_profile_is_public``,
``_latest_heatmap_job``, ``acquire_job_slot``, ``start_job_thread``) are read through the live ``routes`` module reference
(``_routes``) rather than imported directly.
"""

from flask import jsonify, render_template, request, session

from scrobblescope import jobs
from scrobblescope import routes as _routes
from scrobblescope.heatmap import heatmap_task
from scrobblescope.routes import admission, precheck

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

    The answer is the shared pre-check's (``routes/precheck.py``); this maps
    it to the heatmap's JSON. A lookup or privacy outage is a retryable 503
    that reserves no worker slot and leaves this browser's saved heatmap job
    alone.
    """
    check = precheck.check_lastfm_user(username)

    if check.verdict is precheck.Verdict.PUBLIC:
        return None
    if check.verdict is precheck.Verdict.UNAVAILABLE:
        return (
            jsonify(
                {
                    "error": True,
                    "message": precheck.UNAVAILABLE_MESSAGE,
                    "retryable": True,
                }
            ),
            503,
        )
    if check.verdict is precheck.Verdict.MISSING:
        return (
            jsonify(
                {
                    "error": True,
                    "error_code": "user_not_found",
                    "message": precheck.not_found_message(username),
                    "retryable": False,
                }
            ),
            404,
        )
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


def _dispatch_heatmap_job(username):
    """Admit a heatmap job, saving its ID only after startup.

    Admission removes the orphan job and the slot if thread startup fails.
    """
    admitted = admission.admit(
        {"username": username, "mode": jobs.MODE_HEATMAP},
        heatmap_task,
        label="heatmap task",
    )
    if admitted is admission.Refused.CAPACITY:
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
    if admitted is admission.Refused.START_FAILED:
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

    session[_routes._LATEST_HEATMAP_JOB] = admitted
    return jsonify({"job_id": admitted}), 202


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

    ctx = jobs.context(job_id)
    if ctx is None:
        return (
            jsonify({"error": True, "message": "Job not found or expired."}),
            404,
        )

    if ctx.get("params", {}).get("mode") != jobs.MODE_HEATMAP:
        # An album job's results are a list of rows, not the mapping this
        # answer spreads, so a wrong-mode id is refused the way a missing
        # job is -- the same rule the album pages and release checks follow.
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
