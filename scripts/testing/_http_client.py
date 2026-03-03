"""Shared HTTP transport layer for ScrobbleScope integration test scripts.

This module provides three functions that encapsulate the HTTP interaction
pattern common to all testing scripts: fetch a CSRF token from the index
page, submit a job via POST to /results_loading, and poll /progress until
the job completes or a timeout fires.

**Internal module** -- not intended to be executed directly.  Import it
from other scripts in ``scripts/testing/``::

    from scripts.testing._http_client import (
        fetch_csrf_token,
        submit_job,
        poll_until_complete,
    )

Design notes
------------
* A single ``requests.Session`` is threaded through all three functions so
  that cookies (including the Flask session cookie that Flask-WTF ties to
  the CSRF token) persist across requests.
* The CSRF token is fetched from the index page's hidden ``<input>`` field.
  Flask-WTF validates POSTs against (token + session cookie), so both must
  come from the same Session object.
* The job data (including ``job_id``) is extracted from the
  ``<script id="scrobble-config" type="application/json">`` tag in the
  loading page response -- **not** from the ``window.SCROBBLE = ...`` JS
  assignment, which is a ``JSON.parse()`` call and does not contain the
  literal object.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Regex patterns for HTML scraping
# ---------------------------------------------------------------------------

# Matches the hidden CSRF input field rendered by Flask-WTF on the index page.
# Captures the ``value`` attribute content (the token string).
CSRF_INPUT_RE = re.compile(
    r'<input[^>]+name=["\']csrf_token["\'][^>]+value=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Matches the <script id="scrobble-config" type="application/json"> block
# on the loading page.  Captures the raw JSON content between the tags.
SCROBBLE_CONFIG_RE = re.compile(
    r'<script\s+id=["\']scrobble-config["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fetch_csrf_token(session: requests.Session, base_url: str) -> str:
    """Fetch the CSRF token from the index page.

    GETs ``base_url/`` (the index page) and extracts the CSRF token from
    the hidden form field ``<input name="csrf_token" value="...">``.  The
    ``session`` object retains the Flask session cookie set by this request;
    Flask-WTF validates the POST token against the cookie, so both must
    originate from the same ``Session``.

    Parameters
    ----------
    session : requests.Session
        A persistent session that will hold cookies across requests.
    base_url : str
        The root URL of the ScrobbleScope instance (no trailing slash).

    Returns
    -------
    str
        The CSRF token string.

    Raises
    ------
    RuntimeError
        If the index page does not contain a ``csrf_token`` form field.
    """
    response = session.get(f"{base_url}/", timeout=30)
    response.raise_for_status()

    match = CSRF_INPUT_RE.search(response.text)
    if not match:
        raise RuntimeError(
            "Could not find csrf_token input field in the index page HTML. "
            "Ensure the app is running and the index template includes the "
            "CSRF hidden input."
        )
    return match.group(1)


def submit_job(
    session: requests.Session,
    base_url: str,
    username: str,
    year: int,
    sort_by: str = "playcount",
    release_scope: str = "same",
    min_plays: int = 10,
    min_tracks: int = 3,
) -> str:
    """Submit a search job and return the ``job_id``.

    Performs the two-step flow:

    1. Call :func:`fetch_csrf_token` to obtain a token (and a session
       cookie).
    2. POST to ``/results_loading`` with the form data and the token.

    The ``job_id`` is extracted from the ``<script id="scrobble-config">``
    JSON block that the loading page renders.

    Parameters
    ----------
    session : requests.Session
        A persistent session (cookies must survive between steps 1 and 2).
    base_url : str
        Root URL of the ScrobbleScope instance (no trailing slash).
    username : str
        Last.fm username to look up.
    year : int
        Calendar year to scan.
    sort_by : str
        Sort mode (``"playcount"`` or ``"playtime"``).
    release_scope : str
        Release scope filter (``"same"``, ``"previous"``, etc.).
    min_plays : int
        Minimum play count threshold.
    min_tracks : int
        Minimum unique track threshold.

    Returns
    -------
    str
        The ``job_id`` assigned by the server.

    Raises
    ------
    RuntimeError
        If the CSRF token cannot be obtained, the POST fails, or the
        loading page does not contain a valid ``scrobble-config`` block
        with a ``job_id`` key.
    """
    csrf_token = fetch_csrf_token(session, base_url)

    response = session.post(
        f"{base_url}/results_loading",
        data={
            "csrf_token": csrf_token,
            "username": username,
            "year": str(year),
            "sort_by": sort_by,
            "release_scope": release_scope,
            "min_plays": str(min_plays),
            "min_tracks": str(min_tracks),
            "limit_results": "all",
        },
        timeout=30,
    )
    response.raise_for_status()

    # Extract the JSON payload from the <script id="scrobble-config"> tag.
    # This tag contains the Jinja2-rendered job data as raw JSON.
    match = SCROBBLE_CONFIG_RE.search(response.text)
    if not match:
        raise RuntimeError(
            "Could not locate <script id='scrobble-config'> block in the "
            "loading page response. The POST may have been rejected or "
            "redirected."
        )

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse scrobble-config JSON: {exc}") from exc

    job_id = payload.get("job_id")
    if not job_id:
        raise RuntimeError(
            "The scrobble-config payload did not include a job_id key. "
            f"Payload keys: {list(payload.keys())}"
        )
    return job_id


def poll_until_complete(
    session: requests.Session,
    base_url: str,
    job_id: str,
    timeout_seconds: int = 180,
    poll_interval: float = 1.0,
) -> dict[str, Any]:
    """Poll ``/progress`` until the job completes or a timeout fires.

    Repeatedly GETs ``/progress?job_id=<job_id>`` and checks whether the
    ``progress`` field has reached 100.  Returns the final progress payload
    dict on success.

    Parameters
    ----------
    session : requests.Session
        A persistent session.
    base_url : str
        Root URL of the ScrobbleScope instance (no trailing slash).
    job_id : str
        The UUID job identifier returned by :func:`submit_job`.
    timeout_seconds : int
        Maximum wall-clock seconds to wait before raising ``TimeoutError``.
    poll_interval : float
        Seconds to sleep between poll attempts.

    Returns
    -------
    dict[str, Any]
        The final ``/progress`` JSON payload (includes ``stats``, ``message``,
        ``progress``, and possibly ``error`` / ``error_code`` keys).

    Raises
    ------
    RuntimeError
        If ``/progress`` returns an unexpected HTTP status code (not 200 or
        404).
    TimeoutError
        If the deadline is exceeded before the job reaches 100% progress.
    """
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        response = session.get(
            f"{base_url}/progress",
            params={"job_id": job_id},
            timeout=30,
        )
        # 200 = normal progress; 404 = job not yet registered (race on startup).
        # Anything else is unexpected.
        if response.status_code not in (200, 404):
            raise RuntimeError(
                f"/progress returned unexpected status {response.status_code}: "
                f"{response.text[:200]}"
            )

        if response.status_code == 200:
            payload = response.json()
            progress = int(payload.get("progress", 0))
            if progress >= 100:
                return payload

        time.sleep(poll_interval)

    raise TimeoutError(
        f"Timed out waiting for job {job_id} after {timeout_seconds} seconds."
    )
