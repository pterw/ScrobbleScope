# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Batch index (completed batches archived; the active batch, if any, is listed last)

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` | -- |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` | -- |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` | -- |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` | `docs/history/logs/BATCH3_LOG.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` | `docs/history/logs/BATCH4_LOG.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` | `docs/history/logs/BATCH5_LOG.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` | `docs/history/logs/BATCH6_LOG.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` | `docs/history/logs/BATCH7_LOG.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` | `docs/history/logs/BATCH8_LOG.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` | `docs/history/logs/BATCH9_LOG.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` | `docs/history/logs/BATCH10_LOG.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` | `docs/history/logs/BATCH11_LOG.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` | `docs/history/logs/BATCH12_LOG.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` | `docs/history/logs/BATCH13_LOG.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` | `docs/history/logs/BATCH14_LOG.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` | `docs/history/logs/BATCH15_LOG.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` | `docs/history/logs/BATCH16_LOG.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` | `docs/history/logs/BATCH17_LOG.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` | `docs/history/logs/BATCH18_LOG.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` | `docs/history/logs/BATCH19_LOG.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` | `docs/history/logs/BATCH20_LOG.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

A batch's close-out entry sits in its per-batch log only when the heading
carried a `(Batch N WP-X)` tag (as Batch 18's did). Close-outs tagged
`(Batch N close-out)` are not parser-recognized and were routed to the
monolith archive instead -- Batches 19 and 20 are the current examples.
See FINDINGS F-DOCSYNC-3.

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan and the test-infrastructure/dependencies plan are both fully
  executed (every task in each has landed). The three plans' carried items
  are closed out, and their final code review of the whole branch ran on
  2026-09-27; its one fix wave has landed and passed a scoped re-review
  (see Section 4). Next action: the WP-0 close-out below. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-09-29 - docsync refuses declared paths and pin rewrites it cannot trust

Side task, no batch tag: the second-review fix wave for the docsync declarations, the test-count pin writer and the worktree guard (review findings B1-B6, B8, B9 and C1-C5), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
B1, B9: a `[documents]` path must be written in the normalised repository-relative form every reader keys documents by. `./x` or `a//b` is refused with the spelling to write, and an empty value says it is empty.
B2-B4: `--fix --test-count N` parses its rewrite and publishes only the original declarations with `test_count.pinned` changed. Any other result exits 2 and writes nothing.
B5, C3, C1, C5: `[untracked_essentials]` refuses a backslash, any character `str.isprintable()` rejects, an empty path and `.`. A repeated path is reported once, and a directory at the declarations path is an error, not "nothing declared".
C2, C4: WT015's read-failure warning carries the failure class only, never the absolute path or OS text, and points to `doc_state_sync.py --check`. WT004 labels an unsafe base ref once.
B6, B8: the preflight's pin-only exemption decodes `git show` as UTF-8 and fails closed on a blob that is not. DOC025 and the close-out admission refusal name the `--config` file actually read.
`docs/architecture/documentation-tooling.md` is updated to match.
Validation: `pytest -q` -- **N passed**.

### 2026-09-29 - Cache only well-formed Last.fm pages; cancel orphaned fetches

Side task, no batch tag: the second code-review findings A1 and A2 (Last.fm page cache and orphaned fetches), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
A1: `fetch_recent_tracks_page_async` cached any 200 that parsed as JSON, so a first page
with no `@attr`, or an error payload served as a 200, was replayed to every retry for
REQUEST_CACHE_TIMEOUT. A new `_is_well_formed_page` predicate (a `recenttracks` mapping with
an integer `@attr.totalPages`) now gates `set_cached_response`. The body is still returned
unchanged.
A2: when one page raised (the mid-job 404 `ValueError`), sibling page fetches stayed
pending on a closing session. `_cancel_and_drain` now cancels and awaits them before the
unwrapped exception leaves, in the `as_completed` path and in `fetch_pages_batch_async`.
Nine tests were added to `tests/services/test_lastfm_service.py`, each proved by mutation.
Validation: `pytest -q` -- **N passed**.

### 2026-09-29 - Rebuild the unmatched report rows and show portraits whole

Side task, no batch tag: the owner-delegated audit of the unmatched report and F-B23-12, part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
The table loses its fourth "Reason detail" column. A row's note sits under the artist instead:
the shortfall on a threshold row ("3 plays and 1 track short", new `describe_shortfall`), the
reason on a release row, and nothing on a no-match row. At 390px the album title has 144-160px
(it had 51-67px). Headline, panel titles and buttons are sentence case. The subtitle gives the
year and the count, and the attribution is a plain line with 12px text on both pages
(RECONCILIATION section 18). F-B23-12: every cover, portrait and placeholder uses
`.provider-artwork`, so artwork is never cropped and corners are 4px, or 8px from 768px.
F-B23-14: the portrait had never loaded, because it was hidden and `loading="lazy"`. The
attribute is gone. The gate's wide and tall portraits now have URLs of their own and must load
whole, inside their slot. F-B23-15 is open for the owner. Edited tests:
test_group_unmatched_albums_groups_by_reason_code,
test_unmatched_view_success_renders_grouped_reasons.
Validation: `pytest -q` -- **2073 passed**.

### 2026-09-28 - Drop the spotlight's unreachable guards

Side task, no batch tag: removed the spotlight's dead code (`hidePortrait`, three name guards in `hydrateCandidate`, its unused `view` parameter), part of Batch 23 WP-0 Part C. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.
Code-review finding 8. Rotation only renders candidates that already have a confirmed
`image_url`, and `hydrateCandidate` writes only its own index before the array is replaced, so
none of that code could fire. The `hydrateCandidate` docstring now says so. No behaviour change.
Validation: `pytest -q` -- **2055 passed**.
