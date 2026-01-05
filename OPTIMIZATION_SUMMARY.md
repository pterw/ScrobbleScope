# ScrobbleScope Performance Optimization Summary

## Changes Implemented - January 4, 2026

All optimizations have been applied to `app.py` based on official API documentation research.

---

## ✅ Completed Optimizations

### 1. **Corrected API Rate Limiters** (CRITICAL FIX)

**Previous Issue**: Rate limiters were set to 20 req/s for both APIs, which exceeded Last.fm's limit.

**Changes**:
- **Last.fm**: 20 req/s → **4 req/s** (Official limit: 5 req/s per IP)
  - Source: [Last.fm API Terms of Service](https://www.last.fm/api/tos)
  - Using 4 req/s for safety margin to avoid rate limit errors
  - Location: Lines 58-61

- **Spotify**: 20 req/s → **10 req/s** (Conservative, limit undisclosed)
  - Source: [Spotify Rate Limits](https://developer.spotify.com/documentation/web-api/concepts/rate-limits)
  - Spotify uses 30-second rolling window
  - Can be increased to 15-20 if no 429 errors occur
  - Location: Lines 73-75

---

### 2. **Added Connection Pooling** (Performance + Stability)

**New Function**: `create_optimized_session()` (Lines 183-216)

**Benefits**:
- Prevents socket exhaustion
- Enables connection reuse (keepalive)
- DNS caching (5 minutes)
- Proper timeout handling (30s total, 10s connect, 20s read)
- Connection limits: 40 total, 25 per host

**Applied to**:
- `check_user_exists()` - Line 549
- `fetch_all_recent_tracks_async()` - Line 667
- `fetch_spotify_access_token()` - Line 743
- `process_albums()` - Line 972

---

### 3. **Added Cache Cleanup** (Memory Leak Prevention)

**New Function**: `cleanup_expired_cache()` (Lines 245-268)

**Why Critical**:
- Production deployment on Fly.io has memory limits
- Previous implementation had unbounded cache growth
- Now cleans expired entries (1-hour TTL) on each request

**Called**: At start of `background_task()` - Line 399

**Monitoring**: Logs cache size in MB and entry count

---

### 4. **Last.fm Semaphore Control** (Thundering Herd Prevention)

**Updated Function**: `fetch_pages_batch_async()` (Lines 632-662)

**Changes**:
- Added semaphore limiting to **6 concurrent requests**
- Math: 4 req/s ÷ 6 concurrent = 0.67 req/s per slot
- Prevents burst of 40 simultaneous requests
- Enhanced logging with emoji indicators

**Global Constant**: `MAX_CONCURRENT_LASTFM = 6` (Line 50)

---

### 5. **Spotify Search Parallelization** ⭐ (BIGGEST SPEEDUP)

**Updated Function**: `process_albums()` (Lines 895-1105)

**Major Change**: Sequential → Parallel execution

**Before**:
```python
for key, data in filtered_albums.items():
    spotify_id = await search_for_spotify_album_id(...)  # One at a time
```

**After**:
```python
semaphore = asyncio.Semaphore(15)
search_tasks = [search_with_semaphore(key, data) for ...]
search_results = await asyncio.gather(*search_tasks)  # All at once!
```

**Configuration**:
- **15 concurrent searches** (controlled by semaphore)
- **10 req/s rate limiter** (controlled by AsyncLimiter)
- Dual protection prevents both thundering herd AND rate limits

**Global Constant**: `SPOTIFY_SEARCH_CONCURRENCY = 15` (Line 51)

**Expected Speedup**:
- 100 albums: ~100s → ~15s (**7x faster**)
- 300 albums: ~300s → ~45s (**7x faster**)
- 500 albums: ~500s → ~75s (**7x faster**)

---

### 6. **Enhanced Logging** (Monitoring & Debugging)

**Added Logging Features**:
- ✅ Emoji indicators for easy visual scanning
- ✅ Performance timers (search duration, batch duration)
- ✅ Success/failure counts
- ✅ Rate limiter initialization messages
- ✅ Cache cleanup statistics
- ✅ Enhanced 429 error messages with tuning suggestions

**Key Log Messages to Watch**:
```
🎵 Last.fm rate limiter initialized: 4 requests/second
🎧 Spotify rate limiter initialized: 10 requests/second
🧹 Cleaned up X expired cache entries
📥 Starting controlled batch fetch for pages X to Y (max 6 concurrent)
🔍 Starting PARALLEL search for X Spotify albums (max 15 concurrent, 10 req/s limit)
✅ Spotify search completed in Xs: X/X albums found on Spotify
📦 Fetching album details for X albums in X batches
⚠️ LAST.FM RATE LIMIT (429) - Consider reducing concurrency
⚠️ SPOTIFY RATE LIMIT (429) - Consider reducing SPOTIFY_SEARCH_CONCURRENCY
```

---

## 📊 Expected Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **100 albums** | ~110s | ~25-30s | **4-5x faster** |
| **300 albums** | ~330s | ~70-80s | **4-5x faster** |
| **500 albums** | ~550s | ~110-130s | **4-5x faster** |
| **Last.fm pages** | Same | Slightly slower | Compliant with limits |
| **Spotify search** | Sequential | Parallel | **7x faster** |
| **429 error rate** | Occasional | Rare | **Significantly reduced** |
| **Memory growth** | Unbounded | Bounded | **Leak prevented** |

---

## 🧪 Testing Instructions

### 1. **Monitor PowerShell Output**

The app logs to both terminal (PowerShell) and `logs/app_debug.log`. Watch for:

```powershell
# Start the app
python app.py
```

**What to look for in terminal**:
- Rate limiter initialization messages (should show 4 req/s and 10 req/s)
- Parallel search messages (should show "PARALLEL search")
- Timing information (search duration, batch duration)
- Any ⚠️ warnings about rate limits

### 2. **Monitor Log File**

```powershell
# In a separate terminal, tail the log file
Get-Content "logs\app_debug.log" -Wait -Tail 50
```

Or use VS Code to open `logs/app_debug.log` and watch it update in real-time.

### 3. **Test with Different Album Counts**

**Test Case 1: Small library (~50-100 albums)**
- Username: Pick a user with moderate listening in a year
- Expected time: 20-30 seconds

**Test Case 2: Medium library (~200-300 albums)**
- Username: Pick an active user
- Expected time: 60-90 seconds

**Test Case 3: Large library (~500+ albums)**
- Username: Power user
- Expected time: 2-3 minutes

### 4. **Watch for 429 Errors**

If you see:
```
⚠️ LAST.FM RATE LIMIT (429)
```
**Action**: Reduce `MAX_CONCURRENT_LASTFM` from 6 to 4

If you see:
```
⚠️ SPOTIFY RATE LIMIT (429)
```
**Action**: Reduce `SPOTIFY_SEARCH_CONCURRENCY` from 15 to 10

### 5. **Verify Cache Cleanup**

On each new search, you should see:
```
🧹 Cleaned up X expired cache entries
📊 Cache status: X entries (~X.XX MB)
```

---

## 🎛️ Tuning Parameters

All tunable parameters are now at the top of `app.py` (Lines 47-51):

```python
# API Concurrency Configuration
MAX_CONCURRENT_LASTFM = 6       # Last.fm concurrent page fetches
SPOTIFY_SEARCH_CONCURRENCY = 15  # Spotify concurrent album searches
```

### Tuning Guide:

**If experiencing Last.fm 429s**:
```python
MAX_CONCURRENT_LASTFM = 4  # More conservative
```

**If experiencing Spotify 429s**:
```python
SPOTIFY_SEARCH_CONCURRENCY = 10  # More conservative
```

**If NO 429s and want more speed**:
```python
SPOTIFY_SEARCH_CONCURRENCY = 20  # More aggressive
# Don't increase Last.fm - already at limit
```

---

## 🔍 Debugging Tips

### Enable DEBUG mode:

In your `.env` file:
```env
DEBUG_MODE=1
```

This will show more detailed logs including:
- Individual page requests
- Batch details for each group
- Cache hit/miss information
- Connection pool statistics

### Check logs for patterns:

```powershell
# Search for all rate limit warnings
Select-String -Path "logs\app_debug.log" -Pattern "RATE LIMIT"

# Search for timing information
Select-String -Path "logs\app_debug.log" -Pattern "completed in"

# Search for errors
Select-String -Path "logs\app_debug.log" -Pattern "ERROR"
```

---

## 📝 Summary of Files Changed

- ✅ `app.py` - All optimizations implemented
- ✅ `OPTIMIZATION_SUMMARY.md` - This document (NEW)

No other files were modified. All changes are backward compatible with existing UI and frontend code.

---

## ⚠️ Important Notes

1. **Last.fm Rate Limiter Change**: The old 20 req/s was **4x over the limit**. This was likely causing your previous 429 errors and thundering herd issues.

2. **Spotify Batch Size**: Your original `BATCH_SIZE = 20` was already correct. Spotify's limit is 20 IDs per request, not 50 as I initially stated.

3. **Production Deployment**: The cache cleanup is critical for Fly.io deployment to prevent OOM crashes.

4. **Backward Compatibility**: All changes are internal optimizations. The UI, templates, and user experience remain unchanged.

---

## 🚀 Next Steps

1. **Test locally** with your Last.fm account
2. **Monitor logs** for any 429 errors
3. **Measure performance** improvement
4. **Tune parameters** if needed (see Tuning Guide above)
5. **Deploy to Fly.io** once stable

---

**Generated**: January 4, 2026
**Based on Official API Documentation**:
- [Last.fm API ToS](https://www.last.fm/api/tos)
- [Spotify Rate Limits](https://developer.spotify.com/documentation/web-api/concepts/rate-limits)
- [Spotify Get Multiple Albums](https://developer.spotify.com/documentation/web-api/reference/get-multiple-albums)
