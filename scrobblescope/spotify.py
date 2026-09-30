import asyncio
import base64
import contextlib
import contextvars
import logging
import time

import aiohttp

from scrobblescope.config import (
    MAX_RETRY_AFTER_SECONDS,
    SPOTIFY_BATCH_RETRIES,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_SEARCH_RETRIES,
    spotify_token_cache,
)
from scrobblescope.domain import normalize_track_name
from scrobblescope.enrichment import AlbumMetadata
from scrobblescope.errors import ProviderError, provider_failure
from scrobblescope.utils import (
    cancel_and_drain,
    create_optimized_session,
    get_spotify_limiter,
    parse_retry_after,
    retry_with_semaphore,
)

#: Seconds shaved off a token's stated lifetime, so a job that starts with a
#: token about to expire does not spend its second half on a rejected one.
SPOTIFY_TOKEN_MARGIN_SECONDS = 60

#: Statuses that are a refusal to answer, never "no match": the request itself
#: was turned down (400 bad request, 403 forbidden). 401 has its own path.
_REFUSAL_STATUSES = frozenset({400, 403})

#: Refusals (400/403) in a row, with no answer between, that trip a job's
#: breaker: a key that is revoked or blocked refuses every request, so three
#: in a row is a verdict, while one odd refusal is not.
PERSISTENT_REFUSALS = 3

#: What an attempt returns when Spotify answered 401: the token was rejected.
_TOKEN_REJECTED = object()


class SpotifyBreaker:
    """One job's verdict that Spotify has asked it to stay away.

    Tripped by the first Retry-After above ``MAX_RETRY_AFTER_SECONDS``. Once
    tripped, every later Spotify search and details call of that job answers
    "could not answer" without sending a request, so a 500-album job does not
    send 500 requests into a rate limit that will not lift for minutes.
    Deezer is untouched and still runs for those albums.

    Not a module global: jobs run concurrently, and one job's rate limit is
    not another's. See ``spotify_job_breaker``.
    """

    def __init__(self):
        self.tripped = False
        self.refusals_in_a_row = 0
        self.refusal_kinds_logged = set()
        self.refusals_not_logged = 0

    def trip(self, reason):
        if self.tripped:
            return
        self.tripped = True
        logging.warning(f"Spotify {reason}; this job sends Spotify no further requests")

    def note_refusal(self, operation, status):
        """Count a refusal; log the first of each kind, trip on a run of them.

        A persistent refusal (a revoked or blocked key) would otherwise cost
        one refused request per album. ``PERSISTENT_REFUSALS`` in a row, with
        no answer between, trips the breaker.
        """
        kind = (operation, status)
        if kind in self.refusal_kinds_logged:
            self.refusals_not_logged += 1
        else:
            self.refusal_kinds_logged.add(kind)
            logging.warning(f"Spotify refused {operation}: HTTP {status}")
        self.refusals_in_a_row += 1
        if self.refusals_in_a_row >= PERSISTENT_REFUSALS:
            self.trip(f"refused {self.refusals_in_a_row} requests in a row")

    def note_answer(self):
        self.refusals_in_a_row = 0


_job_breaker = contextvars.ContextVar("spotify_job_breaker", default=None)


@contextlib.contextmanager
def spotify_job_breaker():
    """Give the calls made inside this block, and only them, a fresh breaker.

    Carried in a context variable, so the search and details functions keep
    their signatures and every task the job spawns inside the block shares the
    job's breaker, while a concurrent job, on its own loop and context, has
    its own. Outside a block there is no breaker and nothing is skipped.
    """
    breaker = SpotifyBreaker()
    reset_token = _job_breaker.set(breaker)
    try:
        yield breaker
    finally:
        _job_breaker.reset(reset_token)
        if breaker.refusals_not_logged:
            logging.warning(
                f"Spotify refused {breaker.refusals_not_logged} further "
                "requests of this job (same operation and status as above)"
            )


def _breaker_open():
    breaker = _job_breaker.get()
    return breaker is not None and breaker.tripped


def _check_breaker():
    """Raise ``spotify_rate_limited`` if this job's breaker has tripped.

    Called at a function's entry and again inside every attempt, right before
    the request, once the semaphore and the limiter are held. The second call
    is the one that matters in a fan-out: every task passes the entry check
    before the first 429 has come back, and only this one stops the tasks
    still queued.
    """
    if _breaker_open():
        raise provider_failure("spotify")("rate_limited")


def _note_retry_after(retry_after):
    """Trip this job's breaker when *retry_after* is above the cap."""
    breaker = _job_breaker.get()
    if breaker is not None and retry_after > MAX_RETRY_AFTER_SECONDS:
        breaker.trip(
            f"asked for a {retry_after}s wait, above the {MAX_RETRY_AFTER_SECONDS}s cap"
        )


def _note_answer():
    breaker = _job_breaker.get()
    if breaker is not None:
        breaker.note_answer()


def _refused(operation, status):
    """Return the ``ProviderError`` for a request Spotify refused.

    Logs status and operation once per kind per job (the rest are counted and
    summarised when the job's block ends); outside a job block, every time.
    """
    breaker = _job_breaker.get()
    if breaker is None:
        logging.warning(f"Spotify refused {operation}: HTTP {status}")
    else:
        breaker.note_refusal(operation, status)
    return provider_failure("spotify")("unavailable")


async def _replace_rejected_token(rejected):
    """Drop the cached token if it is the one Spotify rejected; return a fresh one.

    A sibling call that already replaced it leaves the cache holding a newer
    token, which is returned as it is: one rejection costs one token request,
    not one per call.
    """
    if spotify_token_cache["token"] == rejected:
        spotify_token_cache["expires_at"] = 0
    return await fetch_spotify_access_token()


class _Bearer:
    """The token one call sends, replaced once if Spotify rejects it (401)."""

    def __init__(self, token):
        self.token = token

    def _adopt_cached_token(self):
        """Use the cached token if it is valid and differs from the one given.

        The orchestrator hands every call the token it fetched at the start; a
        refresh in between leaves that one stale. Adopting the cached token
        first means a refresh is paid once per job, not once per call.
        """
        cached = spotify_token_cache["token"]
        valid = spotify_token_cache["expires_at"] > time.time()
        if cached and valid and cached != self.token:
            self.token = cached

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    async def run(self, attempt, operation):
        """Run *attempt*; on a rejected token, swap it once and run it again.

        A second rejection, or no fresh token to be had, is a refusal: the
        call could not be answered, which is not "no match".
        """
        self._adopt_cached_token()
        outcome = await attempt()
        if outcome is not _TOKEN_REJECTED:
            return outcome
        fresh = await _replace_rejected_token(self.token)
        if not fresh:
            raise _refused(operation, 401)
        self.token = fresh
        outcome = await attempt()
        if outcome is _TOKEN_REJECTED:
            breaker = _job_breaker.get()
            if breaker is not None:
                breaker.trip("rejected a freshly fetched token")
            raise _refused(operation, 401)
        return outcome


async def fetch_spotify_access_token():
    """Return a valid Spotify access token, refreshing from the API if expired.

    Returns None when no token can be had (a non-200 answer, a timeout or a
    connection error on the token request), and every caller already treats
    None as "Spotify unavailable": the album pipeline falls back to Deezer
    and the spotlight keeps the artwork on screen. Missing credentials take
    that same path. They used to be `assert`ed, which `python -O` strips and
    which otherwise raised past the fallback and failed the job (F-B22-2).
    Production cannot start without them (``app._validate_api_keys``), so
    this branch is reached in dev mode only.
    """
    if spotify_token_cache["expires_at"] > time.time():
        return spotify_token_cache["token"]
    if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        logging.error("Spotify credentials are not configured; no token requested")
        return None
    url = "https://accounts.spotify.com/api/token"
    # aiohttp 3.14 deprecates BasicAuth for removal in 4.0; the documented
    # replacement is a pre-encoded Authorization header. base64 is stdlib,
    # so no new dependency.
    credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {encoded}"}
    data = {"grant_type": "client_credentials"}
    try:
        async with create_optimized_session() as s:
            async with s.post(url, data=data, headers=headers) as r:
                if r.status == 200:
                    token_data = await r.json()
                    spotify_token_cache.update(
                        {
                            "token": token_data["access_token"],
                            "expires_at": time.time()
                            + token_data["expires_in"]
                            - SPOTIFY_TOKEN_MARGIN_SECONDS,
                        }
                    )
                    return spotify_token_cache["token"]
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        # The token endpoint not answering is Spotify being unavailable, the
        # same as a non-200 answer: the caller degrades to Deezer.
        logging.error(f"Spotify token request failed: {type(exc).__name__}")
    logging.error("Failed to fetch Spotify token")
    return None


async def search_for_spotify_album_id(session, artist, album, token, semaphore=None):
    """
    Searches Spotify for a single album and returns its Spotify ID, or None
    when Spotify answered and had no match.
    Optimized: Uses relaxed query first (faster, higher success rate).

    A search Spotify could not answer is not a miss: a 429 (or a Retry-After
    above the cap), a 5xx, a timeout or a connection error that outlasts the
    retries raises ``ProviderError`` (``spotify_rate_limited`` or
    ``spotify_unavailable``). The search phase catches it per album, so that
    album falls back to Deezer and, failing that, is listed as unavailable;
    the job fails only when no search was answered and Deezer enriched nothing.

    A 400 or 403 is a refusal and raises at once; a 401 (the token was
    rejected or expired) drops the cached token once, retries with a fresh
    one, and raises if that is refused too. Once this job's breaker is tripped
    (``spotify_job_breaker``) it raises without sending a request.
    """
    _check_breaker()
    bearer = _Bearer(token)
    # Use relaxed query directly - it has better success rate and avoids double-search
    params = {"q": f"{artist} {album}", "type": "album", "limit": 3}
    limiter = get_spotify_limiter()

    async def attempt():
        async with limiter:
            _check_breaker()
            async with session.get(
                "https://api.spotify.com/v1/search",
                params=params,
                headers=bearer.headers,
            ) as response:
                if response.status == 429:
                    retry_after = parse_retry_after(response.headers.get("Retry-After"))
                    logging.warning(
                        f"Spotify 429 on spotify.search. Retry in {retry_after}s"
                    )
                    _note_retry_after(retry_after)
                    return None, retry_after, False

                if response.status >= 500:
                    # An outage, not an answer: retried, and raised as
                    # spotify_unavailable once the retries are spent.
                    return None, None, False

                if response.status == 401:
                    return _TOKEN_REJECTED

                if response.status in _REFUSAL_STATUSES:
                    raise _refused("spotify.search", response.status)

                if response.status != 200:
                    return None, None, True

                _note_answer()
                data = await response.json()
                items = data.get("albums", {}).get("items", [])
                if items:
                    return items[0].get("id"), None, True

                return None, None, True

    async def search_once():
        return await bearer.run(attempt, "spotify.search")

    return await retry_with_semaphore(
        search_once,
        retries=SPOTIFY_SEARCH_RETRIES,
        semaphore=semaphore,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=1,
        jitter=lambda a: (abs(hash((artist, album, a))) % 200) / 1000.0,
        reraise=(ProviderError,),
        error_label="spotify.search",
        failure=provider_failure("spotify"),
    )


#: Statuses that mean the Get Several Albums endpoint itself is gone, not that
#: one request failed. Spotify removed that endpoint for Development Mode apps
#: in February 2026 and postponed the removal for existing apps with no new
#: date (F-B21-59). 401 is excluded because single-album calls would fail on
#: the same token, and 5xx because an outage is no reason to multiply calls.
BATCH_ENDPOINT_GONE_STATUSES = frozenset({403, 404, 410})


class AlbumDetails(dict):
    """Album details keyed by Spotify ID, plus the IDs Spotify could not answer.

    A plain ``dict`` to every reader. ``unanswered`` holds the IDs whose
    detail call was refused or failed (a 5xx, a timeout, a 429 that outlasted
    the retries), as distinct from an ID Spotify answered but returned nothing
    for. The detail phase files those albums as unavailable, not as unmatched.
    """

    def __init__(self, details=(), unanswered=()):
        super().__init__(details)
        self.unanswered = frozenset(unanswered)


async def fetch_spotify_album_details_single(
    session, album_id, token, retries=SPOTIFY_BATCH_RETRIES
):
    """Fetch one album from GET /v1/albums/{id}; return None if unavailable.

    Returns the same album object the batch endpoint returns inside its
    `albums` list, so callers need no second extraction path. None means
    Spotify answered without the album (a 404 is that answer). A call Spotify
    could not answer (a 5xx, a timeout, a 429 that outlasts the retries, a 400
    or 403, a 401 a fresh token does not cure, a tripped job breaker) raises
    ``ProviderError``.
    """
    _check_breaker()
    url = f"https://api.spotify.com/v1/albums/{album_id}"
    bearer = _Bearer(token)
    limiter = get_spotify_limiter()

    async def attempt():
        async with limiter:
            _check_breaker()
            async with session.get(url, headers=bearer.headers) as response:
                if response.status == 200:
                    _note_answer()
                    return await response.json(), None, True
                if response.status == 429:
                    retry_after = parse_retry_after(response.headers.get("Retry-After"))
                    _note_retry_after(retry_after)
                    return None, retry_after, False
                if response.status >= 500:
                    return None, None, False
                if response.status == 401:
                    return _TOKEN_REJECTED
                if response.status in _REFUSAL_STATUSES:
                    raise _refused("spotify.album_details", response.status)
                return None, None, True

    async def fetch_once():
        return await bearer.run(attempt, "spotify.album_details")

    return await retry_with_semaphore(
        fetch_once,
        retries=retries,
        is_done=lambda t: t[2],
        get_retry_after=lambda t: t[1],
        extract_result=lambda t: t[0],
        default=None,
        backoff=lambda a: 2**a,
        jitter=lambda a: (abs(hash((album_id, a))) % 200) / 1000.0,
        reraise=(ProviderError,),
        error_label="spotify.album_details",
        failure=provider_failure("spotify"),
    )


async def _fetch_album_details_one_by_one(session, album_ids, token, retries):
    """Fetch albums individually and key them by ID, dropping unavailable ones.

    An album Spotify could not answer for is dropped and listed in the
    result's ``unanswered``; one such album does not lose its siblings.
    """
    unanswered = set()

    async def fetch_one(album_id):
        try:
            return await fetch_spotify_album_details_single(
                session, album_id, token, retries
            )
        except ProviderError:
            unanswered.add(album_id)
            return None

    tasks = [asyncio.ensure_future(fetch_one(album_id)) for album_id in album_ids]
    try:
        albums = await asyncio.gather(*tasks)
    finally:
        # An error other than ProviderError must not leave the siblings
        # running on a session that is about to close (F-B23-24).
        await cancel_and_drain(tasks)
    return AlbumDetails(
        {album["id"]: album for album in albums if album}, unanswered=unanswered
    )


async def fetch_spotify_album_details_batch(
    session,
    album_ids,
    token,
    semaphore=None,
    retries=SPOTIFY_BATCH_RETRIES,
    on_fallback=None,
):
    """
    Fetches full album details for a list of up to 50 Spotify album IDs
    in a single API call.

    When the batch endpoint answers with a status in
    BATCH_ENDPOINT_GONE_STATUSES, falls back to one GET /v1/albums/{id} call
    per album and calls ``on_fallback(status)`` so the caller can report it.

    Returns an ``AlbumDetails`` (a dict). A batch Spotify could not answer (a
    5xx, a timeout, a 429 that outlasts the retries) comes back empty with
    every requested ID in ``unanswered``: unavailable, not "no details". So
    does a batch Spotify refused (400), one whose 401 a fresh token did not
    cure, and any batch asked for after this job's breaker tripped.
    """
    if not album_ids:
        return {}
    if _breaker_open():
        return AlbumDetails(unanswered=album_ids)

    url = "https://api.spotify.com/v1/albums"
    bearer = _Bearer(token)
    # Spotify API takes a comma-separated string of IDs
    params = {"ids": ",".join(album_ids)}
    limiter = get_spotify_limiter()
    gone_status = None

    async def attempt():
        nonlocal gone_status
        async with limiter:
            _check_breaker()
            async with session.get(
                url, params=params, headers=bearer.headers
            ) as response:
                if response.status == 200:
                    _note_answer()
                    data = await response.json()
                    # response is a dict with an 'albums' key, which is a list.
                    # converts this list into a dict keyed by album ID for easy lookup.
                    return (
                        {
                            album["id"]: album
                            for album in data.get("albums", [])
                            if album
                        },
                        None,
                        True,
                    )
                if response.status == 429:
                    retry_after = parse_retry_after(response.headers.get("Retry-After"))
                    logging.warning(
                        f"⚠️ Batch fetch 429 hit. Retrying after {retry_after}s."
                    )
                    _note_retry_after(retry_after)
                    return {}, retry_after, False
                if response.status in BATCH_ENDPOINT_GONE_STATUSES:
                    gone_status = response.status
                    return {}, None, True
                if response.status >= 500:
                    return {}, None, False
                if response.status == 401:
                    return _TOKEN_REJECTED
                if response.status in _REFUSAL_STATUSES:
                    raise _refused("spotify.batch_details", response.status)
                logging.error(
                    f"Failed to fetch batch album details. Status: {response.status}, Body: {await response.text()}"
                )
                return {}, None, True

    async def fetch_once():
        return await bearer.run(attempt, "spotify.batch_details")

    try:
        details = await retry_with_semaphore(
            fetch_once,
            retries=retries,
            semaphore=semaphore,
            is_done=lambda t: t[2],
            get_retry_after=lambda t: t[1],
            extract_result=lambda t: t[0],
            default={},
            backoff=lambda a: 2**a,
            jitter=lambda a: (abs(hash((tuple(album_ids), a))) % 200) / 1000.0,
            reraise=(ProviderError,),
            error_label="spotify.batch_details",
            failure=provider_failure("spotify"),
        )
    except ProviderError:
        return AlbumDetails(unanswered=album_ids)
    if gone_status is None:
        return AlbumDetails(details)
    if on_fallback is not None:
        on_fallback(gone_status)
    return await _fetch_album_details_one_by_one(
        session, album_ids, bearer.token, retries
    )


def album_metadata_from_details(spotify_id, details):
    """Translate one Spotify album object into the provider contract.

    The one place the application reads Spotify's album JSON. The
    orchestrator's detail phase files what this returns and never drills into
    the payload itself (global rule 4, F-B22-7). A sparse payload degrades
    field by field -- no images gives ``image_url=None``, no external URL
    falls back to the album's canonical URL -- rather than raising.

    Args:
        spotify_id: The album id Spotify issued.
        details: One album object from Get Album or Get Several Albums.

    Returns:
        AlbumMetadata with ``provider="spotify"`` and track durations in
        whole seconds, keyed by ``normalize_track_name``.
    """
    images = details.get("images") or [{}]
    return AlbumMetadata(
        provider="spotify",
        album_id=spotify_id,
        url=details.get("external_urls", {}).get(
            "spotify", f"https://open.spotify.com/album/{spotify_id}"
        ),
        release_date=details.get("release_date", ""),
        image_url=images[0].get("url"),
        track_durations={
            normalize_track_name(t.get("name", "")): t.get("duration_ms", 0) // 1000
            for t in details.get("tracks", {}).get("items", [])
        },
    )


def _artist_spotlight_details(artist, artist_name=None, artist_id=None):
    """Normalize artist payloads while preserving missing-field defaults."""
    images = artist.get("images", [])
    return {
        "name": artist.get("name", artist_name),
        "artist_id": artist.get("id", artist_id),
        "image_url": images[0].get("url") if images else None,
        "spotify_url": artist.get("external_urls", {}).get("spotify"),
    }


async def _request_spotlight_artist(session, headers, artist_name, artist_id):
    """Look up by ID, falling back to name after an unsuccessful HTTP response.

    Return None for unsuccessful or empty searches. Transport and decoding
    exceptions propagate to the caller's shared logging and fallback boundary.
    """
    if artist_id:
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return _artist_spotlight_details(
                    await response.json(), artist_name, artist_id
                )
    if artist_name:
        params = {"q": f"artist:{artist_name}", "type": "artist", "limit": 1}
        async with session.get(
            "https://api.spotify.com/v1/search", params=params, headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                items = data.get("artists", {}).get("items", [])
                if items:
                    return _artist_spotlight_details(items[0], artist_name)
    return None


async def fetch_spotify_artist_spotlight(
    session, artist_name=None, artist_id=None, token=None
):
    """Fetch optional spotlight metadata within the limiter, logging failures.

    Missing credentials or identifiers and failed lookups return None so
    callers can retain the album artwork already displayed on the card.
    """
    if not token or (not artist_name and not artist_id):
        return None

    headers = {"Authorization": f"Bearer {token}"}
    limiter = get_spotify_limiter()
    try:
        async with limiter:
            return await _request_spotlight_artist(
                session, headers, artist_name, artist_id
            )
    # The spotlight is decorative; None keeps the card's existing artwork.
    except Exception as e:  # noqa: BLE001
        logging.warning(f"Error in spotify.artist_spotlight: {type(e).__name__}")
    return None
