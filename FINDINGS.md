# ScrobbleScope Findings & Open Issues

Last updated: 2026-05-17
Status: Batch 19 active on `feat/heatmap`. Batch 18 heatmap iteration 1 is
complete and archived. 385 tests, 24 test files.
Batch 19 polish is in progress: perf documentation cleanup, result frame/KPIs,
pill rename, pinwheel clipping fix, and mobile heatmap layout.
Includes findings from load testing + cache verification session (2026-03-04)
and Batch 18 full source-code audit (2026-03-07).

---

## Severity Key

| Level | Meaning |
|-------|---------|
| **P0** | Fix before next deploy or next batch |
| **P1** | Next batch |
| **P2** | Scaling roadmap / future consideration |
| **Info** | Documented design choice, no action needed now |

---

## Resolved since last update (2026-03-02)

Items from prior audits that have been addressed:

- ~~MEMORY.md stale~~ -- Deleted. Replaced by `AGENT_NOTES.md` (tracked) in Batch 17 WP-4.
- ~~README.md screenshot placeholders~~ -- Owner replaced with "coming soon".
- ~~CI Python version drift~~ -- Aligned to 3.13 in Batch 15.
- ~~docsync cli.py unconditional rewrite~~ -- Gated on changed set (Batch 14).
- ~~Test-count regex defined 3 times~~ -- Consolidated to single `TEST_COUNT_RE`
  in `parser.py`; renderer and logic import it (Batch 14).
- ~~Dedup-sort pattern copy-pasted~~ -- Extracted `_dedup_sorted()` helper in
  `logic.py` (Batch 14).
- ~~Gunicorn HTTP serialization~~ -- Added `--threads 4` to Dockerfile CMD.
  Merged to `main` as `f8a579f` (#57). Deployed and verified.
- ~~Dark mode ignores browser preference~~ -- `theme.js` falls back to
  `matchMedia('prefers-color-scheme: dark')`. Commit `463282e`.
- ~~Log rotation loses data under load~~ -- Increased to 2MB cap, 10 backups.
  Commit `21a3b4c` on `main`.

---

## Batch 18 audit findings (2026-03-07)

Peripheral findings from the full source-code audit that do not directly
affect Batch 18 WPs but should be tracked for future batches. Corrections
that DO affect WPs are documented in BATCH18_DEFINITION.md audit section.

### F-B18-1: orchestrator.py monolith (920 lines)

Album search orchestration, Spotify batch processing, error mapping, progress
tracking, and result assembly in one file. Adding heatmap.py keeps SoC for
iteration 1 but a future batch should extract shared patterns (event loop
setup, progress mapping, error guards) into a common module. Explicitly
deferred.

### F-B18-2: JOBS dict has no type annotations

`repositories.py` JOBS stores heterogeneous result types (list for albums,
dict for heatmap). No TypedDict or dataclass definitions. Future batch
candidate.

### F-B18-3: loading.js hardcoded album messaging

`loading.js` (409 lines) has album-specific rotating messages and scrobble
count cycling. Irrelevant to heatmap (separate heatmap.js). If 3+ features
emerge, polling/progress patterns should be extracted into shared utility.

### F-B18-4: _check_user_exists creates throwaway event loops

`routes.py` wraps an async call via `run_async_in_thread()`. Creates a
throwaway event loop per call. Not a problem at current scale.

### F-B18-5: inline SVG payload growth

Main logo via `{% include 'inline/scrobble_scope_inline.svg' %}` plus new
pinwheel SVG increases initial HTML payload. Both small enough for iteration 1.
If more inline SVGs are added, consider lazy loading or sprite sheets.

### F-B18-6: dark mode uses body.dark-mode class, not data attributes

CSS uses `.dark-mode` class toggled by `theme.js`. Original Batch 18
definition referenced `[data-theme="dark"]` which does not exist. Corrected
in audited definition.

### F-B18-7: Windows SelectorEventLoop guard duplication

Both `orchestrator.py background_task()` and new `heatmap_task()` need
identical `sys.platform == "win32"` guard for `WindowsSelectorEventLoopPolicy`.
Shared utility candidate for future refactor.

### F-B18-8: get_job_context shallow-copies results but not nested dicts

`repositories.py` `get_job_context()` copies list results via `list(results)`
but does not copy dict results at all (returns the original reference).
The Boy Scout fix in WP-1 adds `elif isinstance(results, dict):
results = dict(results)` -- but this is still a shallow copy. The heatmap
result dict contains a nested `daily_counts` dict, which will be shared
by reference. In practice no caller mutates it, but it violates the
function's stated contract ("All mutable containers are shallow-copied
to prevent callers from mutating shared state"). Deep copy would be
correct but is overkill for iteration 1; note for future hardening.

### F-B18-9: username not sanitized for JS/SVG injection

Routes validate that a username exists on Last.fm but do no input
sanitization beyond that. Usernames are echoed back in JSON and rendered
by heatmap.js into SVG text elements and tooltip HTML. Flask's Jinja2
auto-escapes template output, but JS-side rendering into `innerHTML` or
SVG `textContent` must escape manually. `textContent` is safe;
`innerHTML` is not. heatmap.js must use `textContent` for any
user-supplied strings. Note for WP-4 code review.

### F-B18-10: heatmap + album jobs share global throttle

The `_GlobalThrottle` in `utils.py` serializes ALL API calls at 10 req/s
across all job threads. A concurrent album search + heatmap fetch will
compete for the same 10 req/s budget. This is correct behavior (prevents
upstream 429s) but means heatmap fetch slows if album searches are running,
and vice versa. No action needed -- documenting for load-test awareness.

### F-B18-11: heatmap Last.fm page fetch is rate-limit bound (P1)

Heatmap fetch time is dominated by Last.fm page count and the shared
10 req/s global throttle. `lastfm.py` already uses `limit=200`, concurrent
`as_completed` fetching, and `MAX_CONCURRENT_LASTFM=10`; the old sequential
diagnosis was from the pre-implementation design and is no longer accurate.

**Measured data (2026-05-16, local, concurrent):**
- `flounder14`: 103 pages, 10.9s wall-clock.
- Rate-limit floor at current config: 103 pages / 10 req/s = 10.3s minimum.

**Root cause:** `_GlobalThrottle` serializes aggregate Last.fm traffic across
all job threads at `LASTFM_REQUESTS_PER_SECOND` (default 10). This protects
against upstream 429s and is shared by album and heatmap jobs.

**Optimization options after Batch 19:**
1. **Heatmap-specific caching** for same-user repeat requests inside a short
   TTL. This avoids refetching but must account for the rolling 365-day window.
2. **Progressive rendering** so users see partial activity while pages arrive.
   This adds route/JS complexity and should be scoped separately.
3. **Higher Last.fm rate limit** only if the owner accepts 429 risk. Official
   Last.fm guidance is lower than the current 10 req/s setting, so raising it
   is not recommended without load testing.

Priority: P1 -- directly impacts user experience, but no further fetch-speed
work is in Batch 19.

### F-B18-12: pill tabs mismatched in width

The "Album Filtering" pill is wider than "Heatmap" due to different text
lengths and no `min-width` constraint. Owner flagged this after testing.
CSS fix: add `min-width` to `.mode-pill` in `heatmap.css` so both pills
are the same width. To be fixed in a Phase 2 WP.

---

## P0 -- Fix before next deploy

_No open P0 items._

---

## P1 -- Next batch candidates

### Concurrency & deployment

2. **Concurrent user UX when slots are full.** When all 10 `MAX_ACTIVE_JOBS`
   slots are occupied, the user sees "Too many requests in progress. Please
   try again in a moment." on the home page. No indication of how many slots
   are in use. Estimating wait time is not feasible (job durations vary
   21s cached to 5+ min uncached). Showing "N/10 slots in use" or a clearer
   busy state would help.

3. **Dark mode CSS on mobile.** Toggle is fixed-position in footer; may
   overlap content on small screens. Minor CSS polish.
   Source: AUDIT_2026-02-11.

### Test suite gaps

4. **No integration tests in CI.** All 350 tests use mocked dependencies.
   No test makes a real API call, connects to a real DB, or exercises the
   full request-response cycle. The manual scripts (`concurrent_users_test.py`,
   `smoke_cache_check.py`) require a running Flask instance and are not part
   of CI.

5. **Mocks may drift from API reality.** No contract tests or recorded API
   response fixtures. If Last.fm/Spotify change response formats, mocked
   tests pass while production breaks.

6. **No automated JS tests.** Client-side behavior (theme toggle, screenshot
   rendering, progress polling) has no automated test coverage.

### Code quality (verified still open)

7. **`ENTRY_BATCH_RE` too loose.** `parser.py:37` regex can misroute entries
   whose title contains "Batch N" substrings. Tightening requires careful
   backward-compat testing. Source: DOCSYNC_AUDIT Finding 6.

8. **`test_docsync_logic.py` is 852 lines.** Covers sync integration,
   cross-validation, split/merge, and count extraction in one file.
   Suggested split: integration / cross-validate / archive-routing.
   Source: MULTI_AGENT_SWEEP.

9. **Broad `except Exception` catches.** 14 instances across
   `scrobblescope/*.py`. Protects UX but masks root causes. Consider
   narrowing or adding structured logging for exception classes.
   Source: MULTI_AGENT_SWEEP.

---

## P2 -- Scaling roadmap

10. **In-memory `JOBS` dict limits horizontal scaling.** `repositories.py`
    stores job state in a process-local dict. Multiple gunicorn workers or
    Fly.io machines break progress polling. Migration path: Redis or
    Postgres-backed job table.

11. **Celery/Redis RQ for task queue.** Current daemon-thread model works
    for single-worker single-machine. Horizontal scaling requires a real
    task queue. **Owner decision:** out of scope until features complete.

12. **Process-local Spotify token cache.** `config.py` `spotify_token_cache`
    is per-process; multiple workers cause redundant refreshes. Acceptable
    at current scale.

13. **REQUEST_CACHE growth with always-on machines.** If Fly.io machines
    stay on permanently, cleanup is opportunistic (runs at job start, not
    on a timer). TTL mitigates but doesn't cap memory.

---

## Info -- Design decisions (no action needed)

14. **In-memory `REQUEST_CACHE` is intentional.** Avoids re-fetching Last.fm
    pages when a user re-searches the same year with different filters.
    Clears on machine sleep. By design.

15. **Spotify cache TTL is ToS-compliant.** Verified 2026-03-04. Cache hits
    do NOT refresh `updated_at`. Albums expire 30 days from last Spotify
    API call regardless of access frequency.

16. **Pre-slicing reduces Spotify API load.** Playcount filter + 500-album
    playtime cap applied before cache lookup.

17. **Orchestrator splitting deferred to post-Batch 18.** `orchestrator.py`
    (920 lines) mixes workflow, business rules, result shaping, and error
    classification. Now that Batch 18 adds a second pipeline (`heatmap.py`),
    shared patterns (event loop setup, progress mapping, error guards) are
    prime candidates for extraction. See F-B18-1 above. Revisit after both
    pipelines exist and work end-to-end.

---

## Load test data (2026-03-04, local)

Test environment: Flask dev server (Werkzeug, threaded), local `ss-postgres`
Docker container, all caches cleared between runs.

| Concurrent Users | Per-user elapsed | Wall time | Upstream 429s | Outcome |
|------------------|------------------|-----------|---------------|---------|
| 1 (cached)       | 21s              | 21s       | 0             | OK      |
| 2 (uncached)     | 88-106s          | 107s      | 0             | All OK  |
| 3 (uncached)     | 125-201s         | 202s      | 0             | All OK  |
| 5 (uncached)     | 115-268s         | 269s      | 0             | All OK  |
| 10 (partial)     | 216-353s         | ~6min     | unknown       | 6/10 OK |

**Caveat:** Local tests use Werkzeug (threaded HTTP). Production was single
sync gunicorn worker (no threads) at time of testing.

**Global throttle:** `_GlobalThrottle` serializes all API calls at 10 req/s
across all job threads. Jobs slow linearly: N jobs sharing 10 req/s =
~10/N req/s per job.

**Last.fm rate config:** App configures 10 req/s; official limit is 5 req/s
averaged over 5 minutes. No 429s observed in testing, but aggressive.

---

## Feature preparation notes

18. **Top songs feature.** Rank most-played tracks for a year. Needs Last.fm +
    possibly Spotify enrichment. Deferred; heatmap (Batch 18) takes priority.

19. **Listening heatmap feature.** Last.fm-only scrobble density calendar for
    365 days. No Spotify calls. Batch 18 completed the working end-to-end
    feature; Batch 19 is polishing the result frame, KPIs, pill labels,
    pinwheel animation, and mobile layout on `feat/heatmap`.

---

## Source documents

- `docs/history/DOCSYNC_AUDIT_2026-02-25.md` -- 11 findings, detailed code refs
- `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md` -- Full architecture sweep
- `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` -- Earlier audit
- `docs/history/AUDIT_2026-01-10.md` -- Rate limit regression audit
- Agent memory: `load-test-findings.md` -- Raw load test data and analysis
