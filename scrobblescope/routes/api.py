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
from scrobblescope.repositories import get_job_progress, get_job_unmatched
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
