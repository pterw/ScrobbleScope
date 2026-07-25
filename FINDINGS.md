# ScrobbleScope Findings & Open Issues

Last updated: 2026-07-24
Status: Batch 20 complete; Batch 21 (UI overhaul) is next, scope pending
the owner's proposal. 390 tests across 22 test modules.

**Rotation policy:** resolved and no-action findings rotate to
`docs/history/findings/FINDINGS_ARCHIVE.md` at batch close-out (or during
dedicated findings-cleanup WPs); nothing is deleted. Every remaining item
uses an `F-<context>-<N>:` heading (contexts: B18/B19/B20 batches; LOAD,
MAS, DOCSYNC, AUDIT source audits; FEATURE prep notes). Read this file on
demand -- when a task or PLAYBOOK entry references an F-* ID or a P0/P1
item -- not as part of the standard bootstrap order.

---

## Severity Key

| Level | Meaning |
|-------|---------|
| **P0** | Fix before next deploy or next batch |
| **P1** | Next batch |
| **P2** | Scaling roadmap / future consideration |
| **Info** | Documented design choice, no action needed now |

---

## P0 -- Fix before next deploy

_No open P0 items._

---

## P1 -- Next batch candidates

### F-B20-2: orchestrator.py second-pass decomposition (promoted from F-B18-1)

`scrobblescope/orchestrator.py` (916 lines) mixes album workflow, Spotify
batch processing, error mapping, progress tracking, and result assembly.
Now that `heatmap.py` provides a second pipeline, extract the shared
patterns (event loop setup including the win32 Proactor guard, progress
mapping, error guards) into a common module and split the orchestrator
into pipeline / processing / result-shaping modules. Same item is on the
README roadmap; absorbs F-B18-7 (duplicated win32 event-loop guard).
Status: open. Source: Batch 18 audit, promoted in Batch 20.

### F-B20-3: Bootstrap CDN source consolidation

`base.html` loads Bootstrap CSS from cdnjs while `index.html` loads the
JS bundle from jsdelivr; other pages use cdnjs. Consolidate to a single
provider before any Bootstrap 5.1 -> 5.3 upgrade.
Status: open. Source: F-B19-4 owner review; README roadmap companion.

### F-B20-4: UI overhaul (driven by owner audit PDF)

Global font stack, palette integration, index card rework, and the
remaining F-B19-4 audit notes; Batch 21 main scope, possible Batch 22
contingency. Status: open; scope lands via `BATCH21_DEFINITION.md`.
Source: owner audit PDF + F-B19-4 owner review.

### F-B18-11: heatmap Last.fm page fetch is rate-limit bound

Fetch time is bound by page count and the shared 10 req/s throttle
(2026-05-16: 103 pages, 10.9s vs a 10.3s floor; fetching is already
concurrent at `limit=200`). Options: heatmap-specific caching,
progressive rendering, or a higher rate limit (not recommended).
Status: open; no further fetch-speed work scheduled.
Source: Batch 18 audit + perf measurement session 2026-05-16.

### F-LOAD-1: concurrent-user UX when job slots are full

With all 10 `MAX_ACTIVE_JOBS` slots busy, users get "Too many requests in
progress" with no occupancy hint; "N/10 slots in use" would help.
Status: open. Source: load testing 2026-03-04.

### F-AUDIT-1: dark-mode toggle placement on mobile

Fixed-position footer toggle may overlap content on small screens; minor
CSS polish, also a Batch 21 note. Status: open. Source: AUDIT_2026-02-11.

### F-LOAD-2: no integration tests in CI

All tests mock dependencies; an in-process `/results_loading ->
/progress -> /results_complete` test is on the README roadmap.
Status: open. Source: load testing 2026-03-04.

### F-MAS-1: mocks may drift from API reality

No contract tests or recorded API fixtures; upstream format changes would
pass mocked tests. Status: open. Source: MULTI_AGENT_SWEEP.

### F-MAS-2: no automated JS tests

Theme toggle, export, polling, and heatmap rendering have no automated
coverage. Status: open. Source: MULTI_AGENT_SWEEP.

### F-DOCSYNC-1: ENTRY_BATCH_RE too loose

`parser.py` batch-tag regex can misroute entries whose titles contain
"Batch N" substrings; tightening needs backward-compat testing. On the
README roadmap. Status: open. Source: DOCSYNC_AUDIT Finding 6.

### F-MAS-3: test_docsync_logic.py is 852 lines

Suggested split: integration / cross-validate / archive-routing.
Status: open. Source: MULTI_AGENT_SWEEP.

### F-MAS-4: broad `except Exception` catches

14 instances across `scrobblescope/*.py`; narrow or add structured
logging per exception class. Status: open. Source: MULTI_AGENT_SWEEP.

---

## P2 -- Scaling roadmap

### F-MAS-5: in-memory JOBS dict limits horizontal scaling

Process-local dict breaks polling under multiple workers/machines;
migration path is Redis or a Postgres-backed job table.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-MAS-6: Celery/Redis RQ for task queue

**Owner decision:** out of scope until features complete.
Status: open (P2, owner-gated). Source: MULTI_AGENT_SWEEP.

### F-MAS-7: process-local Spotify token cache

Redundant refreshes under multiple workers; acceptable at current scale.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-MAS-8: REQUEST_CACHE growth with always-on machines

Cleanup is opportunistic (at job start); TTL mitigates, does not cap.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

---

## Info -- Design decisions (no action needed)

### F-LOAD-3: in-memory REQUEST_CACHE is intentional

Avoids re-fetching Last.fm on re-searches; clears on machine sleep.
Status: standing design decision. Source: load testing 2026-03-04.

### F-LOAD-4: Spotify cache TTL is ToS-compliant

Hits do NOT refresh `updated_at`; 30-day expiry from last API call.
Status: standing design decision. Source: cache verification 2026-03-04.

### F-LOAD-5: pre-slicing reduces Spotify API load

Playcount filter + 500-album playtime cap applied before cache lookup.
Status: standing design decision. Source: load testing 2026-03-04.

---

## Deferred / future-batch candidates (Batch 18/19 audits)

One-line cross-references; full text lives in `docs/history/` audits and
archived definitions; 2026-03-04 load-test data now lives in the archive.

- F-B18-1: orchestrator monolith -- promoted to F-B20-2 above.
- F-B18-2: JOBS dict lacks TypedDict/dataclass annotations.
- F-B18-3: `loading.js` album messaging; extract shared polling utility
  if a third feature emerges.
- F-B18-4: `_check_user_exists` creates a throwaway event loop per call.
- F-B18-5: inline SVG payload growth; lazy-load or sprite if more added.
- F-B18-7: duplicated win32 event-loop guard -- absorbed into F-B20-2.
- F-B18-10: heatmap + album jobs share the 10 req/s throttle (by design).
- F-B18-12: mode pills differ in width (no `min-width` on `.mode-pill`);
  Batch 21 UI candidate.
- F-B19-3: last.timer aggregate endpoints are not a drop-in heatmap
  speedup; future perf experiments listed in the archive.
- F-B19-4: front-end UI audit notes -- basis of `BATCH21_DEFINITION.md`.

---

## Feature preparation notes

### F-FEATURE-1: top songs feature

Rank most-played tracks for a year (separate task type + loading/results
flow). Status: deferred; on the README roadmap. Source: owner roadmap.

(F-FEATURE-2, the listening heatmap, shipped in Batches 18/19 and is
archived; perf follow-ups continue as F-B18-11.)

---

## Source documents

- `docs/history/DOCSYNC_AUDIT_2026-02-25.md` -- 11 findings, detailed code refs
- `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md` -- Full architecture sweep
- `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` -- Earlier audit
- `docs/history/AUDIT_2026-01-10.md` -- Rate limit regression audit
- `docs/history/findings/FINDINGS_ARCHIVE.md` -- Rotated resolved/no-action items
- Agent memory: `load-test-findings.md` -- Raw load test data and analysis
