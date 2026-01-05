# ScrobbleScope Refactor & Development Plan

## ✅ Phase 1: Pre-Refactoring Optimization (COMPLETED - 2026-01-04)

**Status:** ✅ **COMPLETED**

- ✅ **(CRITICAL) Implement Concurrent API Calls in process_albums**
    - **Goal**: Drastically reduce the ~30-minute processing time for large libraries by running Spotify API calls in parallel.
    - **Completed**: 2026-01-04
    - **Implementation Details**:
        - ✅ Fixed rate limiters based on official API documentation
            - Last.fm: Reduced from 20 req/s to 4 req/s (official limit: 5 req/s)
            - Spotify: Reduced from 20 req/s to 10 req/s (tested and tuned to avoid 429s)
        - ✅ Implemented parallel Spotify album search with semaphore control (10 concurrent)
        - ✅ Added Last.fm batch semaphore control (6 concurrent)
        - ✅ Implemented optimized connection pooling with DNS caching
        - ✅ Added cache cleanup to prevent memory leaks
        - **Performance Improvement**: 4-5x faster for typical use cases
        - **Files Modified**: `app.py` (lines 47-1010), [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md:1-359)

---

## Phase 2: Core Backend Refactoring (The Big Rewrite)

**Status:** 🔜 **PENDING** (Recommend after Phase 3 UX improvements)

### TO-DO during rewrite

- Docstrings/Comments: Write these as functions move into their new files during the refactor. It's more efficient than writing them now and then moving them.

### Architectural overall planned. Proposed module structure included.

- **(CRITICAL) Establish Application Factory & Configuration**
    - **Goal**: Create a scalable Flask application structure
    - **Action**: Create `app/` directory, `app/__init__.py` with `create_app()`, and `config.py` for settings.

- **(CRITICAL) Modularize with Blueprints and Services**
    - **Goal**: Separate concerns to make the code maintainable.
    - **Actions**:
        - Move routes into Flask Blueprints (`app/routes/`).
        - Move API-calling logic into `app/services/spotify_client.py` and `app/services/lastfm_client.py`.
        - Move helper functions (`normalize_name`, `format_seconds`) into `app/utils.py`.
        - Move `background_task` into `app/tasks.py`.

- (*HIGH*) Implement Persistent Cache
    - Goal: Make caching survive application restarts.
    - Action: Create `app/cache.py` using `Flask-Caching` and replace the global `REQUEST_CACHE` dictionary.

---

## ✅ Phase 3: High-Value UX & Frontend Improvements (IN PROGRESS)

**Status:** 🏗️ **IN PROGRESS** (Several features completed 2026-01-04)

### Completed Features ✅

- ✅ **Informative UI Blurb on Homepage** (2026-01-04)
    - Added comprehensive welcome message explaining all features
    - Lists all sorting/filtering/export options
    - Explains default behavior clearly
    - **Files Modified**: `templates/index.html` (lines 55-67)

- ✅ **"All Years" Release Filter** (2026-01-04)
    - Users can now view all albums regardless of release year
    - Backend logic implemented to handle `release_scope="all"`
    - Filter description updated
    - **Files Modified**: `app.py` (lines 929-931, 1249), `templates/index.html` (line 96)

- ✅ **Top N Results Limit** (2026-01-04)
    - Users can limit results to Top 10/25/50/100 albums
    - Dropdown selector on homepage
    - Backend applies limit before displaying results
    - **Files Modified**: `app.py` (lines 497-505), `templates/index.html` (lines 124-135)

- ✅ **Improved Album Thresholds UI** (2026-01-04)
    - Clearer labeling with better explanations
    - Added descriptive helper text
    - Marked defaults explicitly
    - **Files Modified**: `templates/index.html` (lines 137-171)

- ✅ **Improve the landing page (`index.html`) copy to be more descriptive for new users** (2026-01-04)
    - Comprehensive feature overview added
    - Clear default behavior explanation
    - **Files Modified**: `templates/index.html` (lines 55-67)

### Pending Features

- **(CRITICAL) Username & Year Validation on Homepage**
    - **Goal**: Prevent users from starting invalid searches, acts as error prevention.
    - **Action**: Create a small new API endpoint that checks if a username is valid and returns their registration year. Use `JavaScript` on `index.html` to call this onblur from the username field and dynamically populate the year dropdown.

- (*HIGH*) Master HTML Template
    - Goal: Reduce code duplication on the frontend.
    - Action: Create `base.html` and have all other templates `{% extends %}` it.

- (*HIGH*) Link to Spotify from Results
    - Goal: Add a simple, high-value UX feature.
    - Action: In `results.html`, wrap the album title in an `<a>` tag pointing to `https://open.spotify.com/album/{album.id}`.

- (MEDIUM) Finalize Static File Separation
    - Goal: Complete the separation of `HTML`, `CSS`, and `JS`.
    - Action: Move any remaining inline `<style>` and `<script>` blocks to external files.

---

## Phase 4: Advanced Features & Future Polish

**Status:** 🔮 **FUTURE**

These can be implemented incrementally once the core application is rebuilt and stable.

### Bug Fixes

- (MEDIUM) **Fix "King of Limbs" Bug**: Implement the string similarity check using thefuzz in your Spotify service module.
    - **Issue**: "The King of Limbs Live at the Basement" (not on Spotify) was matched to "The King of Limbs" studio album, resulting in incorrect release year (1997 instead of 2018)
    - **Root Cause**: Fallback matching logic may be too aggressive
    - **Solution**: Implement fuzzy string matching with thefuzz library to validate matches

- (MEDIUM) **CSV Encoding Fix**: Implement the `encoding='utf-8-sig'` fix.
    - **Issue**: Exporting to CSV with albums containing special characters or non-latin script creates issues in Excel
    - **Solution**: Use UTF-8 with BOM for Excel compatibility

### Features

- ~~(low) "All Years" Filter~~: ✅ **COMPLETED** 2026-01-04
    - ~~Add the option to select all years for album sorting and associated logic.~~

- (LOW) **Track-Level Details (Modal/Tooltip)**: A great feature for "v2.0".
    - Requires modifying the data structures again to pass track-specific data to the template.
    - Options:
        1. Mouseover tooltip showing most played track from album
        2. Link to Spotify album page (simplest)
        3. Clickable row showing modal with all listened tracks from that album

- (LOW) **Stop/Restart Button on Loading Page**: An advanced feature requiring client-side JS and a backend endpoint for task management.
    - Allow users to return to homepage with one button if backend is taking too long
    - (Optional) Restart button to re-execute exact filter without re-entering params

---

## Additional Elements, Checks, and QA

### Completed ✅

1. ✅ **Optimize metadata fetching and Scrobble fetching** (2026-01-04)
    - Implemented parallel requests with semaphore control
    - Rate limiters properly tuned to official API limits
    - Connection pooling implemented
    - Performance increased 4-5x

2. ✅ **Debug log output logic** (2026-01-04)
    - Logging properly configured with rotation
    - Both terminal and file output working
    - Enhanced logging with emojis and performance timers
    - **Configuration**: `app.py` lines 111-146

### Pending

1. **CSV UTF-8 BOM patch** (See Phase 4 bug fixes above)

2. **Log rotation for app_debug.log**
    - Implement rotation to `oldlogs/` directory
    - Already has `RotatingFileHandler` with 1MB max size, 5 backups
    - Consider adding date-based rotation

3. **Comprehensive backend function docstrings**
    - Many functions now have docstrings after optimization work
    - Need to complete for remaining functions before Phase 2 refactor

4. **Improve responsive design for mobile devices**
    - Current design uses Bootstrap 5, but needs testing on mobile
    - Consider mobile-specific CSS tweaks

---

## Conceptualized Module Structure for Phase 2

(Please review this and check logic and feasibility, or if other modules and blueprints are best. I want the optimal route that allows for modularity, upkeep, and updates with new features.)

### Proposed File Structure:

```
ScrobbleScope/
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── config.py            # Configuration classes
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Homepage, loading, results routes
│   │   ├── api.py           # API endpoints (progress, unmatched JSON)
│   │   └── export.py        # CSV/image export routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lastfm_client.py # Last.fm API calls
│   │   ├── spotify_client.py# Spotify API calls
│   │   └── cache.py         # Caching logic
│   ├── tasks.py             # Background processing
│   ├── utils.py             # Helper functions (normalize_name, format_seconds)
│   ├── models.py            # (Optional) Data models if using database
│   ├── static/              # (Move from root)
│   └── templates/           # (Move from root)
├── tests/
├── logs/
├── run.py                   # Application entry point
├── requirements.txt
└── .env
```

### Module Responsibilities:

| File | Responsibility |
| ------------ | ------------------------------------ |
| `lastfm_client.py` | Last.fm API calls and utilities |
| `spotify_client.py` | Spotify metadata lookups and parsing |
| `cache.py` | Caching logic and memoization |
| `utils.py` | General-purpose helpers |
| `tasks.py` | Background/long-running processing |
| `config.py` | Centralized app configuration |
| `routes/` | Flask Blueprints for page routing |

---

## Ideas for better UX and feature rich app

### Advanced Features (Post-Phase 2)

- **Mouseover tooltips with track/genre info**
    - Show most played track from each album on hover
    - Requires passing track-level data to frontend
    - Would help validate "sort by play time" is working correctly

- **Clickable album rows with modal**
    - Display all tracks listened to from that album
    - Show play count/play time per track
    - Example: "Tracks from In Rainbows you listened to"

- **Link to Spotify** (Simplest option - recommend implementing first)
    - Wrap album title with `<a>` tag to `https://open.spotify.com/album/{id}`
    - High UX value, minimal complexity

### Frontend Improvements

- **Check if username exists before leaving homepage** (See Phase 3 pending)
    - Validate username on blur
    - Dynamically populate year dropdown based on account registration date
    - Prevents invalid searches

- ✅ **Finalize moving all inline CSS/JS to external files** (Partially done)
    - `loading.html` and `index.html` mostly externalized
    - Check remaining templates

- **Create master HTML template** (See Phase 3 pending)
    - `base.html` with common structure
    - All templates extend it

- **Typography improvements** (Optional)
    - Consider Helvetica Neue for body & headings
    - Monospace (IBM Plex Mono? JetBrains Mono?) for data/numbers

- **Handle ALL error cases gracefully**
    - No tracebacks shown in `error.html`
    - User-friendly error messages for all failure modes

---

## Progress Summary

### Completed (2026-01-04)
- ✅ Phase 1: All performance optimizations
- ✅ Spotify concurrency tuning (reduced 15→10 to fix 429s)
- ✅ "All Years" release filter
- ✅ Top N results limit (10/25/50/100)
- ✅ Improved UI descriptions and help text
- ✅ Enhanced logging and monitoring

### In Progress
- 🏗️ Phase 3: UX improvements (several features completed, more pending)

### Next Steps
1. Implement username validation on homepage
2. Add Spotify album links in results
3. Create base HTML template
4. Complete Phase 3 UX improvements
5. Begin Phase 2 refactoring (after UX work stabilizes)

---

**Last Updated**: January 4, 2026
**Current Version**: Monolithic app.py with performance optimizations
**Next Major Milestone**: Complete Phase 3 UX improvements before Phase 2 refactor
