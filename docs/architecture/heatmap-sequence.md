# Heatmap request and rendering sequence

Last updated: 2026-10-28

This diagram is the canonical owner of the heatmap pipeline sequence. Partial
Last.fm data is a successful result with a warning, while terminal fetch
failure produces an error.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as heatmap.js
    participant Routes as routes/
    participant Worker as worker.py
    participant Jobs as jobs.py / job store
    participant Heatmap as heatmap.py
    participant LastFM as Last.fm API

    User->>UI: Open /heatmap and enter username
    UI->>Routes: POST /heatmap_loading + CSRF token
    Note over UI,Routes: /heatmap is the canonical page. /loading stays the transient job route
    Routes->>Routes: Trim and require username
    alt Username missing
        Routes-->>UI: JSON 400
    else Username present
        Routes->>LastFM: Check that the user exists
        alt Validation service unavailable
            LastFM-->>Routes: Exception
            Routes-->>UI: JSON 503, retryable true
        else User not found
            LastFM-->>Routes: exists false
            Routes-->>UI: JSON 404, retryable false
        else Recent listening is private (HTTP 403, error 17)
            LastFM-->>Routes: private
            Routes-->>UI: JSON 403 private_profile, retryable false
        else User exists and listening is public
            LastFM-->>Routes: exists true, public
            Routes->>Jobs: expire_stale()
            Routes->>Worker: acquire_job_slot()
            alt Slot exhausted
                Worker-->>Routes: False
                Routes-->>UI: JSON 429, retryable true
            else Slot acquired
                Worker-->>Routes: True
                Routes->>Jobs: create(mode heatmap)
                Jobs-->>Routes: UUID job_id
                Routes->>Worker: start_job_thread(heatmap_task, job_id)
                alt Thread start fails
                    Worker->>Worker: release_job_slot()
                    Worker-->>Routes: Re-raise startup exception
                    Routes->>Jobs: delete(job_id)
                    Routes-->>UI: JSON 500
                else Daemon thread started
                    Routes-->>UI: JSON 202 with job_id
                end
            end
        end
    end

    opt Job admitted and daemon thread started
        Note over UI,Routes: A saved job that is already cached keeps the loading panel hidden and fades its result in directly
        par Background task runs
            Worker->>Heatmap: heatmap_task(job_id)
            Heatmap->>Jobs: params(job_id), the username admission stored
            Heatmap->>Heatmap: cleanup_expired_cache() from utils (REQUEST_CACHE)
            Heatmap->>Jobs: expire_stale()
            Heatmap->>Jobs: start: progress 0%, stats cleared
            Heatmap->>Jobs: Progress 5%
            Heatmap->>LastFM: Fetch last 365 days of recent tracks (lastfm.fetch_scrobbles)
            loop Paginated pages, 5%-80% progress
                LastFM-->>Heatmap: Page of scrobbles, turned into plays inside lastfm.py
                Heatmap->>Jobs: Store page progress
            end
            alt Terminal Last.fm failure
                Note over Heatmap,Jobs: fetch_scrobbles raises ProviderError(lastfm unavailable), and the unhandled-exception path below publishes lastfm_unavailable
            else Plays available
                Heatmap->>Jobs: record_stat(pages_expected and pages_received)
                opt Partial pages returned
                    Heatmap->>Jobs: record_stat(partial_data_warning)
                    Note over Heatmap,Jobs: Continue with the available pages
                end
                Heatmap->>Jobs: Progress 80%
                Heatmap->>Heatmap: plays.aggregate_daily_counts: the UTC day of each play, boundaries filtered, empty days filled
                Heatmap->>Heatmap: plays.aggregate_weekly_artist_counts: plays per Monday-first week for the top 10 artists, the rest counted as other
                Heatmap->>Heatmap: total, max_count and active_days from the daily counts, total_scrobbles and active_days recorded as stats
                Heatmap->>Heatmap: heatmap_statistics(daily_counts, UTC window end): streak, best day, average, total, each with its population
                Note over Heatmap: Streak, best day and average are computed here, not in the browser
                alt No scrobbles in range
                    Heatmap->>Jobs: fail(no_scrobbles_in_range)
                else Results available
                    Heatmap->>Jobs: succeed: daily_counts, weekly_artists, statistics and progress 100%, in one write
                end
            end
            opt Unhandled exception anywhere above
                Heatmap->>Jobs: fail(classified code, else internal_error)
                Note over Heatmap,Jobs: Classifies via errors.classify_exception_to_error_code (e.g. a Last.fm 404 -> user_not_found), the classifier the album pipeline also calls, by exception type and never by message text, and an unrecognized fault is ours and prevents the polling client from hanging. The album pipeline's fallback is the same (see the Top Albums sequence)
            end
            Heatmap->>Worker: release_job_slot()
            Note over Heatmap,Worker: In worker.run_coroutine_in_new_loop's finally, called from heatmap_task -- always reached because event-loop setup is inside the try block
        and UI polls progress
            loop Poll until 100% or an error
                UI->>Routes: GET /progress?job_id=...
                Routes->>Jobs: progress(job_id)
                alt Job missing or expired
                    Routes-->>UI: JSON 404 with error true
                else Job found
                    Jobs-->>Routes: Progress, warning, or error state
                    Routes-->>UI: JSON 200 progress payload
                end
            end
        end

        alt Payload carries an error
            UI->>UI: Stop polling and show the error
            Note over UI,Routes: heatmap_data is never requested
        else Progress reaches 100%
            UI->>Routes: GET /heatmap_data?job_id=...
            Routes->>Jobs: context(job_id)
            alt Job unknown or expired
                Routes-->>UI: JSON 404 with error true
            else Job errored
                Routes-->>UI: JSON 200 with error, error_code, and retryable
            else Results stored
                Routes-->>UI: JSON 200, ready true + results
                UI->>UI: Render responsive SVG and the published KPIs
                Note over UI: On desktop widths, when weekly_artists is valid, the streamgraph is drawn under the grid
            else Results not stored yet
                Routes-->>UI: JSON 202, ready false
                UI->>UI: Restart polling
                Note over UI,Routes: Narrow race -- progress reaches 100% before the results are stored
            end
        end
    end
```

The pipeline stores `partial_data_warning` in job stats and continues through
aggregation. `/heatmap_data` therefore returns `ready: true` when partial data
still yields results.

The client requests `/heatmap_data` only after progress reaches 100%, so the
202 response covers a narrow race and not ordinary processing. Both
`/progress` and `/heatmap_data` also return HTTP 400 for a missing `job_id`;
the client always sends one, so those responses are not drawn.

`heatmap.py` self-arrows cover in-process work and the `cleanup_expired_cache()`
helper it imports from `utils.py`, which is not drawn as a participant.
A total Last.fm failure is an exception, not a status: `lastfm.fetch_scrobbles`
raises a typed provider failure, and the one backstop -- the
`opt Unhandled exception anywhere above` block -- classifies it by type with
`errors.classify_exception_to_error_code`, the classifier the album pipeline
also uses, and publishes that code (`lastfm_unavailable` for an outage). A
fault the classifier does not recognize is ours, so it publishes
`internal_error` instead (F-SWE-5).
