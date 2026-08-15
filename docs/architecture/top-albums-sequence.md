# Top Albums request and enrichment sequence

This diagram is the canonical owner of the Top Albums pipeline sequence. The
concurrency slot is acquired before job creation, and every acquired slot is
released on thread-start failure or when the background task exits.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Browser
    participant Routes as routes.py
    participant Worker as worker.py
    participant Repo as repositories.py / JOBS
    participant Orch as orchestrator.py
    participant LastFM as Last.fm API
    participant Cache as cache.py / PostgreSQL
    participant Spotify as Spotify API

    User->>Browser: Submit username, year, filters, and sort
    Browser->>Routes: POST /results_loading + CSRF token
    Routes->>Routes: Validate required fields, numbers, and year range
    Routes->>LastFM: Check registration year metadata
    alt Invalid input or year predates known registration
        Routes-->>Browser: index.html + error
    else No blocking validation result
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

    opt Job admitted and daemon thread started
        par Background task runs
            Worker->>Orch: background_task(job_id, parameters)
            Orch->>Repo: Initialize progress at 0%
            Orch->>LastFM: Fetch paginated recent tracks
            loop Each page with retry and global throttling
                LastFM-->>Orch: Scrobbles + page progress
                Orch->>Repo: Progress 5%-20% + stats
            end
            alt Terminal Last.fm failure
                Orch->>Repo: set_job_error(lastfm_unavailable)
            else Pages available
                opt Partial pages returned
                    Orch->>Repo: set_job_stat(partial_data_warning)
                    Note over Orch,Repo: Continue with the available pages
                end
                Orch->>Orch: Group, normalize, threshold, and pre-slice albums
                Orch->>Repo: Progress 20%
                Orch->>Cache: Open connection (None when DB disabled)
                alt DB unavailable
                    Note over Orch,Cache: Lookup, cleanup, and persistence skipped (all albums become misses)
                else DB connected
                    Orch->>Cache: Batch lookup all album keys
                    Cache-->>Orch: Matching in-TTL rows only
                    Orch->>Cache: Clean stale rows
                    Orch->>Orch: Partition cache hits and misses
                end

                alt Cache misses exist
                    Orch->>Spotify: Fetch token
                    alt Token fetch fails
                        alt Cache hits exist
                            Orch->>Repo: Record partial_data_warning and proceed with cached albums only
                            Note over Orch,Spotify: Success with cached albums only
                        else No cache hits
                            Orch->>Repo: set_job_error(spotify_unavailable)
                            Note over Orch,Spotify: Terminal -- pipeline stops, no merge or store
                        end
                    else Token acquired
                        Orch->>Spotify: Search albums
                        Spotify-->>Orch: Spotify IDs or unmatched results
                        Orch->>Repo: Progress 20%-40% + unmatched reasons
                        Orch->>Spotify: Batch-fetch matched album details
                        Spotify-->>Orch: Dates, art, and track durations
                        Orch->>Repo: Progress 40%-60%
                        Orch->>Cache: Persist fresh metadata
                    end
                else All metadata is cached
                    Note over Orch,Spotify: No Spotify call or cache persistence, while JOBS stats still update
                end

                alt Results available
                    Orch->>Orch: Merge metadata, compute playtime, and rank
                    Orch->>Repo: Store results, unmatched entries, stats, and progress
                else Terminal failure
                    Note over Orch,Repo: No merge or store -- job already errored
                end
            end
            Orch->>Worker: release_job_slot()
            Note over Orch,Worker: Unconditional in background_task finally, on success or failure
        and Browser polls progress
            loop Poll until terminal state
                Browser->>Routes: GET /progress?job_id=...
                Routes->>Repo: get_job_progress(job_id)
                Repo-->>Routes: Progress, stats, errors, and retry metadata
                Routes-->>Browser: JSON progress payload
            end
        end

        alt Complete
            Browser->>Routes: POST /results_complete + job_id
            Routes->>Repo: get_job_context(job_id)
            Repo-->>Routes: Results + unmatched data
            Routes-->>Browser: results.html
        else Upstream or fatal failure
            Routes-->>Browser: Stable error state + retry metadata
        end
    end
```

The cache lookup returns hits only; the orchestrator partitions the full
candidate set after lookup. Cached metadata avoids Spotify and cache
persistence, but the pipeline still writes cache statistics and final job
state to `repositories.py / JOBS`.
