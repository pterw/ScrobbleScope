# Heatmap request and rendering sequence

This diagram is the canonical owner of the heatmap pipeline sequence. Partial
Last.fm data is a successful result with a warning, while terminal fetch
failure produces an error.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as heatmap.js
    participant Routes as routes.py
    participant Worker as worker.py
    participant Repo as repositories.py / JOBS
    participant Heatmap as heatmap.py
    participant LastFM as Last.fm API

    User->>UI: Select Heatmap and enter username
    UI->>Routes: POST /heatmap_loading + CSRF token
    Routes->>Routes: Trim and require username
    alt Username missing
        Routes-->>UI: JSON 400
    else Username present
        Routes->>LastFM: _check_user_exists(username)
        alt Validation service unavailable
            LastFM-->>Routes: Exception
            Routes-->>UI: JSON 503, retryable true
        else User not found
            LastFM-->>Routes: exists false
            Routes-->>UI: JSON 404, retryable false
        else User exists
            LastFM-->>Routes: exists true
            Routes->>Repo: cleanup_expired_jobs()
            Routes->>Worker: acquire_job_slot()
            alt Slot exhausted
                Worker-->>Routes: False
                Routes-->>UI: JSON 429, retryable true
            else Slot acquired
                Worker-->>Routes: True
                Routes->>Repo: create_job(mode heatmap)
                Repo-->>Routes: UUID job_id
                Routes->>Worker: start_job_thread(heatmap_task, args)
                alt Thread start fails
                    Worker->>Worker: release_job_slot()
                    Worker-->>Routes: Re-raise startup exception
                    Routes->>Repo: delete_job(job_id)
                    Routes-->>UI: JSON 500
                else Daemon thread started
                    Routes-->>UI: JSON 202 with job_id
                end
            end
        end
    end

    opt Job admitted and daemon thread started
        par Background task runs
            Worker->>Heatmap: heatmap_task(job_id, username)
            Heatmap->>Repo: Initialize progress at 0%
            Heatmap->>LastFM: Fetch last 365 days of recent tracks
            loop Paginated pages, 5%-80% progress
                LastFM-->>Heatmap: Raw scrobble page
                Heatmap->>Repo: Store page progress
            end
            alt Terminal Last.fm failure
                Heatmap->>Repo: set_job_error(lastfm_unavailable)
            else Pages available
                opt Partial pages returned
                    Heatmap->>Repo: set_job_stat(partial_data_warning)
                    Note over Heatmap,Repo: Continue with the available pages
                end
                Heatmap->>Heatmap: Decode UTC timestamps and filter boundaries
                Heatmap->>Heatmap: Aggregate daily counts and statistics
                alt No scrobbles in range
                    Heatmap->>Repo: set_job_error(no_scrobbles_in_range)
                else Results available
                    Heatmap->>Repo: Store daily_counts and progress 100%
                end
            end
            Heatmap->>Worker: release_job_slot()
            Note over Heatmap,Worker: Unconditional in heatmap_task finally, on success or failure
        and UI polls progress
            loop Poll until terminal state
                UI->>Routes: GET /progress?job_id=...
                Routes->>Repo: get_job_progress(job_id)
                Repo-->>Routes: Progress, warning, or error state
                Routes-->>UI: JSON progress payload
            end
        end

        alt Progress reaches 100%
            UI->>Routes: GET /heatmap_data?job_id=...
            Routes->>Repo: get_job_context(job_id)
            Routes-->>UI: JSON 200, ready true + results
            UI->>UI: Render responsive SVG and KPIs
        else Still processing
            UI->>Routes: GET /heatmap_data?job_id=...
            Routes-->>UI: JSON 202, ready false
        else Terminal error
            Note over UI,Routes: Polling stops, so heatmap_data is not requested
        end
    end
```

The pipeline stores `partial_data_warning` in job stats and continues through
aggregation. `/heatmap_data` therefore returns `ready: true` when partial data
still yields results.
