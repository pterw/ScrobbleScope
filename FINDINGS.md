# ScrobbleScope Findings & Open Issues

Last updated: 2026-05-19
Status: Batch 19 closed out; `feat/heatmap` PR #152 open against `main` with
two Gemini-Code-Review-driven fixes applied (UTC timestamps, nested
daily_counts isolation, streak boundary). 389 tests, 24 test files.
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
- ~~F-B18-8 nested daily_counts shared by reference~~ -- `get_job_context`
  now explicitly copies `results["daily_counts"]` in addition to the outer
  dict. Closed during PR #152 review (Gemini Code Review catch).

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

### F-B18-8: get_job_context shallow-copies results but not nested dicts -- RESOLVED

**Status:** resolved during PR #152 review (Gemini Code Review catch).
`get_job_context()` now explicitly does `results["daily_counts"] =
dict(results["daily_counts"])` after the outer dict copy, restoring the
function's stated contract for heatmap result shape. Variant chosen over
`copy.deepcopy` because the polling hot path runs every ~1s per active
job and the nested structure is well known. New regression test:
`tests/test_repositories.py::test_get_job_context_nested_daily_counts_is_isolated`.

Historical context: `repositories.py` `get_job_context()` originally
copied list results via `list(results)` but did not copy dict results at
all (returned the original reference). A Boy Scout fix added an
`elif isinstance(results, dict): results = dict(results)` branch, but
that was still a shallow copy, leaving the nested `daily_counts` shared
by reference. PR #152 review surfaced this; the fix above closes it.

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

## Batch 19 owner-review findings (2026-05-19)

### F-B19-1: loading state still read as a card

Owner review showed the pinwheel centered inside a large Bootstrap card-like
box. That made the loading state feel broken even after the earlier clipping
fix. The follow-up removes the card wrapper and uses an unframed loading panel
with a larger SVG-bounded pinwheel.

Status: fixed in Batch 19 owner-review follow-up. The final SVG keeps the
original breathing/expanding blade animation; the simplified rotating
replacement was rejected during owner review.

### F-B19-2: heatmap sizing needed separate desktop and mobile treatment

Desktop screenshots at 1440p and 1080p showed the heatmap grid taking too
little visual space because the result container was still constrained by the
Bootstrap `col-md-8` width. Mobile review showed the opposite failure after
the prior reduction pass: cells were no longer heavy, but calendar-constrained
mobile layouts either left excessive side space or made cells too small.

Follow-up direction: widen only `#heatmap-result` on desktop, keep the rest of
the page unchanged, and replace calendar-constrained mobile layouts with a
sequential activity strip that fills the heatmap frame width with larger cells.
The headline also needs mobile fitting so common usernames avoid a forced line
break.

Status: fixed in Batch 19 owner-review follow-up; owner visual approval still
required.

### F-B19-3: last.timer is not a drop-in heatmap speedup

The referenced `last.timer` project fetches Last.fm aggregate endpoints:
`user.gettopartists` and `user.gettoptracks`, with `limit=1000`, page fan-out,
and `Promise.all` for remaining pages. That is appropriate for top-track
period summaries, but it does not provide per-scrobble timestamps needed for an
exact day-by-day heatmap.

Potential future experiments:
1. Test whether `user.getrecenttracks` reliably accepts `limit=1000`; current
   ScrobbleScope uses the documented conservative `limit=200`.
2. Add heatmap-specific cached daily aggregates for repeat same-user requests.
3. Add progressive rendering if partial heatmap feedback is worth the extra
   route and client complexity.

Status: documented for a future performance batch; no Batch 19 API change.

### F-B19-4: broader front-end UI audit should be a separate batch

Low-risk local heatmap changes are fine in Batch 19, but a global UI overhaul
should not be folded into owner-review fixes. Open audit notes:

- Bootstrap is split across CDNs: `base.html` uses cdnjs for CSS, while
  `index.html` uses jsdelivr for the Bootstrap JS bundle and other pages use
  cdnjs. A future batch should standardize the source before considering a
  Bootstrap upgrade.
- Bootstrap 5.3 color modes could reduce `.dark-mode .table`,
  `.dark-mode .modal-content`, and `.dark-mode .form-control` overrides, but
  upgrading from 5.1.3 risks component regressions and should be tested as its
  own WP.
- Global Geist font, Bootstrap variable overrides, warm surfaces, and inky
  purple palette should be handled in `global.css`/`base.html` as a dedicated
  UI batch, not piecemeal in heatmap follow-up work.
- Index popovers/tooltips are visually large relative to form labels and
  should be reviewed with form density, label sizing, and mobile tap targets in
  the same UI batch.
- Dark-mode table/export CSS remains scattered across `results.css`,
  `unmatched.css`, and `results.js`; Bootstrap 5.3 or shared CSS tokens may
  reduce that duplication.

### F-B19-5: visual-verification tooling

The Browser plugin/skill is the right Codex-side tool when its browser MCP
tools are exposed. In this session, deferred tool discovery did not expose a
callable browser screenshot tool, and shell-launched headless Chrome did not
emit screenshots in the sandbox. For future UI-heavy batches, enable a
Browser/Playwright MCP path if available. No new Python or Node package is
recommended for Batch 19 solely for visual QA.

### F-B19-6: naive-tz vacuous-test anti-pattern

PR #152 review (Gemini) surfaced that `scrobblescope/heatmap.py` decoded
Last.fm UTS values with naive `datetime.fromtimestamp` and built the fetch
window with naive `datetime.now()`. On Fly.io (UTC container) this was
silently fine; on local Windows dev or any non-UTC host it shifted day
attribution by hours.

The deeper finding -- worth recording so it does not repeat -- is that the
**test pyramid did not catch it**. `tests/test_heatmap.py` constructed UTS
values using the same naive `datetime.combine(...).timestamp()` pattern that
the SUT decoded. Boundary tests like `test_midnight_boundary_attribution`
passed only because the SUT and tests shared the same naive-tz interpretation:
the test was effectively comparing the SUT against itself, not against an
invariant. This is the **vacuous-test pattern** AGENTS.md forbids ("Every
test must fail if the function under test is deleted") in a subtler form --
the test fails if the function is deleted, but does *not* fail if the function
silently regresses to a naive-tz bug.

**Anti-pattern to register in AGENTS.md (future):** any datetime test that
builds inputs with the same tz-awareness pattern (naive vs aware) as the SUT
is at risk of being vacuous against tz bugs. Build inputs with explicit
`tzinfo=` and assert on a date that would shift under a naive interpretation.

The PR #152 fix added `tests/test_heatmap.py::TestAggregateDailyCounts::
test_utc_decode_invariant_against_local_tz_drift` as the canonical example.

Status: code fixed in PR #152 (commit `ccb000f`). AGENTS.md addition is
deferred to the next bootstrap/docs batch -- noted here as a forward TODO.

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
