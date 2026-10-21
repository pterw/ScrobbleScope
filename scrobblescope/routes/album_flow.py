"""The album job flow: loading, results, unmatched, and starting a new job.

See ``scrobblescope/routes/__init__.py`` for why cross-cutting dependencies
that live on the facade (``_check_user_exists``, ``_check_profile_is_public``,
``_get_validated_job_context``, ``_request_or_session_job_id``,
``acquire_job_slot``, ``start_job_thread``) are read through the live
``routes`` module reference (``_routes``) rather than imported directly.
"""

import logging

from flask import jsonify, redirect, render_template, request, session, url_for

from scrobblescope import jobs
from scrobblescope import routes as _routes
from scrobblescope.album_request import (
    Refusal,
    parse_album_request,
    registration_refusal,
)
from scrobblescope.listening_stats import album_play_statistics
from scrobblescope.orchestrator import background_task
from scrobblescope.routes import admission, precheck
from scrobblescope.spotlight import select_spotlight_artists
from scrobblescope.unmatched import (
    CATEGORY_METADATA,
    REASON_NO_SPOTIFY_MATCH,
    REASON_PROVIDER_UNAVAILABLE,
)

bp = _routes.bp


def _extract_job_params(job_context):
    """Return a dict of job parameters stored in *job_context*."""
    params = job_context.get("params", {})
    return {
        "username": params.get("username"),
        "year": params.get("year"),
        "sort_mode": params.get("sort_mode"),
        "release_scope": params.get("release_scope", "same"),
        "decade": params.get("decade"),
        "release_year": params.get("release_year"),
        "min_plays": params.get("min_plays", 10),
        "min_tracks": params.get("min_tracks", 3),
        "limit_results": params.get("limit_results", "all"),
        "include_unmatched": params.get("include_unmatched", False),
    }


def _filter_results_for_display(results_data, sort_mode):
    """Remove albums with no play-time data when sorting by playtime.

    Albums without ``play_time_seconds`` would sort to zero and produce
    misleading playtime rankings. All albums are kept for every other
    sort mode.
    """
    return [
        album
        for album in results_data
        if album.get("play_time_seconds", 0) > 0 or sort_mode != "playtime"
    ]


def _get_filter_description(release_scope, decade, release_year, listening_year):
    """Generate a readable description of the active release-year filter.

    Wording only; the years each scope accepts are the table in
    ``domain.release_window``.
    """
    if release_scope == "all":
        return "all albums (no release year filter)"
    elif release_scope == "same":
        return f"albums released in {listening_year}"
    elif release_scope == "previous":
        return f"albums released in {listening_year - 1}"
    elif release_scope == "decade" and decade:
        return f"albums released in the {decade}"
    elif release_scope == "custom" and release_year:
        return f"albums released in {release_year}"
    else:
        return "albums matching your criteria"


def _render_loading_page():
    """Render the canonical loading page for an existing job."""
    job_id, job_context, err = _routes._get_validated_job_context(
        missing_id_message="We could not identify your in-progress request.",
        expired_error="Job Not Found",
        expired_message="Your loading session has expired.",
        expired_details="Please start a new search.",
        session_key=_routes._LATEST_ALBUM_JOB,
        expected_mode=jobs.MODE_ALBUM,
    )
    if err:
        return err

    p = _extract_job_params(job_context)
    return render_template(
        "loading.html",
        job_id=job_id,
        username=p["username"],
        year=p["year"],
        sort_by=p["sort_mode"],
        include_unmatched=p["include_unmatched"],
        release_scope=p["release_scope"],
        decade=p["decade"],
        release_year=p["release_year"],
        min_plays=p["min_plays"],
        min_tracks=p["min_tracks"],
        limit_results=p["limit_results"],
    )


@bp.route("/loading", methods=["GET"])
def loading_page():
    """Show the canonical loading URL for the current job."""
    return _render_loading_page()


@bp.route("/reset_progress", methods=["POST"])
def reset_progress():
    """Reset progress state for a specific job ID."""
    job_id = request.form.get("job_id")
    if not job_id:
        return jsonify({"status": "error", "message": "Missing job identifier."}), 400

    if not jobs.reset(job_id, "Reset successful"):
        return jsonify({"status": "error", "message": "Job not found."}), 404

    return jsonify({"status": "success"})


def _partial_run_notice(stats, unchecked_count):
    """Return ``(text, link_to_unmatched)`` for a degraded run, or ``("", False)``.

    The orchestrator records ``partial_data_warning`` (the loading page shows
    it for three seconds) and, beside it, ``partial_data_sources``: which kind
    of degradation it was, ``"lastfm"`` (pages dropped) or ``"provider"``
    (Spotify or Deezer could not answer). This reads the kind, never the
    wording. The Results page is where the ranking is read, so it says so
    there too. Last.fm's own sentence already reads as plain copy; the
    provider sentences are written for the loading page ("checking Deezer for
    their details"), so Results words them afresh. Only a provider outage
    leaves albums under "could not be checked", so only that notice links to
    the Unmatched page, and only when ``unchecked_count`` albums are there.
    """
    stats = stats or {}
    sources = stats.get("partial_data_sources") or []
    if not sources:
        return "", False
    lastfm_text = ""
    if "lastfm" in sources:
        lastfm_text = "Some Last.fm pages failed to load, so results may be incomplete."
        if "provider" not in sources:
            return stats.get("partial_data_warning") or lastfm_text, False
    return (
        (lastfm_text + " " if lastfm_text else "")
        + "Spotify or Deezer could not answer for some albums in this run, so "
        "the ranking may be missing albums or details.",
        bool(unchecked_count),
    )


def _render_results_page():
    """Render the results page for a completed job, or an error page on failure."""
    used_saved_job = request.method == "GET" and not request.values.get("job_id")
    if request.method == "GET" and not _routes._request_or_session_job_id(
        _routes._LATEST_ALBUM_JOB
    ):
        return render_template("results_empty.html")

    job_id, job_context, err = _routes._get_validated_job_context(
        missing_id_message="We could not identify your in-progress request.",
        expired_error="Results Not Found",
        expired_message="We couldn't find your results.",
        expired_details="The processing may have expired. Please try again.",
        session_key=_routes._LATEST_ALBUM_JOB,
        expected_mode=jobs.MODE_ALBUM,
    )
    if err:
        if used_saved_job:
            return render_template(
                "results_empty.html",
                empty_message=(
                    "Your previous results have expired. Run an album search "
                    "to build a new ranking."
                ),
            )
        return err

    progress_payload = job_context["progress"]
    if progress_payload.get("error"):
        error_code = progress_payload.get("error_code")
        retryable = progress_payload.get("retryable", False)
        details = "Please try again or use different parameters."
        status_code = 500
        if retryable:
            details = "This appears to be a temporary issue. Please try again."
            status_code = 503
        if error_code == "user_not_found":
            details = "Please check the username and try again."
            status_code = 404
        elif error_code == "private_profile":
            details = "Make recent listening public on Last.fm, then search again."
            status_code = 403
        return (
            render_template(
                "error.html",
                error="Processing Error",
                status_code=status_code,
                message=progress_payload.get("message", "An unknown error occurred"),
                details=details,
            ),
            status_code,
        )

    p = _extract_job_params(job_context)
    username = p["username"] or request.values.get("username")
    year = p["year"]
    if year is None:
        year = int(request.values.get("year", _routes._current_year()))
    sort_mode = p["sort_mode"] or request.values.get("sort_by", "playcount")
    release_scope = p["release_scope"] or request.values.get("release_scope", "same")
    decade = p["decade"]
    release_year = p["release_year"]
    min_plays = p["min_plays"]
    min_tracks = p["min_tracks"]

    results_data = job_context.get("results")
    if results_data is None:
        return (
            render_template(
                "error.html",
                error="Results Still Processing",
                status_code=202,
                message="Your results are not ready yet.",
                details="Please wait on the loading page and try again.",
            ),
            202,
        )

    filtered_results = _filter_results_for_display(results_data, sort_mode)
    # The figures describe the rows this page lists, after every filter it
    # applies, so they are computed here and not at job completion.
    play_stats = album_play_statistics(filtered_results)

    unmatched_count = len(job_context.get("unmatched", {}))
    unchecked_count = sum(
        1
        for item in job_context.get("unmatched", {}).values()
        if item.get("reason_code") == REASON_PROVIDER_UNAVAILABLE
    )
    has_durations = any(a.get("play_time_seconds", 0) > 0 for a in (results_data or []))
    partial_notice, partial_notice_links_unmatched = _partial_run_notice(
        progress_payload.get("stats"), unchecked_count
    )

    if not filtered_results:
        filter_description = _get_filter_description(
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
            partial_notice=partial_notice,
            partial_notice_links_unmatched=partial_notice_links_unmatched,
            has_durations=has_durations,
            filter_description=filter_description,
            job_id=job_id,
            play_stats=play_stats,
        )

    # Passed so the release-check status line renders with the page. It sits
    # above the table, so creating it on the first poll reply would push every
    # row down -- the one move the owner's progressive-disclosure ruling
    # forbids. A skipped pass reserves nothing, because nothing will report.
    release_check = progress_payload.get("stats", {}).get("release_check")

    include_unmatched = p["include_unmatched"]
    unmatched_row_count = sum(1 for a in filtered_results if a.get("unmatched_reason"))
    # The badge words come from the Unmatched page's table, one source.
    unmatched_badges = {
        code: CATEGORY_METADATA[code]["badge"]
        for code in (REASON_NO_SPOTIFY_MATCH, REASON_PROVIDER_UNAVAILABLE)
    }

    # Matched rows only: an unmatched album has no provider data for the
    # artist portrait, so it cannot be the spotlight.
    spotlight_artists = select_spotlight_artists(
        [a for a in filtered_results if not a.get("unmatched_reason")], job_id
    )
    spotlight_artist = spotlight_artists[0] if spotlight_artists else {}
    top_artist_name = spotlight_artist.get("name", "")
    top_artist_scrobbles = spotlight_artist.get("scrobbles", 0)
    top_artist_album_count = spotlight_artist.get("album_count", 0)
    top_artist_play_time = spotlight_artist.get("play_time", "")

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
        unmatched_count=unmatched_count,
        partial_notice=partial_notice,
        partial_notice_links_unmatched=partial_notice_links_unmatched,
        has_durations=has_durations,
        play_stats=play_stats,
        include_unmatched=include_unmatched,
        unmatched_row_count=unmatched_row_count,
        unmatched_badges=unmatched_badges,
        job_id=job_id,
        top_artist_name=top_artist_name,
        top_artist_scrobbles=top_artist_scrobbles,
        top_artist_album_count=top_artist_album_count,
        top_artist_play_time=top_artist_play_time,
        spotlight_artists=spotlight_artists,
        release_check=release_check,
    )


@bp.route("/results", methods=["GET"])
def results():
    """Show completed results at their canonical URL."""
    return _render_results_page()


@bp.route("/results_complete", methods=["POST"])
def results_complete():
    """Keep the legacy completion POST working while callers move to GET."""
    return _render_results_page()


def _listed_unmatched_counts(job_context, include_unmatched, unmatched_data, reasons):
    """Count the report's albums that an include run lists in its results.

    A report entry is listed when the run is an include run and a result row
    carrying ``unmatched_reason`` has the entry's report key as its
    ``_normalized_key``. A Show limit can cut such rows, so the reason code
    alone never says an album is listed. Returns ``(listed, by_reason)``:
    the total, and the count per ``reasons`` group.
    """
    if not include_unmatched:
        return 0, {}
    results = job_context.get("results")
    rows = results if isinstance(results, list) else []
    listed_keys = {
        "|".join(row["_normalized_key"])
        for row in rows
        if row.get("unmatched_reason") and row.get("_normalized_key")
    }
    # group_unmatched_albums groups the very dicts held in unmatched_data.
    listed_ids = {
        id(item) for key, item in unmatched_data.items() if key in listed_keys
    }
    by_reason = {
        reason_key: sum(1 for album in albums if id(album) in listed_ids)
        for reason_key, albums in reasons.items()
    }
    return sum(by_reason.values()), by_reason


def _render_unmatched_page():
    """Render the unmatched-album report for an existing job."""
    used_saved_job = request.method == "GET" and not request.values.get("job_id")
    if request.method == "GET" and not _routes._request_or_session_job_id(
        _routes._LATEST_ALBUM_JOB
    ):
        return render_template("unmatched_empty.html")

    job_id, job_context, err = _routes._get_validated_job_context(
        missing_id_message="We could not find unmatched albums without a valid job ID.",
        expired_error="Job Not Found",
        expired_message="Your unmatched album data has expired.",
        expired_details="Please run a new search.",
        session_key=_routes._LATEST_ALBUM_JOB,
        expected_mode=jobs.MODE_ALBUM,
    )
    if err:
        if used_saved_job:
            return render_template(
                "unmatched_empty.html",
                empty_message=(
                    "Your previous results have expired. Run a new album search."
                ),
            )
        return err

    p = _extract_job_params(job_context)
    username = p["username"]
    year = p["year"]
    release_scope = p["release_scope"]
    decade = p["decade"]
    release_year = p["release_year"]
    min_plays = p["min_plays"]
    min_tracks = p["min_tracks"]

    filter_desc = _get_filter_description(
        release_scope, decade, release_year, int(year)
    )

    unmatched_data = dict(job_context.get("unmatched", {}))
    reasons, reason_counts, reason_metadata = _routes.group_unmatched_albums(
        unmatched_data
    )

    listed_count, listed_by_reason = _listed_unmatched_counts(
        job_context, p["include_unmatched"], unmatched_data, reasons
    )

    return render_template(
        "unmatched.html",
        username=username,
        year=year,
        filter_desc=filter_desc,
        unmatched_data=unmatched_data,
        reasons=reasons,
        reason_counts=reason_counts,
        reason_metadata=reason_metadata,
        total_count=len(unmatched_data),
        listed_count=listed_count,
        listed_by_reason=listed_by_reason,
        min_plays=min_plays,
        min_tracks=min_tracks,
        job_id=job_id,
    )


@bp.route("/unmatched", methods=["GET"])
def unmatched_page():
    """Show the unmatched-album report at its canonical URL."""
    return _render_unmatched_page()


@bp.route("/unmatched_view", methods=["POST"])
def unmatched_view():
    """Keep the legacy unmatched POST working while callers move to GET."""
    return _render_unmatched_page()


def _refuse(message, status=200):
    """Re-render the form with *message*.

    Every refusal is a 200 with the reason on the form, except an outage of the
    Last.fm pre-check, which is a retryable 503: the listener can try again.
    """
    return render_template("index.html", error=message), status


@bp.route("/results_loading", methods=["POST"])
def results_loading():
    """Turn the submitted form into a job, or re-render the form with one reason.

    Order: parse the form (no network), pre-check the Last.fm user, compare the
    registration year, admit the job. Each step that refuses ends the request
    before the next one runs, so a refusal never costs a slot or a job.
    """
    album = parse_album_request(request.form, current_year=_routes._current_year())
    if isinstance(album, Refusal):
        logging.warning("Album form refused on field %s.", album.field)
        return _refuse(album.message)

    # Existence first, then privacy: a name Last.fm does not know gets "not
    # found", never a verdict about a ghost. A lookup that cannot answer
    # refuses retryably and starts nothing.
    check = precheck.check_lastfm_user(album.username)
    if check.verdict is precheck.Verdict.UNAVAILABLE:
        return _refuse(precheck.UNAVAILABLE_MESSAGE, status=503)
    if check.verdict is precheck.Verdict.MISSING:
        return _refuse(precheck.not_found_message(album.username))
    if check.verdict is precheck.Verdict.PRIVATE:
        return _refuse(_routes._PRIVATE_PROFILE_MESSAGE)

    # The registration-year comparison is the one optional step: an account
    # whose registration year Last.fm did not report is simply not compared.
    hint = registration_refusal(album.year, check.registered_year)
    if hint is not None:
        return _refuse(hint.message)

    admitted = admission.admit(
        album.to_params(), background_task, label="background task"
    )
    if admitted is admission.Refused.CAPACITY:
        return _refuse(_routes._capacity_message())
    if admitted is admission.Refused.START_FAILED:
        return _refuse("Failed to start processing. Please try again.")

    session[_routes._LATEST_ALBUM_JOB] = admitted

    return redirect(url_for(".loading_page", job_id=admitted), code=303)
