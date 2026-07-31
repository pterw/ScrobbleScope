# ScrobbleScope Findings & Open Issues

Last updated: 2026-07-31
Status: Batch 21 (UI overhaul -- Tailwind + daisyUI migration) is ACTIVE;
WP-0 done, WP-1 next. 390 tests across 22 test modules.

**Rotation policy:** resolved and no-action findings rotate to
`docs/history/findings/FINDINGS_ARCHIVE.md` at batch close-out or during
findings-cleanup WPs; nothing is deleted. Every item uses an
`F-<context>-<N>:` heading (format: AGENTS.md "Finding-Writing Rules").
Read this file on demand -- when a task or PLAYBOOK entry references an
F-* ID or a P0/P1 item -- not as part of the standard bootstrap order.

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
into pipeline / processing / result-shaping modules. Also on the README
roadmap; absorbs F-B18-7. Status: open. Source: Batch 18 audit.

### F-B20-3: Bootstrap CDN source consolidation

`base.html` loads Bootstrap CSS from cdnjs while `index.html` loads the
JS bundle from jsdelivr; other pages use cdnjs. The original remedy
(consolidate to one provider before a Bootstrap 5.1 -> 5.3 upgrade) is
dead: Batch 21 removes Bootstrap entirely and resolves the split by
elimination (`BATCH21_DEFINITION.md` WP-8 "closes F-B20-3").
Status: open; closes at Batch 21 WP-8. Source: F-B19-4 owner review.

### F-B20-4: UI overhaul (driven by owner audit)

Scope, locked decisions, and acceptance criteria live entirely in
`BATCH21_DEFINITION.md` (active batch) -- this entry is a pointer, not a
second copy. Status: in progress (Batch 21 active, WP-0 done).
Source: owner audit (UI Audit v3) + F-B19-4 owner review.

### F-B18-11: heatmap Last.fm page fetch is rate-limit bound

Fetch time is bound by page count and the shared 10 req/s throttle
(2026-05-16: 103 pages, 10.9s vs a 10.3s floor; fetching is already
concurrent at `limit=200`). Options: heatmap-specific caching,
progressive rendering, or a higher rate limit (not recommended). Status:
open; no fetch-speed work scheduled. Source: Batch 18 audit + perf
session 2026-05-16.

### F-LOAD-1: concurrent-user UX when job slots are full

With all 10 `MAX_ACTIVE_JOBS` slots busy, users get "Too many requests in
progress" with no occupancy hint; "N/10 slots in use" would help.
Status: open. Source: load testing 2026-03-04.

### F-AUDIT-1: dark-mode toggle placement on mobile

Fixed-position footer toggle may overlap content on small screens.
Batch 21 moves the toggle into the standing header bar; acceptance
criterion 8 states "toggle meets tap-target size (closes F-AUDIT-1)".
Status: open; closes at Batch 21 WP-2. Source: AUDIT_2026-02-11.

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

### F-SWE-1: SWE-principles audit chartered, pending execution

No differential check of the ten mandated software principles
(AGENT_NOTES.md Owner Preferences) has run since the 2026-02 audits.
`docs/SWE_AUDIT_CHARTER.md` defines scope (Python only until Batch 21
ships), the do-not-re-report baseline, method, and output contract; any
dedicated single-purpose agent session (Claude or Codex) can execute it
cold. Report lands as `docs/history/SWE_PRINCIPLES_AUDIT_<date>.md` with
net-new findings as F-SWE-2 onward; this entry closes by pointing at the
report. Status: open (chartered 2026-07-31, execution pending).
Source: owner request 2026-07-31.

### F-MAS-4: broad `except Exception` catches

17 instances across `scrobblescope/*.py` (recounted 2026-07-24; 14 at
the original sweep); narrow or add structured logging per exception
class. Status: open. Source: MULTI_AGENT_SWEEP.

---

## P2 -- Scaling roadmap

### F-DOCSYNC-2: STATUS block misreports current batch between batches

When a close-out entry (untagged `(Batch N close-out)` suffix) still sits
inside the CURRENT-BATCH markers, `renderer.py:85-86` falls back to
`last_completed + 1` even though the Section 3 parse correctly returns
the between-batches state. Transient: rotation self-corrects it when the
next batch's WP-0 entry lands. Fix candidates: prefer the between-batches
branch whenever the parse returns none, or make close-out tags parseable.
Status: open (P2). Source: PR #162 review round 4.

### F-DOCSYNC-3: close-out entries route to the monolith, not the batch log

Close-out headings use a `(Batch N close-out)` suffix that `ENTRY_BATCH_RE`
does not recognize as batch-tagged, so rotation routes them into the
untagged monolith archive instead of `docs/history/logs/BATCHN_LOG.md`.
Consistent across batches: neither BATCH19_LOG.md nor BATCH20_LOG.md
contains its close-out entry; both sit in the monolith. Per-batch history
is therefore incomplete without a monolith grep. Fix belongs in a docsync
WP together with F-DOCSYNC-1/F-DOCSYNC-2 (make close-out tags parseable,
then one-time re-route of the existing close-out entries); hand-retagging
machine-rotated archive content was declined in PR #162 round 3 and again
in PR #163 round 3 on the same point-in-time principle.
Status: open (P2). Source: PR #163 review round 3.

### F-DOCSYNC-4: per-batch logs were undiscoverable; tombstones retained

Until 2026-07-31 the 18 `docs/history/logs/BATCHN_LOG.md` files were
referenced by no working doc (PLAYBOOK Section 2 had no Log column), so
batch history was reachable only via a directory glob. Fixed: Section 2
gained a Log column and the AGENTS.md close-out procedure fills it per
batch. Related disposition: the two ~300-byte
`PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` files under `docs/history/` and
`docs/history/logs/` are deliberate Batch 14 "Moved:" tombstones kept
for backward references -- not cruft, do not delete.
Status: resolved 2026-07-31; rotates to the archive at Batch 21
close-out. Source: PR #163 doc-hygiene pass.

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

One-line cross-references; detailed bodies live in pre-Batch-20
`FINDINGS.md` (git history before `494f2c7`) or the `docs/history/`
audits; 2026-03-04 load-test data is in the findings archive.

- F-B18-1: orchestrator monolith -- promoted to F-B20-2 above.
- F-B18-2: JOBS dict lacks TypedDict/dataclass annotations.
- F-B18-3: `loading.js` album messaging; extract shared polling utility
  if a third feature emerges.
- F-B18-4: `_check_user_exists` creates a throwaway event loop per call.
- F-B18-5: inline SVG payload growth; lazy-load or sprite if more added.
- F-B18-7: duplicated win32 event-loop guard -- absorbed into F-B20-2.
- F-B18-10: heatmap + album jobs share the 10 req/s throttle (by design).
- F-B18-12: mode pills differ in width (no `min-width` on `.mode-pill`);
  in Batch 21 scope (WP-6, acceptance criterion 8) -- no longer a
  future-batch candidate.
- F-B19-3: last.timer aggregate endpoints are not a drop-in heatmap
  speedup; future perf experiments listed in the archive.
- F-B19-4: front-end UI audit notes -- basis of `BATCH21_DEFINITION.md`.

---

## Feature preparation notes

### F-FEATURE-1: top songs feature

Rank most-played tracks for a year (separate task type + loading/results
flow). Status: deferred; on the README roadmap. Source: owner roadmap.

- F-FEATURE-2: listening heatmap -- shipped in Batches 18/19, archived;
  perf follow-ups continue as F-B18-11.

---

## Source documents

- `docs/history/DOCSYNC_AUDIT_2026-02-25.md` -- 11 findings, detailed code refs
- `docs/history/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md` -- Full architecture sweep
- `docs/history/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` -- Earlier audit
- `docs/history/AUDIT_2026-01-10.md` -- Rate limit regression audit
- `docs/history/findings/FINDINGS_ARCHIVE.md` -- Rotated resolved/no-action items
- Agent memory: `load-test-findings.md` -- Raw load test data and analysis
