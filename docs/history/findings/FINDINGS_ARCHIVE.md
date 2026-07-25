# FINDINGS Archive

Resolved and no-action findings rotate here from `FINDINGS.md` at batch
close-out (or during dedicated findings-cleanup WPs) so the active file
stays short while grep history is preserved. Entries keep their original
F-IDs and text; nothing here is deleted. Newest rotation first.

---

## Rotated 2026-07-24 (Batch 20 WP-7)

### F-B19-6 (follow-up portion): register naive-tz anti-pattern in AGENTS.md -- RESOLVED

The remaining open portion of F-B19-6 (the code fix was archived in WP-6
below) was closed in Batch 20 WP-7: the naive-tz vacuous-datetime-test
anti-pattern is now item 6 in the AGENTS.md Anti-Pattern Registry, citing
`tests/test_heatmap.py::TestAggregateDailyCounts::
test_utc_decode_invariant_against_local_tz_drift` as the canonical
regression example.

## Rotated 2026-07-24 (Batch 20 WP-6)

### F-B20-1: README/SESSION_CONTEXT test-file count drift -- RESOLVED

`README.md` and `.claude/SESSION_CONTEXT.md` claimed "24 test files" while
the tree held 22 pytest modules. Corrected in Batch 20 WP-1 (README) and
via the machine-managed SESSION_CONTEXT refresh; the stale "389 tests,
24 test files" line in the FINDINGS header was the last occurrence, fixed
in WP-6. Recorded for audit completeness and archived immediately.

### Resolved since last update (2026-03-02)

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

### F-B18-6: dark mode uses body.dark-mode class, not data attributes -- RESOLVED

CSS uses `.dark-mode` class toggled by `theme.js`. Original Batch 18
definition referenced `[data-theme="dark"]` which does not exist. Corrected
in the audited definition; informational only since then.

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

### F-B18-9: username not sanitized for JS/SVG injection -- RESOLVED

Routes validate that a username exists on Last.fm but do no input
sanitization beyond that; usernames are echoed back in JSON and rendered
client-side. Addressed during Batch 18: `heatmap.js` renders all
user-supplied strings via `textContent` (never `innerHTML`), with the
criterion cited at the top of the file ("No innerHTML with user data
(XSS criterion F-B18-9)"). Verified still true 2026-07-24.

### F-B19-1: loading state still read as a card -- RESOLVED

Owner review showed the pinwheel centered inside a large Bootstrap card-like
box. That made the loading state feel broken even after the earlier clipping
fix. The follow-up removed the card wrapper and uses an unframed loading panel
with a larger SVG-bounded pinwheel. The final SVG keeps the original
breathing/expanding blade animation; the simplified rotating replacement was
rejected during owner review. Fixed in Batch 19 owner-review follow-up.

### F-B19-2: heatmap sizing needed separate desktop and mobile treatment -- RESOLVED

Desktop screenshots at 1440p and 1080p showed the heatmap grid taking too
little visual space because the result container was still constrained by the
Bootstrap `col-md-8` width. Mobile review showed calendar-constrained layouts
either left excessive side space or made cells too small. The follow-up
widened only `#heatmap-result` on desktop and replaced the mobile layout with
a sequential activity strip that fills the frame width with larger cells,
plus mobile headline fitting. Fixed in Batch 19 owner-review follow-up.

### F-B19-5: visual-verification tooling -- NO ACTION

The Browser plugin/skill is the right Codex-side tool when its browser MCP
tools are exposed. In the Batch 19 session, deferred tool discovery did not
expose a callable browser screenshot tool, and shell-launched headless Chrome
did not emit screenshots in the sandbox. For future UI-heavy batches, enable
a Browser/Playwright MCP path if available. No new Python or Node package is
recommended solely for visual QA.

### Load test data (2026-03-04, local) -- HISTORICAL RECORD

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

### F-B19-6 (code-fix portion): naive-tz day-attribution bug -- RESOLVED

PR #152 review (Gemini) surfaced that `scrobblescope/heatmap.py` decoded
Last.fm UTS values with naive `datetime.fromtimestamp` and built the fetch
window with naive `datetime.now()`. On Fly.io (UTC container) this was
silently fine; on local Windows dev or any non-UTC host it shifted day
attribution by hours. Code fixed in PR #152 (commit `ccb000f`) with
`tests/test_heatmap.py::TestAggregateDailyCounts::
test_utc_decode_invariant_against_local_tz_drift` as the canonical
regression test. The follow-up (register the naive-tz vacuous-test
anti-pattern in AGENTS.md) was closed in Batch 20 WP-7; see the WP-7
rotation block above.
