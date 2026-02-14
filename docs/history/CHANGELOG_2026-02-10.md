# ScrobbleScope Changes - February 10, 2026

## Summary

Performance optimizations to Last.fm page fetching, UX overhaul of the index and loading pages, and mobile scroll support for results.

---

## Performance Optimizations

### 1. Removed Sequential Batch Fetching for Last.fm Pages

**Problem**: Last.fm pages were fetched in sequential batches of 50. Each batch had to fully complete (via `asyncio.gather`) before the next batch started, creating idle gaps when slow pages needed retries.

**Fix**: All remaining pages are now launched in a single `asyncio.gather` call. The semaphore (`MAX_CONCURRENT_LASTFM`) and rate limiter (`_LASTFM_LIMITER`) still control throughput — no change in API load.

**Files Modified**: `app.py` (lines 705-713)

### 2. Increased Last.fm Concurrency Semaphore (5 → 10)

**Problem**: With a semaphore of 5 and a rate limiter of 10 req/s, the semaphore was the bottleneck when individual requests were slow (>500ms). The pipeline couldn't sustain 10 req/s.

**Fix**: `MAX_CONCURRENT_LASTFM` increased from 5 to 10, matching the rate limiter. The rate limiter is now always the binding constraint, keeping the pipeline fully saturated.

**Files Modified**: `app.py` (line 45)

### 3. Fixed Stale Log Message

**Fix**: The 429 warning message for Last.fm referenced "4 req/s" from an old config. Updated to "10 req/s".

**Files Modified**: `app.py` (line 635)

---

## UX Improvements

### 4. Clickable Spotify Album Links in Results

**Feature**: Album names in the results table now link directly to their Spotify page (`https://open.spotify.com/album/{id}`). Links open in a new tab.

**Files Modified**: `templates/results.html`

### 5. Welcome Modal (First-Visit Onboarding)

**Feature**: The inline info block on the index page has been replaced with a Bootstrap modal that:
- Auto-opens on first visit (tracked via `localStorage.seenWelcome`)
- Dismissed with "Get Started" button, X, or backdrop click
- Re-openable via an "Info" button below the logo on return visits

**Files Modified**: `templates/index.html`, `static/js/index.js`, `static/css/index.css`

### 6. Contextual Tooltip Icons on Form Fields

**Feature**: Small `?` icons next to form labels (Listening Year, Release Date Filter, Sort By, Album Thresholds) that show explanatory popovers on hover (desktop) or tap (mobile). Uses Bootstrap 5 popovers.

**Tooltip content**:
- **Listening Year**: "The year to scan your scrobbles from..."
- **Release Date Filter**: "Filter albums by when they were released. Default shows albums released the same year you listened to them — ideal for building your Album of the Year list."
- **Sort By**: "Play Count ranks by total track plays. Listening Time uses Spotify track durations multiplied by your play counts — a feature unique to ScrobbleScope."
- **Album Thresholds**: "Control what counts as an album..."

**Files Modified**: `templates/index.html`, `static/js/index.js`, `static/css/index.css`

### 7. Listening Year: Dropdown → Number Input

**Problem**: A `<select>` dropdown with 20+ years (2005–2026) was clunky, especially on mobile where scrolling a long list is tedious.

**Fix**: Replaced with `<input type="number" min="2002" max="current_year">`. Users type the year directly (4 keystrokes). Mobile devices show a numeric keypad. Validation on submit catches invalid years.

**Files Modified**: `templates/index.html`

### 8. Personalized Loading Stats

**Feature**: The loading page now shows real-time personalized data as the backend processes:
- "Scanned 20,177 scrobbles in 2025"
- "199 albums passed your thresholds (out of 1,370 unique albums)"
- "Matched 197 albums on Spotify"

Stats are piped through the existing `/progress` JSON endpoint via a new `stats` field and displayed with fade-in animations.

**Files Modified**: `app.py` (progress stats pipeline), `templates/loading.html`, `static/js/loading.js`, `static/css/loading.css`

### 9. Removed Inline Form Help Text

**Change**: `form-text` helper paragraphs under each form field were removed. Their content is now in the tooltip popovers, keeping the form compact.

**Files Modified**: `templates/index.html`

---

## Mobile Improvements

### 10. Results Table Horizontal Scroll

**Problem**: `.table-responsive` had `overflow: hidden`, preventing horizontal scrolling on mobile. The results table was clipped on narrow screens.

**Fix**: Changed to `overflow-x: auto` with `-webkit-overflow-scrolling: touch` for smooth mobile scrolling.

**Files Modified**: `static/css/results.css`

---

## Dark Mode Additions

- Welcome modal content styled for dark mode (background, borders, close button)
- Tooltip icons adapt color on hover in dark mode
- Live stats on loading page use theme-aware colors

**Files Modified**: `static/css/index.css`

---

## Files Summary

### Modified (8 files)
1. **app.py** — Parallel fetch optimization, concurrency increase, personalized stats pipeline
2. **templates/index.html** — Welcome modal, tooltip icons, year number input, removed info block
3. **templates/loading.html** — Live stats container
4. **static/js/index.js** — Modal first-visit logic, popover initialization
5. **static/js/loading.js** — `updateLiveStats()` function for personalized loading data
6. **static/css/index.css** — Tooltip icon, modal dark mode, info button styling
7. **static/css/loading.css** — Live stats styling with fade-in animation
8. **static/css/results.css** — Mobile horizontal scroll fix

### New (1 file)
1. **CHANGELOG_2026-02-10.md** — This file

### Updated (1 file)
1. **README.md** — Updated rate limit docs, added new features to highlights, updated checklist

---

**Date**: February 10, 2026
**Branch**: `wip/pc-snapshot`
