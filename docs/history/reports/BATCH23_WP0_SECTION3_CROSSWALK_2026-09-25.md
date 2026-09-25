# Batch 23 WP-0 Section 3 crosswalk -- 2026-09-25

## Resume decision

`docs/agents/PLAYBOOK.md` Section 3 is the current work order.
`BATCH23_DEFINITION.md` owns WP-0 scope and acceptance. The
2026-09-25 completed-work review checks the most recent finished tasks.
The 2026-09-24 handoff and the gitignored SDD ledgers describe earlier
snapshots; their root-cleanup resume instructions have been overtaken by
commits through `7d159b60`. The untracked 2026-09-23 handoff naming
reconcile Task 8 is also an older snapshot and remains untouched.

The next unfinished work is Part C's three follow-on plans, in the
reconcile plan's "After this plan" order: control plane, frontend, then
test infrastructure and dependencies. The definition keeps WP-0 open
until its listed findings and final reviews meet acceptance.

## Owners of removed Section 3 material

Ranges below refer to Section 3 at `7d159b60`, before this cleanup.
Each row identifies where the removed material belongs; it does not
replace those owners.

| Old lines | Material | Owner |
|---|---|---|
| 72-113 | Completed Batches 18-22 and Batch 22 work packages | PLAYBOOK Section 2; archived batch definitions and `docs/history/logs/BATCH22_LOG.md` |
| 114-121 | 2026-09-24 handoff state | `docs/history/reports/HANDOFF_2026-09-24.md`, now marked historical |
| 122-132 | PR #234/#236 chronology; #235/#237/#238 integration | This cleanup's dated Section 4 entry owns #234/#236; `docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md` Step 6 records #235/#237/#238 |
| 133-140 | PR #241 and the next PR target | `docs/history/reports/HANDOFF_2026-09-24.md` Sections 1 and 6 |
| 141-157 | Request identity, provider contact, gate split, MusicBrainz fix | `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, F-B21-51 in the findings archive, and this cleanup's Section 4 entry for the dated contact report |
| 158-167 | Batch 23 opening | `BATCH23_DEFINITION.md` header and PLAYBOOK Section 3's retained active-batch line |
| 168-202 | Part A, reconcile tasks and their order | `BATCH23_DEFINITION.md` WP-0; the foundation and reconcile plans; dated execution entries |
| 203-262 | Foundation and root-cleanup tasks; WP-0 logging | The two checked plans, their dated execution entries, and `BATCH23_DEFINITION.md` WP-0 |
| 263-282 | Completed-work review, old test-count incident, owner live check | `docs/history/reports/BATCH23_WP0_COMPLETED_WORK_REVIEW_2026-09-25.md`; F-DOCSYNC-11 and F-DOCSYNC-13; reconcile plan Q0 |
| 283-301 | Batch 21 UI and PR #227 follow-up | `docs/history/definitions/BATCH21_DEFINITION.md`, `docs/history/logs/BATCH21_LOG.md`, and the PR #227 reports |
| 302-387 | Batch 21 remediation and prior PRs | The Batch 21 definition and log, linked PR reports, and the named findings |
| 388-413 | Batch 21 WP-7 close and deferred audit | Batch 21 definition and log; `BATCH23_DEFINITION.md` WP-7 owns the audit now |
| 414-428 | Spotify export rationale and older owed commits | `BATCH23_DEFINITION.md` owner rulings and dated execution entries |
| 429-442 | Design traversal, performance and Last.timer notes | `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`; F-B18-11 and F-B19-3 |
| 443-446 | Top songs candidate | `docs/agents/FINDINGS.md` F-FEATURE-1 |

## Verification boundary

The current branch was checked at `7d159b60` before editing. Git
confirmed the #234 and #236 merge commits and the eight commits between
their branch tips; the dated Section 4 entry preserves that correction.
The codebase graph generation predates this batch and excludes `docs/`,
so this map uses direct document reads and targeted text searches.
