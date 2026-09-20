"""Small JSON/service endpoints: validation, CSRF, progress, and spotlight.

See ``scrobblescope/routes/__init__.py`` for why cross-cutting dependencies
that live on the facade (``_check_user_exists``, ``_check_profile_is_public``,
``fetch_spotify_access_token``, ``run_async_in_thread``) are read through the
live ``routes`` module reference (``_routes``) rather than imported directly.
"""

import logging

from flask import jsonify, request
from flask_wtf.csrf import generate_csrf

from scrobblescope import routes as _routes
from scrobblescope.domain import format_album_key
from scrobblescope.release_checks import CHECK_UNCHECKED, STATUS_PENDING
from scrobblescope.repositories import (
    get_job_context,
    get_job_progress,
    get_job_unmatched,
)
from scrobblescope.spotify import fetch_spotify_artist_spotlight
from scrobblescope.utils import create_optimized_session

bp = _routes.bp


@bp.route("/validate_user", methods=["GET"])
def validate_user():
    """Validate a Last.fm username for client-side blur checks."""
    username = (request.args.get("username") or "").strip()
    if not username:
        return jsonify({"valid": False, "message": "Username is required."}), 400
    if len(username) > 64:
        return jsonify({"valid": False, "message": "Username is too long."}), 400

    try:
        result = _routes._check_user_exists(username)
        if result["exists"] and not _routes._check_profile_is_public(username):
            return jsonify(
                {"valid": False, "message": _routes._PRIVATE_PROFILE_MESSAGE}
            )
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


@bp.route("/csrf-token", methods=["GET"])
def csrf_token():
    """Issue a fresh token for a long-lived AJAX form without reloading it."""
    return jsonify({"csrf_token": generate_csrf()})


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


@bp.route("/api/unmatched")
def unmatched_data():
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


#: The job-level status an error response carries. It is deliberately not
#: one of the worker's own words: a poller that stops on anything it does
#: not recognise stops on an error too, which is the safe direction.
_RELEASE_CHECK_ERROR_STATUS = "error"


def _release_check_error(message, status_code):
    """Return a fully shaped release-check payload carrying *message*."""
    return (
        jsonify(
            {
                "status": _RELEASE_CHECK_ERROR_STATUS,
                "checked": 0,
                "total": 0,
                "moved_in": 0,
                "albums": [],
                "error": message,
            }
        ),
        status_code,
    )


def _changed_albums(results):
    """Return one entry per result the correction worker has ruled on.

    A result the worker has not reached yet is omitted rather than sent as
    ``unchecked``: the page already renders every row, so the only thing it
    needs from this endpoint is what changed. A result with no
    ``_normalized_key`` cannot be addressed by the page either, so it is
    skipped for the same reason ``update_job_result`` never matches one.
    """
    albums = []
    for result in results or []:
        state = result.get("release_check")
        if not state or state == CHECK_UNCHECKED:
            continue
        normalized_key = result.get("_normalized_key")
        if not normalized_key:
            continue
        albums.append(
            {
                "key": format_album_key(normalized_key),
                "original_release_date": result.get("original_release_date"),
                "state": state,
            }
        )
    return albums


@bp.route("/api/release_checks", methods=["GET"])
def release_checks():
    """Return the live MusicBrainz correction state for one album job.

    The results page polls this while the correction worker
    (``scrobblescope/release_checks.py``) works through the job, and stops on
    a terminal status. Errors answer in JSON rather than through
    ``_get_validated_job_context``, whose failure paths render ``error.html``:
    a poller cannot read an HTML page, and its sibling JSON endpoints above
    already answer this way.

    Ownership follows the same rule as every other job endpoint here -- the
    128-bit job ID is the capability, with no session check. F-B22-3 records
    that as an open question for the owner rather than a decision taken in
    this endpoint alone.
    """
    job_id = request.args.get("job_id")
    if not job_id:
        return _release_check_error("Missing job identifier.", 400)

    job_context = get_job_context(job_id)
    if job_context is None:
        return _release_check_error("Job not found or expired.", 404)
    if job_context.get("params", {}).get("mode", "album") != "album":
        # A heatmap job has no albums to correct, so this is a wrong-mode
        # request rather than an empty one -- the same 404 the album pages
        # give, for the same reason.
        return _release_check_error("Job not found or expired.", 404)

    state = job_context.get("progress", {}).get("stats", {}).get("release_check") or {}
    return jsonify(
        {
            "status": state.get("status", STATUS_PENDING),
            "checked": state.get("checked", 0),
            "total": state.get("total", 0),
            "moved_in": state.get("moved_in", 0),
            "albums": _changed_albums(job_context.get("results")),
        }
    )


@bp.route("/api/artist_spotlight", methods=["GET"])
def artist_spotlight():
    """Return spotlight photograph and metadata for the top artist."""
    artist_name = (request.args.get("artist") or "").strip()
    artist_id = (request.args.get("artist_id") or "").strip()
    if not artist_name and not artist_id:
        return jsonify({"error": "Missing artist or artist_id"}), 400

    async def _fetch():
        token = await _routes.fetch_spotify_access_token()
        if not token:
            return None
        async with create_optimized_session() as s:
            return await fetch_spotify_artist_spotlight(
                s, artist_name=artist_name, artist_id=artist_id, token=token
            )

    try:
        data = _routes.run_async_in_thread(_fetch)
        if data:
            return jsonify(data)
    except Exception as e:
        logging.warning(
            f"Error fetching artist spotlight for '{artist_name or artist_id}': {e}"
        )

    return jsonify(
        {
            "name": artist_name,
            "artist_id": artist_id,
            "image_url": None,
            "spotify_url": None,
        }
    )
