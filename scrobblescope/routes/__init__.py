"""Stable public facade for the Flask route package.

WP-0 (Batch 22) split the former ``scrobblescope/routes.py`` into this
package. One ``Blueprint`` -- ``bp``, named ``"main"`` for backward
compatibility with every ``url_for("main.<endpoint>")`` call in the
templates -- is shared across four route files grouped by concern:
``pages`` (the home page), ``album_flow`` (loading/results/unmatched for an
album job), ``heatmap_flow`` (the heatmap job and its page), and ``api``
(small JSON/service endpoints). Each decorates its own routes onto this
module's ``bp`` rather than declaring a separate blueprint, so endpoint
names, URLs and template references are unchanged.

Every external dependency stays imported here, unchanged, even where only a
submodule still calls it directly: the existing test suite patches several
of them at ``scrobblescope.routes.<name>``, and a submodule reads the current
value of a same-named attribute through the ``routes`` module reference at
the top of each file, not through its own import -- see
``scrobblescope/orchestrator/__init__.py`` for the identical reasoning.
Importers should continue to use this facade so the internal module
boundaries may evolve safely.
"""

import logging
from datetime import datetime

from flask import Blueprint, render_template, request, session, url_for

from scrobblescope.lastfm import check_profile_is_public, check_user_exists
from scrobblescope.repositories import cleanup_expired_jobs, get_job_context
from scrobblescope.spotify import fetch_spotify_access_token
from scrobblescope.unmatched import group_unmatched_albums
from scrobblescope.utils import run_async_in_thread
from scrobblescope.worker import acquire_job_slot, start_job_thread

bp = Blueprint("main", __name__)

_LATEST_ALBUM_JOB = "latest_album_job_id"
_LATEST_HEATMAP_JOB = "latest_heatmap_job_id"
_PRIVATE_PROFILE_MESSAGE = (
    "This Last.fm profile is private. Make recent listening public and try again."
)


def _check_user_exists(username):
    """Call check_user_exists in a dedicated async thread."""

    async def _check():
        return await check_user_exists(username)

    return run_async_in_thread(_check)


def _check_profile_is_public(username):
    """Call the Last.fm recent-listening privacy preflight in its own thread."""

    async def _check():
        return await check_profile_is_public(username)

    return run_async_in_thread(_check)


def _group_unmatched_by_reason(unmatched_data):
    """Group unmatched-album items by their ``reason`` string or ``reason_code``.

    Delegates to ``scrobblescope.unmatched.group_unmatched_albums``.
    """
    groups, counts, _ = group_unmatched_albums(unmatched_data)
    return groups, counts


def _request_or_session_job_id(session_key=None):
    """Return an explicit job ID, or the latest one stored for this browser."""
    return request.values.get("job_id") or (
        session.get(session_key) if session_key else None
    )


def _get_validated_job_context(
    missing_id_message,
    expired_error,
    expired_message,
    expired_details,
    session_key=None,
    expected_mode=None,
):
    """Validate ``job_id`` from the current request query or form data.

    Returns ``(job_id, job_context, None)`` on success, or
    ``(None, None, (html, status))`` when validation fails. Missing IDs
    return 400; unavailable or wrong-mode jobs return 404, matching the APIs.
    """
    cleanup_expired_jobs()
    job_id = _request_or_session_job_id(session_key)
    if not job_id:
        return (
            None,
            None,
            (
                render_template(
                    "error.html",
                    status_code=400,
                    error="Missing Job Identifier",
                    message=missing_id_message,
                    details="Please start a new search.",
                ),
                400,
            ),
        )

    job_context = get_job_context(job_id)
    actual_mode = None
    if job_context:
        actual_mode = job_context.get("params", {}).get("mode", "album")
    if not job_context or (expected_mode and actual_mode != expected_mode):
        logging.warning(f"Job context not found for {job_id}")
        if session_key and session.get(session_key) == job_id:
            session.pop(session_key, None)
        return (
            None,
            None,
            (
                render_template(
                    "error.html",
                    status_code=404,
                    error=expired_error,
                    message=expired_message,
                    details=expired_details,
                ),
                404,
            ),
        )

    if session_key:
        session[session_key] = job_id
    return job_id, job_context, None


def _latest_heatmap_job():
    """Return resumable heatmap metadata from an explicit or saved job."""
    cleanup_expired_jobs()
    job_id = request.values.get("job_id") or session.get(_LATEST_HEATMAP_JOB)
    if not job_id:
        return None

    job_context = get_job_context(job_id)
    if not job_context or job_context.get("params", {}).get("mode") != "heatmap":
        if session.get(_LATEST_HEATMAP_JOB) == job_id:
            session.pop(_LATEST_HEATMAP_JOB, None)
        return None

    session[_LATEST_HEATMAP_JOB] = job_id
    return {
        "job_id": job_id,
        "username": job_context.get("params", {}).get("username", ""),
    }


def _render_no_job_state(title, message):
    """Render a friendly empty state for a job-backed page opened directly."""
    return render_template(
        "error.html",
        page_title=title,
        error=title,
        message=message,
        empty_state=True,
        show_error_icon=False,
        show_status_code=False,
        show_back_action=False,
        primary_action_label="Start from Home",
    )


@bp.app_context_processor
def inject_current_year():
    """Inject ``current_year`` into all Jinja2 templates."""
    return {"current_year": datetime.now().year}


@bp.app_context_processor
def inject_page_navigation():
    """Build the shared, canonical page navigation for the current request."""
    endpoint = request.endpoint
    return {
        "page_navigation": (
            {
                "label": "Home",
                "href": url_for("main.home"),
                "active": endpoint == "main.home",
            },
            {
                "label": "Heatmap",
                "href": url_for("main.heatmap"),
                "active": endpoint == "main.heatmap",
            },
            {
                "label": "Results",
                "href": url_for("main.results"),
                "active": endpoint in {"main.results", "main.results_complete"},
            },
            {
                "label": "Unmatched",
                "href": url_for("main.unmatched_page"),
                "active": endpoint in {"main.unmatched_page", "main.unmatched_view"},
            },
        )
    }


@bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with a nice error page"""
    return (
        render_template(
            "error.html",
            error="Page not found",
            status_code=404,
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
            status_code=500,
            message="Something went wrong on our end. Please try again later.",
        ),
        500,
    )


# The concern-specific route files decorate onto ``bp`` above and, for any
# cross-cutting dependency the existing test suite patches at
# ``scrobblescope.routes.<name>``, read it back through a live reference to
# this module rather than their own import -- see the module docstring.
# They must be imported last, after every name above is defined.
from scrobblescope.routes import album_flow, api, heatmap_flow, pages  # noqa: E402,F401
from scrobblescope.routes.album_flow import (  # noqa: E402
    _filter_results_for_display,
    _get_filter_description,
)

__all__ = [
    "_check_profile_is_public",
    "_check_user_exists",
    "_filter_results_for_display",
    "_get_filter_description",
    "_group_unmatched_by_reason",
    "acquire_job_slot",
    "bp",
    "fetch_spotify_access_token",
    "get_job_context",
    "internal_error",
    "page_not_found",
    "run_async_in_thread",
    "start_job_thread",
]
