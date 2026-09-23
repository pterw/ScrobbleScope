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
    participant Repo as repositories.py / JOBS
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
        Routes->>LastFM: Read the registration year
        alt Year predates the registration year
            Routes-->>Browser: index.html + error
        else Registration year satisfied, unknown, or lookup failed
            Routes->>Repo: cleanup_expired_jobs()
            Routes->>Worker: acquire_job_slot()
            alt Slot exhausted
                Worker-->>Routes: False
                Routes-->>Browser: Too many requests, no job created
            else Slot acquired
                Worker-->>Routes: True
                Routes->>Repo: create_job(params)
                Repo-->>Routes: UUID job_id
                Routes->>Worker: start_job_thread(background_task, args)
                alt Thread start fails
                    Worker->>Worker: release_job_slot()
                    Worker-->>Routes: Re-raise startup exception
                    Routes->>Repo: delete_job(job_id)
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
            Orch->>Repo: cleanup_expired_jobs()
            Orch->>Repo: Initialize progress at 0%
            Orch->>Repo: Progress 5%
            Orch->>LastFM: Fetch paginated recent tracks
            loop Each page with retry and global throttling
                LastFM-->>Orch: Scrobbles + page progress
                Orch->>Repo: Progress 5%-20%
            end
            Orch->>Orch: Group, normalize, and partition by threshold (inside fetch_top_albums_async)
            Orch->>Repo: Persist one below_threshold exclusion per album, with its counts and failed thresholds
            Note over Orch,Repo: Threshold exclusions are partitioned before Spotify, so they cost no Spotify quota
            Orch->>Repo: Aggregation stats, and partial_data_warning when pages were dropped
            alt Terminal Last.fm failure
                Orch->>Repo: set_job_error(lastfm_unavailable)
                Note over Orch,Repo: set_job_error also stores an empty result list
            else Pages available
                alt No albums pass filters
                    Orch->>Repo: Store empty results and progress 100%
                    Note over Orch,Repo: Terminal -- no pre-slice, cache, or Spotify
                else Albums pass filters
                    Orch->>Repo: Progress 20%
                    Orch->>Orch: Pre-slice eligible albums to _MAX_ALBUM_CAP 500 for every sort mode
                    Orch->>Repo: Progress 20% + prepared album count
                    Orch->>Cache: Open connection (None when DB disabled)
                    Orch->>Repo: set_job_stat(db_cache_enabled)
                    alt DB unavailable
                        Orch->>Repo: set_job_stat(db_cache_warning)
                        Note over Orch,Cache: No lookup, cleanup, or persistence -- every album is a miss
                    else DB connected
                        Orch->>Cache: Batch lookup all album keys
                        alt Lookup fails
                            Orch->>Repo: set_job_stat(db_cache_warning), cached metadata stays empty
                            Note over Orch,Cache: Fail-open -- every album becomes a miss, persistence still allowed
                        else Lookup succeeds
                            Cache-->>Orch: Matching in-TTL rows only
                            Orch->>Repo: set_job_stat(db_cache_lookup_hits)
                        end
                        Orch->>Cache: Clean stale rows (both lookup outcomes)
                    end
                    Orch->>Orch: Partition cache hits and misses (runs with or without a connection)
                    Orch->>Repo: set_job_stat(cache_hits)

                    alt Cache misses exist
                        Orch->>Spotify: Fetch token
                        alt Token fetch fails
                            Orch->>Repo: set_job_stat(partial_data_warning)
                            Note over Orch,Spotify: No search or detail call; every miss goes to Deezer
                        else Token acquired
                            Orch->>Spotify: Search albums
                            Spotify-->>Orch: Spotify IDs, or search misses
                            Orch->>Repo: Progress 20%-40%
                            opt At least one album matched
                                Orch->>Spotify: Batch-fetch matched album details
                                Spotify-->>Orch: Dates, art, and track durations
                                Orch->>Repo: Progress 40%-60%
                                Note over Orch: A matched album promotes into cache_hits
                            end
                        end
                        opt Misses remain -- a search miss, a detail failure, or no token
                            Orch->>Deezer: Search, then fetch detail and track list, per album
                            Deezer-->>Orch: Date, art, and track durations
                            Orch->>Repo: Progress 60%-75%
                            alt No token, nothing was cached beforehand, and Deezer matched nothing
                                Orch->>Orch: raise SpotifyUnavailableError
                            else At least one album enriched, or cache hits existed
                                Note over Orch: Continue -- a partly enriched run is a valid outcome
                            end
                        end
                        opt Albums neither provider could enrich
                            Orch->>Repo: Unmatched reason No match on Spotify or Deezer
                        end
                        opt DB connected and new metadata rows exist
                            Orch->>Cache: Persist fresh metadata
                            Orch->>Repo: set_job_stat(db_cache_persisted)
                            Note over Orch,Cache: A persist failure is non-fatal and sets db_cache_warning
                        end
                    else All metadata is cached
                        Note over Orch,Spotify: No Spotify or Deezer call, while JOBS stats still update
                    end
                    opt DB connected
                        Orch->>Cache: Close connection
                        Note over Orch,Cache: Closed in a finally, so it also closes while SpotifyUnavailableError unwinds
                    end

                    alt SpotifyUnavailableError reached background_task
                        Orch->>Repo: set_job_error(spotify_unavailable)
                        Note over Orch,Repo: Terminal -- no merge, and the stored result list is empty
                    else Metadata available
                        Orch->>Repo: set_job_stat(spotify_matched and spotify_unmatched)
                        Orch->>Orch: Apply release filter, compute playtime, and rank
                        Orch->>Repo: Unmatched entries for albums failing the release filter
                        Orch->>Repo: get_job_context(job_id) to count No Spotify match entries
                        alt Every album returned No Spotify match
                            Orch->>Repo: set_job_error(spotify_unavailable)
                        else Ranked results, possibly emptied by the release filter
                            Orch->>Repo: Progress 60%-90%
                            Orch->>Orch: Post-slice to limit_results
                            Orch->>Repo: Store results and progress 100%
                            Orch->>Repo: enqueue_release_check(job_id)
                            Note over Orch,ReleaseChecks: Queued on a FIFO, never awaited -- and only here, because an error path stores an empty list worth no correction
                        end
                    end
                end
            end
            opt A correction pass was queued
                ReleaseChecks->>Repo: Read this job's candidate albums
                ReleaseChecks->>Cache: Look up the findings already known
                loop Each album still unknown, capped per job
                    ReleaseChecks->>MusicBrainz: Look up the release group's first-release-date
                    MusicBrainz-->>ReleaseChecks: A trusted match, or nothing close enough
                    ReleaseChecks->>Cache: Persist the finding, hit and miss alike
                    ReleaseChecks->>Repo: Mark a moved-out row in place
                end
                ReleaseChecks->>Repo: set_job_release_check(running, then done)
            end
            opt Unhandled exception inside _fetch_and_process
                Orch->>Repo: Classified error code, or empty results with a retryable unknown error
            end
            opt Exception escaping that handler
                Orch->>Repo: set_job_error(internal_error)
                Note over Orch,Repo: background_task logs it and publishes internal_error, so a polling page stops
            end
            Orch->>Worker: release_job_slot()
            Note over Orch,Worker: In worker.run_coroutine_in_new_loop's finally, called from background_task -- always reached because event-loop setup is inside the try block
        and Browser polls progress
            loop Poll until 100% or an error
                Browser->>Routes: GET /progress?job_id=...
                Routes->>Repo: get_job_progress(job_id)
                alt Job missing or expired
                    Routes-->>Browser: JSON 404 with error true
                else Job found
                    Repo-->>Routes: Progress, stats, error state, and retry metadata
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
                Routes->>Repo: get_job_context(job_id)
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
                        Note over Browser,Routes: below_threshold, then release_scope, then no_spotify_match
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

`set_job_error` writes an empty result list as well as the error state, so an
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

`SpotifyUnavailableError` is raised on three conditions together -- no token,
nothing cached before this call, and Deezer matched nothing -- so a Deezer-only
run that finds even one album is a valid partial outcome rather than a failure.
An earlier revision of this diagram drew the no-cache-hits case as an immediate
raise, which was wrong before Batch 22 added Deezer and is wrong now.

The correction pass is queued, never awaited, and is enqueued only on the happy
path: the error handlers below it store an empty result list, and an empty list
has nothing to correct. `release_checks.py` runs it on its own thread with a
FIFO queue of job ids, which is why it appears as a separate lifeline rather
than an `Orch` arrow. `GET /api/release_checks` is what the open results page
polls for the findings; that poll is not drawn here, because this view ends at
the results document.
