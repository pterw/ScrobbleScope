# Top Albums request and enrichment sequence

This diagram is the canonical owner of the Top Albums pipeline sequence:
admission, Last.fm retrieval, enrichment across two metadata providers, the
deferred MusicBrainz correction pass, result storage, and polling.

The concurrency slot is acquired before job creation. `start_job_thread` releases
the slot when the thread does not start; once the thread runs, `background_task`
is a single call into `worker.run_coroutine_in_new_loop`, which owns the
build-run-close-release protocol -- the event-loop setup sits inside the `try`
that its `finally` guards, so the release is unconditional: a failure to
create the loop is caught and logged like any other, and the slot still comes
back. `background_task` supplies only the reaction to a failed run (logging).

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Browser
    participant Routes as routes/
    participant Worker as worker.py
    participant Jobs as jobs.py / job store
    participant Orch as orchestrator/
    participant LastFM as Last.fm API
    participant Cache as cache.py / PostgreSQL
    participant Spotify as Spotify API
    participant Deezer as Deezer API
    participant ReleaseChecks as release_checks.py
    participant MusicBrainz as MusicBrainz API

    User->>Browser: Submit username, year, filters, and sort
    Browser->>Routes: POST /results_loading + CSRF token
    alt Missing field, non-numeric input, or year outside 2002 to this year
        Routes-->>Browser: index.html + error
    else Input valid
        Routes->>LastFM: Check that the user exists (and read the registration year), then that recent listening is public
        alt User not found
            Routes-->>Browser: index.html + "not found" message, no privacy check made
        else Recent listening is private (HTTP 403, error 17)
            Routes-->>Browser: index.html + private-profile message
        else Year predates the registration year
            Routes-->>Browser: index.html + error
        else Registration year satisfied, unknown, or either lookup failed
            Note over Routes,LastFM: A failed lookup is logged and the search proceeds without the hint; only a confirmed missing user or private profile refuses
            Routes->>Jobs: expire_stale()
            Routes->>Worker: acquire_job_slot()
            alt Slot exhausted
                Worker-->>Routes: False
                Routes-->>Browser: Too many requests, no job created
            else Slot acquired
                Worker-->>Routes: True
                Routes->>Jobs: create(params)
                Jobs-->>Routes: UUID job_id
                Routes->>Worker: start_job_thread(background_task, args)
                alt Thread start fails
                    Worker->>Worker: release_job_slot()
                    Worker-->>Routes: Re-raise startup exception
                    Routes->>Jobs: delete(job_id)
                    Routes-->>Browser: Failed to start processing
                else Daemon thread started
                    Routes-->>Browser: loading.html(job_id)
                end
            end
        end
    end

    opt Job admitted and daemon thread started
        par Background task runs
            Worker->>Orch: background_task(job_id, parameters)
            Orch->>Orch: cleanup_expired_cache() from utils (REQUEST_CACHE)
            Orch->>Jobs: expire_stale()
            Orch->>Jobs: Initialize progress at 0%
            Orch->>Jobs: Progress 5%
            Orch->>LastFM: Fetch paginated recent tracks
            loop Each page with retry and global throttling
                LastFM-->>Orch: Scrobbles + page progress
                Orch->>Jobs: Progress 5%-20%
            end
            Orch->>Orch: Group, normalize, and partition by threshold (inside fetch_top_albums_async)
            Orch->>Jobs: Aggregation stats, and partial_data_warning plus record_partial_source(lastfm) when pages were dropped (failed, or malformed after every retry)
            alt Terminal Last.fm failure
                Orch->>Jobs: fail(lastfm_unavailable)
                Note over Orch,Jobs: jobs.fail also stores an empty result list
            else Pages available
                Orch->>Jobs: Persist one below_threshold exclusion per album, with its counts and failed thresholds
                Note over Orch,Jobs: Threshold exclusions are partitioned before Spotify, so they cost no Spotify quota
                alt No albums pass filters
                    Orch->>Jobs: succeed: empty results and progress 100%, in one write
                    Note over Orch,Jobs: Terminal -- no pre-slice, cache, or Spotify
                else Albums pass filters
                    Orch->>Jobs: Progress 20%
                    Orch->>Orch: Pre-slice eligible albums to _MAX_ALBUM_CAP 500 for every sort mode
                    Orch->>Jobs: Progress 20% + prepared album count
                    Orch->>Cache: Open connection (None when DB disabled)
                    Orch->>Jobs: record_stat(db_cache_enabled)
                    alt DB unavailable
                        Orch->>Jobs: record_stat(db_cache_warning)
                        Note over Orch,Cache: No lookup, cleanup, or persistence -- every album is a miss
                    else DB connected
                        Orch->>Cache: Batch lookup all album keys
                        alt Lookup fails
                            Orch->>Jobs: record_stat(db_cache_warning), cached metadata stays empty
                            Note over Orch,Cache: Fail-open -- every album becomes a miss, persistence still allowed
                        else Lookup succeeds
                            Cache-->>Orch: Matching in-TTL rows only
                            Orch->>Jobs: record_stat(db_cache_lookup_hits)
                        end
                        Orch->>Cache: Clean stale rows (both lookup outcomes)
                    end
                    Orch->>Orch: Partition cache hits and misses (runs with or without a connection)
                    Orch->>Jobs: record_stat(cache_hits)

                    alt Cache misses exist
                        Note over Orch,Jobs: Every partial_data_warning below (token, search, details, Deezer fallback) also calls record_partial_source(provider)
                        Orch->>Spotify: Fetch token
                        alt Token fetch fails (a non-200 answer, a timeout, or a refused connection)
                            Orch->>Jobs: record_stat(partial_data_warning) and record_partial_source(provider)
                            Note over Orch,Spotify: No search or detail call; every miss goes to Deezer
                        else Token acquired
                            Orch->>Spotify: Search albums
                            Spotify-->>Orch: Spotify IDs, search misses, or searches it could not answer (429, 5xx, timeout)
                            Note over Orch: An unanswered album degrades to Deezer; the siblings carry on
                            Orch->>Jobs: Progress 20%-40%
                            opt At least one album matched
                                Orch->>Spotify: Batch-fetch matched album details
                                Spotify-->>Orch: Dates, art, and track durations
                                Orch->>Jobs: Progress 40%-60%
                                Note over Orch: A matched album promotes into cache_hits
                            end
                        end
                        opt Misses remain -- a search miss, an unanswered search, a detail failure, or no token
                            Orch->>Deezer: Search, then fetch detail and track list, per album
                            Deezer-->>Orch: Date, art, and track durations
                            Orch->>Jobs: Progress 60%-75%
                            alt Spotify gave nothing for every miss (an unanswered search or unanswered details), nothing was cached beforehand, and Deezer matched nothing
                                Orch->>Orch: raise SpotifyUnavailableError
                            else At least one album enriched, or cache hits existed
                                Note over Orch: Continue -- a partly enriched run is a valid outcome
                            end
                        end
                        opt Albums neither provider could enrich
                            Orch->>Jobs: Unmatched reason No match on Spotify or Deezer, or Could not be checked when a provider did not answer
                        end
                        opt DB connected and new metadata rows exist
                            Orch->>Cache: Persist fresh metadata
                            Orch->>Jobs: record_stat(db_cache_persisted)
                            Note over Orch,Cache: A persist failure is non-fatal and sets db_cache_warning
                        end
                    else All metadata is cached
                        Note over Orch,Spotify: No Spotify or Deezer call, while job stats still update
                    end
                    opt DB connected
                        Orch->>Cache: Close connection
                        Note over Orch,Cache: Closed in a finally, so it also closes while SpotifyUnavailableError unwinds
                    end

                    alt SpotifyUnavailableError reached background_task
                        Orch->>Jobs: fail(spotify_unavailable)
                        Note over Orch,Jobs: Terminal -- no merge, and the stored result list is empty
                    else Metadata available
                        Orch->>Jobs: record_stat(spotify_matched and spotify_unmatched)
                        Orch->>Orch: Apply release filter, compute playtime, and rank
                        Orch->>Jobs: Unmatched entries for albums failing the release filter
                        Note over Orch,Jobs: Ranked results, possibly emptied by the release filter or because every album was No match -- a finished run, never a failure
                        Orch->>Jobs: Progress 60%-90%
                        Orch->>Orch: Post-slice to limit_results
                        Orch->>Jobs: succeed: results and progress 100%, in one write
                        Orch->>ReleaseChecks: enqueue_release_check(job_id)
                        Note over Orch,ReleaseChecks: Queued on a FIFO, never awaited -- and only here, because an error path stores an empty list worth no correction
                    end
                end
            end
            opt A correction pass was queued
                ReleaseChecks->>Jobs: Read this job's candidate albums
                ReleaseChecks->>Cache: Look up the findings already known
                loop Each album still unknown, capped per job
                    ReleaseChecks->>MusicBrainz: Look up the release group's first-release-date
                    MusicBrainz-->>ReleaseChecks: A trusted match, or nothing close enough
                    ReleaseChecks->>Cache: Persist the finding, hit and miss alike
                    ReleaseChecks->>Jobs: Mark a moved-out row in place
                end
                ReleaseChecks->>Jobs: record_stat(release_check: running, then done)
            end
            opt Unhandled exception inside _fetch_and_process
                Orch->>Jobs: fail(classified code, else internal_error): empty results, no exception text shown
            end
            opt Exception escaping that handler
                Orch->>Jobs: fail(internal_error)
                Note over Orch,Jobs: background_task logs it and publishes internal_error, so a polling page stops
            end
            Orch->>Worker: release_job_slot()
            Note over Orch,Worker: In worker.run_coroutine_in_new_loop's finally, called from background_task -- always reached because event-loop setup is inside the try block
        and Browser polls progress
            loop Poll until 100% or an error
                Browser->>Routes: GET /progress?job_id=...
                Routes->>Jobs: progress(job_id)
                alt Job missing or expired
                    Routes-->>Browser: JSON 404 with error true
                else Job found
                    Jobs-->>Routes: Progress, stats, error state, and retry metadata
                    Routes-->>Browser: JSON 200 progress payload
                end
            end
        end

        alt Payload carries an error
            Browser->>Browser: Stop polling and show the error
            alt Error is retryable
                Browser->>Browser: Offer Retry and stay on the loading page
                Note over Browser,Routes: The browser stays on canonical /loading on this path
            else Error is not retryable
                Browser->>Browser: Wait three seconds
                Browser->>Routes: GET /results?job_id=...
                Routes-->>Browser: error.html -- Processing Error
                Note over Browser,Routes: Same handler as the 100% path, taking its Job errored branch
            end
        else Progress reaches 100%
            Browser->>Routes: GET /results?job_id=...
            alt job_id missing
                Routes-->>Browser: error.html -- Missing Job Identifier
            else job_id present
                Routes->>Jobs: context(job_id)
                alt Job unknown or expired
                    Routes-->>Browser: error.html -- Results Not Found
                else Job errored
                    Routes-->>Browser: error.html -- Processing Error
                else Results not stored yet
                    Routes-->>Browser: error.html -- Results Still Processing
                else No album survived the display filter
                    Routes-->>Browser: results.html with no_matches
                else Results present
                    Routes-->>Browser: results.html
                    opt User opens the unmatched list
                        Browser->>Routes: GET /unmatched?job_id=...
                        Routes-->>Browser: unmatched.html, one panel per reason, sorted by reason code
                        Note over Browser,Routes: below_threshold, release_scope, no_spotify_match, then provider_unavailable
                    end
                end
            end
        end
    end
```

Grouping and threshold filtering happen inside `fetch_top_albums_async`, so
they run before every downstream branch. The Last.fm failure terminal and the
empty-result terminal simply discard the grouped set. The cache lookup returns
hits only, and the hit/miss partition runs on the full candidate set whether or
not a connection was opened.

`jobs.fail` writes an empty result list as well as the error state, so an
errored job holds `[]` rather than `None`. `results_complete` depends on that
difference: `None` means the results are not stored yet.

`Orch` self-arrows cover in-process work across the `orchestrator/` package
(a facade `__init__.py` plus `_search.py`, `_details.py`, `_cache.py`,
`_deezer_fallback.py`, `_results.py` as of Batch 22 WP-0 and WP-1) and helpers
it imports from `utils.py` and `domain.py`, none of which are drawn as separate
participants -- this view stays at the pipeline level, not the module-split
level. The `/progress` handler also returns HTTP 400 for a missing `job_id`;
the loading page always sends one, so that response is not drawn.

`_fetch_spotify_misses` owns the whole enrichment chain, and the order in it is
load-bearing. A Spotify match promotes into `cache_hits`; whatever is still
missing afterwards is computed as `cache_misses` minus `cache_hits`, so a
search miss and a detail failure converge on the same Deezer pass rather than
being retried separately. Persistence happens in the caller (Phase 4) after
that call returns, which is why the diagram shows it after Deezer: one row set
is written for both providers, not one per provider.

`SpotifyUnavailableError` is raised on three conditions together -- Spotify
gave nothing for every miss (no token, or every miss either a search it did not
answer or a matched album whose details it did not answer), nothing cached
before this call, and Deezer matched nothing -- so a run that finds even one
album is a valid partial outcome rather than a failure. A "no match" answer is
an answer: it keeps the run alive here, and a run where both providers answered
"no match" for every album succeeds with no albums (owner ruling 2026-09-30):
the Results page says none were found and links to the Unmatched breakdown,
where each album reads "No match on Spotify or Deezer".
An earlier revision of this diagram drew the no-cache-hits case as an immediate
raise, which was wrong before Batch 22 added Deezer and is wrong now.

Errors are classified by type, not by message text. A provider call that
cannot be answered -- a 429 or a Retry-After above the cap, a 5xx, a timeout,
and for Spotify a 400 or 403 or a 401 that a fresh token does not cure; for
Deezer an HTTP 429 or 403 -- raises `ProviderError`, never a "no match". A
Spotify token is refreshed a minute before it expires, and a 401 drops the
cached token once and retries once with a fresh one. Within one job (one
event loop) the refresh is single-flight: concurrent expiries or 401s cost one
token request, and if it fails the calls waiting on it get no token. Once a
Spotify call meets a Retry-After above the cap, or refuses three requests in a
row, or rejects a freshly fetched token, that job sends Spotify no further
requests (a per-job breaker, checked again right before each request so a
queued call is stopped too; another job is unaffected) and its remaining
albums go to Deezer. For Spotify the search phase
catches it per album: the album degrades to Deezer, and if Deezer has nothing
either it is listed under the distinct `provider_unavailable` reason, not as a
no-match. The same holds for an album Spotify's search matched but whose detail
call (batch or single) it could not answer. Each row's text says which provider
was unavailable and which had no match. Only when Spotify gave nothing for every miss (no search or details call
answered) and Deezer enriched nothing does the job fail, as the retryable
`spotify_unavailable`. A Deezer or
MusicBrainz call that cannot be answered degrades too: the album is left
unenriched (Deezer: listed as unavailable), no finding is cached for
MusicBrainz, and the job carries a partial-data warning. Any exception nothing
classifies is our bug and publishes `internal_error`, with no exception text
shown.

The correction pass is queued, never awaited, and is enqueued only on the happy
path: the error handlers below it store an empty result list, and an empty list
has nothing to correct. `release_checks.py` runs it on its own thread with a
FIFO queue of job ids, which is why it appears as a separate lifeline rather
than an `Orch` arrow. `GET /api/release_checks` is what the open results page
polls for the findings; that poll is not drawn here, because this view ends at
the results document.
