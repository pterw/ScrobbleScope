# ScrobbleScope Findings & Open Issues

Last updated: 2026-08-12
Status: Batch 21 (UI overhaul -- Tailwind + daisyUI migration) is ACTIVE;
WP-0 done; PR #170 lands first, then the F-SWE-1 audit, then WP-1.
589 tests across 35 test modules.

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

## Resolved this batch

### F-WORKTREE-1: Rebase merges leave linked branches history-diverged

GitHub rebase merges rewrite commit identities on `main` without moving the
linked worktree branch, producing a branch that is both ahead and behind even
when its tree is identical; after PRs #163, #165, and #168 this repeatedly
created a risk of phantom PRs, duplicate work, or an incorrect merge.
Status: resolved 2026-08-05. Evidence: the read-only CLI distinguishes
behind-only, identical-tree rebase artifacts, and true divergence; the
canonical bootstrap stops on its errors; and live linked-worktree inspection
reported the expected branch and ancestry without modifying Git. Review
remediation adds final WT013 context to every offline result and keeps
custom-base guidance aligned with the caller-selected ref. Final review
remediation preserves the public facade; WT014 fails closed without traceback or
sensitive runner text, and exact severity plus real CLI tests protect every WT
code. Shared fixtures create host-appropriate tools; host-rendered missing-tool
assertions and simulated POSIX inspection protect the Ubuntu CI boundary.
Source: post-merge lineage investigations for PRs #163, #165, and #168.

### F-WORKTREE-2: Linked worktrees cannot use the relative virtualenv path

The sole `.venv` is gitignored under the primary checkout, so a fresh shell in
a linked worktree cannot run the documented relative activation or test
commands; an uninformed agent may create a forbidden second environment or
fall back to bare pip and reproduce dependency drift.
Status: resolved 2026-08-05. Evidence: the live linked-worktree guard reported
Python, pytest, and pre-commit under the primary checkout's existing `.venv`,
and AGENTS now forbids a second environment and requires those qualified paths.
Source: repository-integrity design validation on 2026-08-05.

### F-DOCSYNC-5: Operational doc metadata drifted across path and branch changes

The live archive prologue and active-definition branch metadata drifted while
`doc_state_sync.py --check` and CI remained green because prefixes were opaque,
live-document references were only narrowly checked, and integrity warnings
did not affect the exit code.
Status: resolved 2026-08-05. Evidence: final-state CLI enforcement rejects
conflicting test fields, dead optional-session references, non-unique tracked
root definitions, and sanitized Git discovery failures; `pytest -q` measured
**521 passed** with 3 existing warnings on the final combined remediation.
Approved design:
`docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.
Source: PR #168 pre-merge audit and follow-up root-cause investigation.

---

### F-DOCSYNC-4: per-batch logs were undiscoverable; tombstones retained

Until 2026-07-31 the 18 `docs/history/logs/BATCHN_LOG.md` files were
referenced by no working doc (PLAYBOOK Section 2 had no Log column), so
batch history was reachable only via a directory glob. Fixed: Section 2
gained a Log column and the AGENTS.md close-out procedure fills it per
batch. Related disposition: the two ~300-byte
`docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` and
`docs/history/logs/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` are deliberate Batch 14
"Moved:" tombstones kept
for backward references -- not cruft, do not delete.
Status: resolved 2026-07-31; rotates to the archive at Batch 21
close-out. Source: PR #163 doc-hygiene pass.

---

## P1 -- Next batch candidates

### F-DOCSYNC-6: known DOC001 and count-derivation boundaries

Cases the PR #169 review round confirmed and deliberately left unfixed
because each needs a design decision rather than a patch:
four-space indented blocks are still scanned for references, because the
canonical documents use that indentation for list continuations and
excluding it would silently disable DOC001 across much of AGENTS.md;
prose added after the last Section 4 entry is never reference-checked;
`cli.py` glob discovery is case-insensitive on Windows and case-sensitive
on Linux while candidate matching uses `re.IGNORECASE`; a live document
resolving outside the working directory raises `ValueError` rather than
the documented exit 2; and a file deleted on disk with the deletion
unstaged still counts as tracked.
Status: open. Source: PR #169 independent review.

### F-WORKTREE-3: guard boundaries outside the design decision table

Confirmed but unaddressed: between batches the guard skips every ancestry
check by design, which is exactly when the rebase-merge artifact appears,
so a genuinely diverged branch passes silently; WT010 never fires for a
detached dirty worktree, which returns WT012 alone; and
`missing_base_remediation` receives an already-labelled ref, so an unsafe
ref name renders as "the local base ref configured base ref".

The fourth item originally listed here -- `resolve_venv` deriving the primary
checkout from the common Git directory's parent -- was fixed in this PR's
round-2 remediation, which discovers the main working tree with
`git worktree list --porcelain` and passes it in. The remaining three are
unchanged.
Status: open. Source: PR #169 independent review.

### F-DOCSYNC-7: `_latest_test_count_from_entries` has no production caller

The bare-count wrapper lost its last production caller when the integrity gate
moved to `latest_test_count_authority`. It is now exercised only by its own
unit tests in `tests/test_docsync_logic.py`, which is the same condition that
led to `_cross_validate` being removed rather than kept.

Deliberately not removed in the review round that created the condition:
deleting it also rewrites eight test call sites, which is a refactor rather
than a review fix. Remove it and repoint those tests at
`latest_test_count_authority` in a hygiene pass.
Status: open. Source: PR #169 review round 5.

### F-WORKTREE-4: three guard files exceed their directory peer caps

Review remediation grew three files past the peer-size rule in the Proposal
and Design Rules. Measured, with the pre-existing peer that sets each cap:

| File | Lines | Peer cap |
|------|-------|----------|
| `scripts/dev/_worktree_guard_inspection.py` | 256 | 236 (`scripts/dev/dev_start.py`) |
| `tests/scripts/dev/test_worktree_guard_venv.py` | 270 | 184 (`tests/scripts/dev/test_dev_start.py`) |
| `tests/scripts/dev/test_worktree_guard_inspection.py` | 192 | 184 (same) |

All three were within their caps before the review rounds -- inspection was
217, then 227 -- and crossed while fixing confirmed defects. Splitting them
was considered and declined by the owner: the rule exists to prevent
unmaintainable monoliths, none of these approaches that, and restructuring
files mid-review invites another round of inventory drift for no
maintainability gain. Recorded rather than fixed so no document claims a
compliance that does not hold.

Revisit when any of these files next changes substantially; the natural seam
in the collector is Git/topology collection versus diagnostic orchestration.
Status: open (accepted deviation). Source: PR #169 review round 4.

### F-WORKTREE-5: display-unsafe branch candidates are dropped before the conflict check

`parse_batch_branch` filters candidates through `is_display_safe_ref` and only
then counts them, so a Section 3 naming both `wip/batch-21` and a second,
Git-valid branch holding a non-ASCII letter resolves to the ASCII one instead
of failing closed on conflicting metadata. The guard then reports an aligned
checkout even though the document declared two different branches.

The ordering was deliberate in the PR #170 round-2 remediation, on the
reasoning that a candidate failing the predicate "can name no real branch".
That reasoning does not hold: `is_display_safe_ref` is deliberately narrower
than Git's ref rule, so a rejected candidate can still name a real branch --
which is the whole basis of F-WORKTREE-5. What the predicate decides is
whether a value may be *rendered*, not whether it may *exist*.

Not changed in the round that found it, because reversing a deliberate
decision needs its own reasoning rather than a review-round patch, and
reachability is low: it requires two `Branch:` values in Section 3, one of
them non-ASCII. The fix is to count candidates before filtering and let a
conflicting pair raise the existing GuardError.
Status: open. Source: PR #170 review round 5 (Codex).

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

With all `MAX_ACTIVE_JOBS` slots busy (default 5 since 2026-07-31; was
10), users get "Too many requests in progress" with no occupancy hint.
An "N/<cap> slots in use" hint would help, with the cap read from the
configured `MAX_ACTIVE_JOBS` at render time rather than written as a
literal -- deployments that override the env var must show their own
capacity, and a literal silently goes stale at the next default change
(it read "N/10" until 2026-07-31).
Status: open. Source: load testing 2026-03-04.

### F-AUDIT-1: dark-mode toggle placement on mobile

Fixed-position footer toggle may overlap content on small screens.
Batch 21 moves the toggle into the standing header bar; its acceptance
criterion on tap-target size names this finding as closed by that work.
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

### F-MAS-3: test_docsync_logic.py covers several unrelated seams

One module holds WP collection, test-count authority, whole-sync
integration, log merging, archive splitting, dedup, and Section 3 parsing.
Splitting along those class boundaries stays worthwhile. The originally
suggested `cross-validate` seam no longer exists -- that helper and its
tests were removed on this branch. Count authority is now split across two
files rather than extracted from this one: `TestLatestTestCount` still holds
the unit cases here, while `tests/test_docsync_test_count.py` covers the
behaviour through `_sync`. Consolidating them is part of the same split.

No line count is quoted here deliberately: the figure in the original
finding went stale as soon as the file changed, and size was never the
defect. Compare against the largest peer in the directory when deciding
whether the split is due.
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

### F-DATA-1: reissue editions collapse onto the original's cache row

`normalize_name()` strips `deluxe`/`edition`/`remastered`/`anniversary`
and seven more words from the album string, so
`"viagr aboys (Deluxe Edition)"` and `"viagr aboys"` both normalize to
`viagr aboys`. The `spotify_cache` primary key is
`artist_norm + album_norm`, so **both editions share one row** holding
whichever release populated it first, for the 30-day TTL. When the
reissue wins that race its `release_date` is served for the original.

Observed 2026-07-31: Viagra Boys "viagr aboys" (2025) appears under
`release_scope: same` for 2026, matching the JP deluxe released
2026-01-09, on an account that never played the deluxe.

The collapse is not a bug on its own -- it is what makes matching work
across Last.fm's inconsistent album strings, where the same record is
scrobbled as `Album`, `Album (Deluxe Edition)`, and `Album - Deluxe`
depending on the reporting client. Keying editions apart would fragment
one album into several leaderboard rows with split playcounts, which is
a worse defect than an occasional wrong year. Collapsing is correct for
*counting* and wrong for *dating*; the two need decoupling, not one
shared key.

Candidate fix (untested): keep the collapse for aggregation, but when
resolving `release_date`, select the **earliest** date among candidate
Spotify matches instead of whichever cached first. The original predates
its reissues by construction, and this approximates the "Original
Release Date" that Deezer's API team confirmed is a separate field from
the digital release date labels supply. No schema change required.

Rejected: a boolean `is_deluxe` discriminator. The stopword list has 11
entries that combine freely (deluxe, expanded, anniversary, JP deluxe),
so a boolean still collides variant-against-variant. Retaining the
stripped tokens as a variant tag would work but reintroduces the
fragmentation above.

Open questions, answerable by investigation rather than speculation:
1. Do the scrobbles themselves carry the deluxe title? Last.fm stores
   whatever album metadata the player reported, which is a second
   independent path to the same result.
2. Which other albums are affected? **Not answerable from the cache
   alone:** `(artist_norm, album_norm)` is the primary key
   (`init_db.py:42`) and the upsert overwrites the single stored
   `release_date`, so there are no sibling rows and no losing candidate
   dates to compare against. Detection requires re-running the Spotify
   search for each cached album and flagging rows whose stored date is
   later than the earliest candidate in the fresh result set, or
   cross-checking against an external original-release source
   (MusicBrainz, per the note below).
3. Can both a Latin-script deluxe and a JP deluxe surface at once? Only
   if the JP title carries Japanese characters -- NFKC preserves those,
   so it would not collapse; a Latin-script `(Deluxe Edition)` always
   merges to one row.

Note: Spotify exposes no original-release-date field. `release_date`
belongs to the matched release object, and `release_date_precision`
(`year`/`month`/`day`) only reports granularity. Disambiguation must
come from the search result set, the discarded `(Deluxe Edition)`
suffix, or `total_tracks`. MusicBrainz does carry original release
dates -- a lookup narrowed to that single field, cached, is far smaller
than the full-enrichment attempt abandoned in 2025.

Status: open (P2). Low user impact -- one recalled instance across ~14
years of scrobbles, and `release_scope: all` bypasses date filtering
entirely. Source: session 2026-07-31.

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
Affects only close-outs written with that suffix: BATCH19_LOG.md and
BATCH20_LOG.md lack their close-out entries (both sit in the monolith),
while Batch 18's close-out was tagged `(Batch 18 WP-5)` and routed
correctly. Per-batch history is therefore incomplete for the affected
batches without a monolith grep. Fix belongs in a docsync
WP together with F-DOCSYNC-1/F-DOCSYNC-2 (make close-out tags parseable,
then one-time re-route of the existing close-out entries); hand-retagging
machine-rotated archive content was declined in PR #162 round 3 and again
in PR #163 round 3 on the same point-in-time principle.
Status: open (P2). Source: PR #163 review round 3.

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
  in Batch 21 scope (WP-6, and the acceptance criterion requiring equal
  mode-pill width) -- no longer a future-batch candidate.
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
- Agent memory: load-test-findings.md (not a repository file) -- raw load
  test data and analysis
