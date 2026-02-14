# Performance Timing Documentation

## Overview
This document describes the elapsed time tracking added to ScrobbleScope to help monitor and optimize performance.

## Timing Points Added (2026-01-10)

All timing entries use the format: `⏱️  Time elapsed ([operation]): X.Xs`

### High-Level Steps (background_task)

1. **User Verification** - `app.py:431`
   - Verifies Last.fm username exists
   - Typical time: <1s

2. **Last.fm Data Fetch** - `app.py:453`
   - Fetches all scrobbles from Last.fm for the specified year
   - Includes detailed sub-timing (see below)
   - Typical time: 5-30s depending on number of scrobbles

3. **Spotify Album Processing** - `app.py:490`
   - Full Spotify search and metadata fetch
   - Includes two sub-steps (see below)
   - Typical time: 10-60s depending on number of albums

4. **Total Time Elapsed** - `app.py:527`
   - Complete end-to-end processing time
   - Typical time: 20-120s

### Detailed Sub-Steps

#### Last.fm Fetching (fetch_all_recent_tracks_async)
- **Last.fm Pages Fetch** - `app.py:720`
  - Shows total pages fetched
  - Format: `⏱️  Time elapsed (fetching N Last.fm pages): X.Xs`

#### Spotify Processing (process_albums)
- **Spotify Album Search** - `app.py:1024`
  - Parallel search for Spotify album IDs
  - Uses 10 concurrent requests with 10 req/s rate limit
  - Typical time: 5-20s for 100 albums

- **Spotify Batch Fetch** - `app.py:1061`
  - Fetches full album metadata in batches of 20
  - Parallel batching with 5 concurrent batches
  - Typical time: 2-10s for 100 albums

## Example Log Output

```
2026-01-10 10:00:01,234 [Thread-7] [INFO] ⏱️  Time elapsed (user verification): 0.3s
2026-01-10 10:00:25,456 [Thread-7] [INFO] ⏱️  Time elapsed (fetching 142 Last.fm pages): 24.2s
2026-01-10 10:00:25,789 [Thread-7] [INFO] ⏱️  Time elapsed (Last.fm data fetch): 24.5s
2026-01-10 10:00:38,123 [Thread-7] [INFO] ⏱️  Time elapsed (Spotify album search): 12.3s
2026-01-10 10:00:40,456 [Thread-7] [INFO] ⏱️  Time elapsed (Spotify batch fetch): 2.3s
2026-01-10 10:00:40,789 [Thread-7] [INFO] ⏱️  Time elapsed (Spotify album processing): 15.0s
2026-01-10 10:00:42,012 [Thread-7] [INFO] ⏱️  Total time elapsed: 41.0s
```

## Performance Benchmarks

### Expected Performance (2025 listening year, typical user)

| Albums Found | Last.fm Fetch | Spotify Search | Spotify Fetch | Total |
|--------------|---------------|----------------|---------------|-------|
| 50 albums    | 10-15s        | 5-8s           | 1-3s          | 20-30s |
| 100 albums   | 15-25s        | 10-15s         | 2-5s          | 35-50s |
| 200 albums   | 20-35s        | 18-25s         | 3-8s          | 50-75s |
| 500+ albums  | 30-60s        | 40-60s         | 5-12s         | 90-150s |

### Optimization Guidelines

**If Last.fm fetch is slow (>30s):**
- Consider increasing `MAX_CONCURRENT_LASTFM` (currently 10)
- Check Last.fm API rate limits aren't being hit
- Verify batch size is optimal (currently 50)

**If Spotify search is slow (>20s for 100 albums):**
- Consider increasing `SPOTIFY_SEARCH_CONCURRENCY` (currently 10)
  - ⚠️ Don't exceed 15 - causes 429 errors
- Verify rate limiter is set to 10 req/s (correct as of 2026-01-04)

**If Spotify batch fetch is slow (>5s for 100 albums):**
- Consider increasing `SPOTIFY_BATCH_CONCURRENCY` (currently 5)
- Verify batch size is 20 (Spotify API maximum)

## Monitoring Recommendations

1. **Watch for 429 errors** - Indicates rate limiting issues
   - Last.fm: Reduce below 5 req/s
   - Spotify: Reduce below 10 req/s or lower concurrency

2. **Compare step timings** - Identify bottlenecks
   - If one step is >70% of total time, optimize that step first

3. **Track cache hit rates** - Better caching reduces API calls
   - Check `REQUEST_CACHE` effectiveness

## Related Files

- `app.py` - Main application with timing implementation
- `logs/app_debug.log` - Contains all timing output
- `OPTIMIZATION_SUMMARY.md` - Details of rate limiter tuning
- `CHANGELOG_2026-01-04.md` - Performance optimization history

---

**Last Updated**: 2026-01-10
**Performance Version**: v1.2 (with detailed timing)
