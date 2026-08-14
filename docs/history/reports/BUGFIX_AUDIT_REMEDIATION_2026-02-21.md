# Gemini Audit Remediation (2026-02-21)

Date: 2026-02-21
Triggered by: Third-party audit review (Gemini Pro analysis of orchestrator.py,
              cache.py, domain.py, routes.py)
Implemented by: Claude Sonnet 4.6

---

## 1. Summary

A Gemini Pro static analysis review identified four issues in the orchestrator and
support modules. Three were confirmed against the live codebase and fixed. One was
assessed and deferred as near-false-alarm. An additional separation-of-concerns
violation not in the original report was also identified and fixed during the
investigation.

---

## 2. Issues found, confirmed, and fixed

### Issue 1 (Medium): Late slicing -- Spotify API waste on playcount sort

**File:** `scrobblescope/orchestrator.py:_fetch_and_process`

**Root cause:**
`limit_results` was applied post-Spotify at the very end of `_fetch_and_process`.
For a user requesting "Top 10" with a library of 500 albums, `process_albums` was
called with all 500 albums, triggering Spotify searches and batch detail fetches for
all cache misses across the full set.

For `sort_mode="playcount"`, the final ranking is fully determined by Last.fm
`play_count` data -- available before any Spotify call. Pre-slicing to the requested
limit is therefore safe and eliminates all unnecessary Spotify calls for albums outside
the requested top N.

For `sort_mode="playtime"`, ranking depends on Spotify track durations, which are
unavailable until after the Spotify fetch. Pre-slicing is not possible in this case
and was not attempted.

**Note on DB cache interaction:** DB cache hits do not incur Spotify API calls, so the
practical impact of late slicing is proportional to the cache miss rate. On a warm
cache the waste is near-zero. On a cold cache with a large library and a small
`limit_results`, this could have triggered hundreds of unnecessary Spotify searches.

**Fix:**
In `_fetch_and_process`, after `filtered_albums` is validated as non-empty and before
`process_albums` is called, add a conditional sort-and-slice:

```python
if sort_mode == "playcount" and limit_results != "all":
    try:
        limit = int(limit_results)
        if len(filtered_albums) > limit:
            sorted_items = sorted(
                filtered_albums.items(),
                key=lambda kv: kv[1]["play_count"],
                reverse=True,
            )
            filtered_albums = dict(sorted_items[:limit])
    except ValueError:
        pass  # malformed limit_results handled by the post-process slice
```

The existing post-process slice remains as a safety net for `playtime` sort and for
malformed `limit_results` values.

---

### Issue 2 (Low-Medium): Indefinite DB growth -- no stale row cleanup

**File:** `scrobblescope/cache.py`

**Root cause:**
`_batch_lookup_metadata` filtered by TTL at read time (`AND updated_at > NOW() -
make_interval(days => $3)`), so stale rows were never returned to callers. However,
no DELETE statement existed anywhere in the codebase. Rows that fell outside the TTL
window were silently excluded from reads but accumulated in the `spotify_cache` table
indefinitely.

Active albums (re-queried within the TTL window) refresh their `updated_at` timestamp
via the ON CONFLICT DO UPDATE upsert in `_batch_persist_metadata`. Only truly inactive
rows -- albums that no user has queried within the TTL -- accumulate stale.

**Severity:** Bounded in practice by the universe of Spotify albums and the active user
base. The Fly Postgres free tier has generous disk limits, but the correctness gap was
real -- the "30-day TTL" was enforced only at read time, not at write/storage time.

**Fix:**
Added `_cleanup_stale_metadata(conn)` to `cache.py`:

```python
async def _cleanup_stale_metadata(conn):
    try:
        result = await conn.execute(
            """
            DELETE FROM spotify_cache
            WHERE updated_at < NOW() - make_interval(days => $1)
            """,
            METADATA_CACHE_TTL_DAYS,
        )
        logging.info("Stale cache cleanup: %s", result)
    except Exception as exc:
        logging.warning("Stale cache cleanup failed (non-fatal): %s", exc)
```

Called opportunistically from `process_albums` in `orchestrator.py` after Phase 1
batch lookup, inside the `if conn:` block, before the connection is closed. Non-fatal:
the function catches and logs all exceptions internally so cleanup failures never
surface to the job.

---

### Issue 3 (Low): Separation of concerns -- ERROR_CODES and SpotifyUnavailableError
in domain.py

**File:** `scrobblescope/domain.py`

**Root cause:**
`domain.py` is the module for core business logic (Unicode normalization, key
extraction). It contained two items that do not belong there:

1. `ERROR_CODES` -- a dict of user-facing message strings and infrastructure flags
   (`"retryable": True/False`). Domain logic should not own UI copy or network-failure
   retryability semantics.
2. `SpotifyUnavailableError` -- a runtime exception class that belongs with the error
   classification it supports.

The practical impact was zero -- no functional bugs -- but the placement created a
dependency on UI concerns from a module that should be import-free of presentation
layer knowledge.

**Fix:**
Created `scrobblescope/errors.py` as a new leaf module (imports nothing from the
package). Moved both `ERROR_CODES` and `SpotifyUnavailableError` there verbatim.
Updated import sites:

- `scrobblescope/orchestrator.py`: `from scrobblescope.errors import SpotifyUnavailableError`
- `scrobblescope/repositories.py`: `from scrobblescope.errors import ERROR_CODES`
- `tests/services/test_orchestrator_service.py`: import updated to match

`domain.py` now contains only normalization functions and `_extract_registered_year`.

---

### Issue 4 (Low): Separation of concerns -- duplicate filter-text translation in routes.py

**File:** `scrobblescope/routes.py:unmatched_view`

**Root cause (found during investigation, not in original report):**
`unmatched_view` contained a 10-line inline block translating `release_scope` into a
human-readable `filter_desc` string. This is identical in purpose to the
`get_filter_description()` function defined 60 lines earlier in the same file. Two
independent implementations of the same logic meant changes to filter options required
edits in two places, with risk of divergence.

**Fix:**
Replaced the inline block with a call to the existing `get_filter_description`:

```python
# Before
if release_scope == "same":
    filter_desc = f"same year as listening ({year})"
elif release_scope == "previous":
    filter_desc = f"previous year ({int(year) - 1})"
elif ...

# After
filter_desc = get_filter_description(release_scope, decade, release_year, int(year))
```

---

## 3. Issue assessed and deferred: Empty result hallucination

**Gemini claim:** If a user has a legitimately obscure library with no Spotify matches,
`_fetch_and_process` would classify the result as "Spotify Unavailable" (a system
error) instead of "No matches found" (a user condition).

**Assessment:** The heuristic in `_fetch_and_process` (lines 510-518) triggers only
when ALL of these are true simultaneously:
1. `results` is empty
2. `filtered_albums` is non-empty
3. `spotify_no_match == len(filtered_albums)` (every single album is "No Spotify match")
4. No DB cache hits (cache hits never enter the `unmatched` dict, so they prevent the
   count from equalling `len(filtered_albums)`)

Condition 4 is a strong guard: any user with prior search history has cached results,
meaning `spotify_no_match < len(filtered_albums)` and the error is never triggered.
For a new user whose entire library is absent from Spotify AND who has zero cache hits,
the heuristic misclassifies. This scenario is extremely unlikely in practice.

**Decision:** Deferred. Not worth the refactor risk without a concrete real-world case.
Document as a known false-positive edge case.

---

## 4. New tests added

| Test | File | Verifies |
|------|------|----------|
| `test_playcount_limit_slices_before_spotify` | test_orchestrator_service.py | process_albums called with <= limit entries for playcount sort |
| `test_playtime_limit_does_not_preslice` | test_orchestrator_service.py | process_albums receives all albums for playtime sort |
| `test_cleanup_stale_metadata_issues_delete` | test_orchestrator_service.py | DELETE statement issued with TTL parameter |
| `test_cleanup_stale_metadata_nonfatal` | test_orchestrator_service.py | Exception in conn.execute does not propagate |

---

## 5. Files changed

| File | Change |
|------|--------|
| `scrobblescope/orchestrator.py` | WP-1 pre-slice block; WP-2 cleanup call; WP-4 import update |
| `scrobblescope/cache.py` | WP-2 `_cleanup_stale_metadata` function added |
| `scrobblescope/routes.py` | WP-3 inline filter_desc replaced with get_filter_description call |
| `scrobblescope/errors.py` | WP-4 NEW FILE: ERROR_CODES + SpotifyUnavailableError |
| `scrobblescope/domain.py` | WP-4 ERROR_CODES + SpotifyUnavailableError removed |
| `scrobblescope/repositories.py` | WP-4 import updated to errors.py |
| `tests/services/test_orchestrator_service.py` | 4 new tests; import updated to errors.py |

---

## 6. Validation

- `pytest -q`: **114 passed** (110 pre-existing + 4 new).
- `pre-commit run --all-files`: all 8 hooks passed (black, isort, autoflake, flake8,
  trim trailing whitespace, fix end of files, check yaml, doc-state-sync-check).
- No schema changes, no API contract changes, no migration required.
- The `errors.py` module is a dependency graph leaf (imports nothing from the package),
  preserving the acyclic import structure.

---

## 7. Known limitation (documented)

`sort_mode="playtime"` with a finite `limit_results` still processes all albums through
Spotify before slicing. This is a genuine architectural constraint: playtime ranking
requires track durations from Spotify, which are only available after the full fetch.
A two-pass approach (fetch all, rank, discard extras) would add complexity without
eliminating the underlying Spotify calls. Documented with a comment in
`_fetch_and_process`.
