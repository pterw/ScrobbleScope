<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# FINDINGS_ARCHIVE -- page 0005

### F-B21-9: the findings-to-issues mirror is manual -- NO ACTION

Open findings were mirrored to GitHub issues #174-#215 on 2026-08-22. The
mirror ran once, from a script that was not committed.

Nothing keeps it current. A new finding does not open an issue. A resolved
finding does not close one. The two lists will drift.

This was deliberate, not an oversight. A sync script is code. It needs tests
and a work package. It did not belong in the documentation PR that created
the mirror.

What a sync needs: open an issue for each finding that has none, close the
issue when its finding resolves, and never write back to `docs/agents/FINDINGS.md`. The
file stays the source of truth. Issues are a read-only mirror.

**Owner ruling, 2026-09-20:** the sync has to run in both directions --
GitHub issues to `docs/agents/FINDINGS.md` as well as out -- so neither side can become
the only place a defect is recorded.

- [x] **Status:** no action
**Completed:** 2026-09-25
Owner ruling 2026-09-25: findings are not mirrored to GitHub, because `docs/agents/FINDINGS.md` is committed and can be followed there. The sync is not built, which supersedes the 2026-09-20 two-way ruling and the reconcile plan's Q15 sync answer. Issues #174-#215 stay as a frozen 2026-08-22 snapshot.
Was recorded as: open, deferred on purpose. The owner accepted the drift on
2026-08-22 and asked that the work be recorded rather than done now.
Source: findings mirror, 2026-08-22.

### F-B23-8: the WP-0 definition lagged completed Part B records -- RESOLVED

The Batch 23 definition left the completed foundation Tasks 4-10 and
root-cleanup Tasks 0-8 unchecked after PLAYBOOK Section 3 and both plans
recorded them done. It also pointed six rotated finding records at the
active file, where they no longer lived. A new agent could read the checked
plan tasks and the definition as conflicting work orders.

The definition now checks those two completed Part B bullets and points to
the findings archive. The Section 3 cleanup bullet stays open because that
work has not been done; WP-0 remains next.

- [x] **Status:** resolved
**Completed:** 2026-09-25
Source: Batch 23 WP-0 completed-work review, 2026-09-25.

### F-B23-7: an empty release-check pass has no finish log -- RESOLVED

`run_release_checks` logged a start for a job with zero eligible candidates,
then marked it done and returned before its finish log. This is a normal
outcome, so the Stage 4 provider-log contract's start/finish pair was absent
in the case the worker can complete without opening a cache connection.

The zero-candidate branch now emits the same finish fields as a processed
pass. The existing empty-candidate test asserts both log lines and the done
state without a DB call.

- [x] **Status:** resolved
**Completed:** 2026-09-25
Source: Batch 23 WP-0 completed-work review, 2026-09-25.

### F-DOCSYNC-21: document declarations can hide a live file or escape the repository -- RESOLVED

The root-cleanup `[documents]` loader accepted duplicate or aliased paths, so
`--check` could exit 0 after scanning one declared role twice and omitting
another. It also read an outside-root document before failing with an uncaught
`ValueError`. An external `--config` passed `--check` but a writing mode
refused it at the publication boundary. The 2026-09-25 review reproduced all
three paths against the real CLI or its publication transaction.

The declaration loader now resolves and checks all five live roles, including
the fixed `AGENTS.md`, before reading documents. It rejects duplicate,
traversing, absolute, symlinked and directory paths. An explicit config path
must resolve inside the repository, so checks and writing modes agree and the
transaction can prove its source snapshot. Regression tests and live CLI
probes cover the duplicate and outside-path cases.

- [x] **Status:** resolved
**Completed:** 2026-09-25
Source: Batch 23 WP-0 completed-work review, 2026-09-25.

### F-DOCSYNC-17: an active batch with no logged work package rendered as between batches -- RESOLVED

Section 3's status block treated a batch Section 3 declares open, with no
work package logged yet, as "between batches," and the next-package rule
gave up on an empty block instead of naming WP-0 -- the state every batch
enters the moment its branch is named, so a false next-package claim could
pass DOC007 right as the batch opened.
- [x] **Status:** resolved
**Completed:** 2026-09-21
the status block now branches on the declared batch rather than on whether entries exist, and the next-package rule counts WP-0 as next under a finite plan.
Source: foundation Task 3 live-probe audit, `aad26e5`.

### F-DOCSYNC-18: the archive page target had no reader, and the cold rule's all-dated condition was undocumented -- RESOLVED

`ArchiveStore.page_target_issues` could already detect an unpaginated
archive over `[archives] max_lines` and a hot page not fully dated, but
`--check` raised neither as a diagnostic, and
`documentation-tooling.md` described the cold rule only as "365 days,"
leaving its all-dated requirement unstated.
- [x] **Status:** resolved
**Completed:** 2026-09-23
DOC024 (warning severity) now fires on both conditions, and documentation-tooling.md states what the cold rule actually checks.
Source: foundation Task 4, `d499e3a`.

### F-B23-6: provider calls leave no trace in the log -- RESOLVED

Testing Batch 22's MusicBrainz corrections, the owner could not tell from the
log whether any MusicBrainz call was made, or how it ended. The release-check
worker logs nothing on success, and `enqueue_release_check` skips silently
when MusicBrainz is disabled or `MUSICBRAINZ_CONTACT` is unset.
`musicbrainz.py` and `deezer.py` contain no log call at all. Last.fm and
Spotify log some failures, each in its own words, so a 429, a 404 or a
timeout reads differently depending on which provider returned it.

Every provider builds its HTTP session in `utils.create_optimized_session`,
so one `aiohttp` trace hook there can log every call in one format. It must
not log query strings: they carry Last.fm's API key, and the artist and album
search terms that `BATCH23_DEFINITION.md`'s Data handling section keeps out
of logs.

- [x] **Status:** resolved
**Completed:** 2026-09-24
Every provider call is logged by `api_logging` through
`create_optimized_session`, and the release worker logs its start, finish
and skip.

### F-STYLE-1: repository prose is denser than it needs to be -- NO ACTION

The goal is writing that is easier to read, not conformance to a standard.
ASD-STE100 Simplified Technical English names the target well: short
sentences, active voice, one idea per sentence, lean docstrings that say what
a function does and why, and no coined compound terms where a plain phrase
exists. It is an example of the goal, not a standard this repository adopts.

**This is not a gate and cannot become one.** The ASD-STE100 dictionary is
licensed and unavailable here, so no agent can check anything against it, and
no automated check scores prose quality. Declaring it a rule would also
trigger anti-pattern 11 in `AGENTS.md`, which requires a claim to be applied
across the corpus in the commit that states it -- a sweep far larger than the
benefit. Treat this as standing guidance for text you are already editing.

Concrete instance: `AGENTS.md` carries the coined term "blast-radius"
hyphenated in two places, and the spaced phrase "blast radius" in one more.
Locate them by the term; the line numbers drift with every insertion above
them. Later agent sessions copy it from there. Replace it with the
plain phrase, such as "search the repo for other copies of the same claim",
when those lines are next edited for another reason.
- [x] **Status:** no action
**Completed:** 2026-09-23
Owner ruling 2026-09-23: standing prose guidance with no fix state -- it cannot become a gate, and its one example was already rewritten in `14ba5705`; the guidance stands for future edits.
Source: owner style direction, 2026-08-19.

### F-STYLE-2: Python style settings disagree, and Ruff is planned but unwritten -- NO ACTION

Three separate problems that one decision settles.

**Docstring convention.** Measured 2026-08-19 across tracked Python outside
`tests/` (38 files, via `git ls-files "*.py"` plus an `ast` walk of every
function, async function and class): 204 definitions, 171 carrying a
docstring (84%), and 4 using Google sections such as `Args:` or `Returns:`
(2%). Adopting Google sections everywhere is a 167-definition sweep across
the documented ones, plus 33 that carry no docstring at all. That size is why
this is a finding and not a rule. Re-measure before quoting these numbers.

**Line length and the stale `.flake8` note are settled.** Ruff replaced black,
isort, autoflake and flake8 in `c7bfaec` on 2026-09-07, and `pyproject.toml`
`[tool.ruff]` now owns one line length, 88. The orphaned `.flake8` -- still
claiming 120 and calling its ignores temporary, with nothing left that reads
it -- was deleted on 2026-09-21.

What remains is the docstring convention alone: adopt Google sections or
not. Defer the sweep; record the decision.
- [x] **Status:** no action
**Completed:** 2026-09-23
Owner ruling 2026-09-23: no docstring convention is adopted -- a sweep of the undocumented-section definitions buys no test or gate; line length and the stale `.flake8` were settled earlier.
Source: root-hygiene side task, 2026-08-19.

### F-B21-53: the surface-card token now sits darker than the page it lifts off -- NO ACTION

The owner's 2026-09-07 surface split (`d41db1f`) moved `--ss-surface-card`
from `#fcfbf8` to `#f9f7f1` and added `--ss-surface-card-standout: #ffffff`
for the index card alone. Against the `#faf8f3` page, that reverses the sign
of the intended lift: the deployed card was 2 channel steps lighter than the
page (contrast 1.026:1), and the current one is 1 step darker (1.009:1).

Neither value reads as a raised surface unaided -- at these ratios the 1px
`--ss-border-default` rule (1.25:1 against the page) is doing all the
separating work. But the deployed direction was at least upward, and the owner
reports the deployed aesthetic as the better one. At the initial measurement, the Results KPI rail still consumed this token.
The later owner refinement moved Results panels and the table to a midpoint
between page and sunken; the general card token itself was not changed.

Decide at the token: either return the light-theme card to a value above the
page, or accept that cards are delineated by rule rather than by fill and stop
describing them as elevated. The dark theme is unaffected (`#181520` card on
`#0e0c12` page is a clear lift).

- [x] **Status:** no action
**Completed:** 2026-09-23
Owner ruling 2026-09-23: the light card is delineated by its border, not lifted by its fill; the UI stays as it is.
Source: owner-reported stat-bar background regression, 2026-09-09.

### F-B21-4: four screens where the design bundle contradicts itself -- NO ACTION

The design handoff imported to `docs/design/` carries two documents that
disagree. `docs/design/README.md` is canonical. `docs/design/reference/
audit-review.md` is a later second-pass critique, and it dissents on four
screens:

1. **Index hero -- DECIDED 2026-08-24 (owner), README wins.** WP-3 shipped
   the two-column split. Items 2, 3 and 4 stay open for WP-4, WP-5 and WP-7;
   do not close this finding on the strength of this one ruling.
   The README specifies a two-column `1.1fr 1fr` editorial
   split. The review calls it a generic SaaS landing layout applied to a tool
   whose users arrive to type a username and press go, and asks for a single
   centred column. It names this "the thing to challenge first".
2. **Loading signals.** The README specifies pinwheel, phase line, progress
   bar, three stats and a parameter tag row. The review counts that as five
   simultaneous progress signals and wants the pinwheel and phase line always,
   the bar only when the value is real.
3. **Results KPIs.** The README specifies three sidebar stat blocks. The
   review says two of them restate row 1 of the list, and only albums matched
   versus albums seen earns a card.
4. **Unmatched fix line -- DECIDED 2026-09-13 (owner), 12px.** The README sets
   it at 9px mono uppercase. The review says the most actionable text in the
   product is at the smallest, hardest-to-read size, and asks for 11px sentence
   case. The owner ruled 12px mono, still uppercase, for the fix hint and the
   per-panel "albums" label. It meets the 12px floor RECONCILIATION section 1
   records. See RECONCILIATION section 16, Superseded 5.

`docs/history/definitions/BATCH21_DEFINITION.md` encodes the README's side on the first two: WP-3 says
"Editorial hero", WP-4 specifies the pinwheel, bar, phase label, four-KPI
strip and chip row together.

Item 2 has support inside the canonical bundle itself:
`docs/design/components/feedback/ProgressBar.d.ts` documents `value` as "Only
show it when the value is real; otherwise show the pinwheel alone." WP-4
should read that before deciding.

- [x] **Status:** no action
**Completed:** 2026-09-23
Items 1, 2 and 4 are settled: item 1 by `templates/index.html` `.index-grid` (the two-column split), item 2 by RECONCILIATION's loading-signal override, and item 4 by RECONCILIATION section 16, Superseded 5. Item 3 is folded into Batch 23 WP-6.
Source: design handoff import, 2026-08-21. Owner ruling on precedence the
same day. See `docs/design/RECONCILIATION.md`.

### F-B21-15: the heatmap stays on the index page, and the split waits -- NO ACTION

WP-3 kept the heatmap form, wait panel and result frame on `index.html` and
extracted three Jinja partials instead of a page. The Batch 18 decision that
all states live on one page with no navigation still stands, and the owner
reaffirmed it on 2026-08-23.

The split only pays for itself alongside the deferred
`GET /heatmap/<username>` item under "Out of scope" in
`docs/history/definitions/BATCH21_DEFINITION.md`. Without a route, a separate template cannot be
reached, linked or shared, and the frontend gate cannot see it either --
which is the same reason `LEGACY_PAGES` is empty.

The partials are the enabler. `templates/partials/_loading.html` is
framework-neutral and parameterised by id, so a future page can include it
without inheriting the index's script wiring.

- [x] **Status:** no action
**Completed:** 2026-09-23
Owner ruling 2026-09-23: Batch 23 schedules no `GET /heatmap/<username>` route, and the split pays off only with it; reopen when a batch schedules shareable heatmap URLs.
Source: Batch 21 WP-3, owner decision 3, 2026-08-23.

### F-B21-19: heatmap mobile and day-detail behaviour drifted from the design -- NO ACTION

Two canonical heatmap requirements have no ruling and do not match the PR:

- `docs/design/components/heatmap/HeatmapFrame.prompt.md` requires four
  stacked, season-labelled 13-week strips on a phone with the same cell size.
  `docs/history/definitions/BATCH21_DEFINITION.md` and the WP-3 plan also say to keep the 14px cell.
  `renderHeatmapMobile()` instead chooses 10 to 28 columns and 18px to 28px
  cells from container width, producing one unlabelled sequential grid. The
  product README was rewritten to describe that implementation, but the
  reconciliation file has no owner-approved override.
- `docs/design/README.md` says hovering a day reveals what was played. The
  heatmap payload contains only `daily_counts`, and the tooltip renders only
  date plus count, so the client has no track detail it could reveal.

The export sibling is recorded under F-B21-18 rather than duplicated here.
The mobile requirement needs a product ruling before code: implement the four
strips, or explicitly override the canonical handoff. Day detail changes the
response contract and is a future-batch feature if the canonical requirement
stands.

- [x] **Status:** no action
**Completed:** 2026-09-23
Owner ruling 2026-09-23 (Q12 = a): the width-driven mobile grid is recorded as an owner-approved override in `docs/design/RECONCILIATION.md` section 1; day detail (hover reveals what was played) is a future feature, since the payload holds only `daily_counts`.
Source: independent PR #218 specification review, 2026-08-25.

### F-B21-24: the index does not use large displays well -- NO ACTION

The owner runs a 1080p and a 1440p monitor and reports that dragging the window
to the larger one leaves too much whitespace: the content keeps its size and
the margins absorb the extra width.

PR #220 added a source-level viewport-scale path, the compact-height padding
rule, the 12px label floor, reduced capability-mark tracking, and the light
muted-text contrast. The source path did not ship usable proportional
composition scaling. The later owner-review layout, hierarchy, boundary,
loading-progress, and unmatched-empty-state work also remains incomplete. In
particular, the live source still used the interim wide split and a centred
`23.75rem` form cap until Task 3 landed the final `3fr 4fr` split and
`27.5rem` owner-refined base cap.

Measurement on 2026-09-01 named the cause. The formula divides window height by
the 1080px design viewport instead of by the composition's own 673px height,
and an unconditional `min()` then lets browser chrome discard the width term on
every real window. The browser gate missed it because `set_viewport_size` sets
the content box exactly, so the gate measured `2560x1440` -- a geometry no
maximised window has. Chromium and Firefox measured the same composition width
to within 0.1px at four window sizes, so this is not an engine defect and
Firefox evidence is not the acceptance condition. Realistic window geometry is.

`docs/superpowers/plans/2026-09-01-batch21-index-scaling-and-review-remediation.md`
is the sole acceptance specification for the reopened work. It records the
1080p comparison needed before any global header-density decision.

- [x] **Status:** no action
**Completed:** 2026-09-23
Tasks 2-5 shipped; Task 6, the accessibility pass, is the same work as Batch 23 WP-7's audit and runs there (owner ruling 2026-09-13).
Source: owner large-display review, 2026-08-28; owner clarification and
measurement, 2026-09-01.

### F-WORKTREE-4: three guard files exceed their directory peer caps -- NO ACTION

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

- [x] **Status:** no action
**Completed:** 2026-09-23
Owner ruling 2026-09-21 (PR #169 review round 4): none of the three files approaches a monolith, and a split adds inventory drift for no gain; revisit when one next changes substantially.
Source: PR #169 review round 4.

### F-MAS-2: no automated JS tests -- NO ACTION

Theme toggle, export, polling, and heatmap rendering have no automated
coverage.

- [x] **Status:** no action
**Completed:** 2026-09-23
Owner ruling 2026-09-23: absorbed into F-B21-18, which covers the same untested JavaScript in more detail.
Source: MULTI_AGENT_SWEEP.

### F-B23-5: the release-window rule is written twice -- RESOLVED

`domain._matches_release_criteria` decides whether a release date fits the
user's scope, for the album filter. `release_checks._window_end` computes the
last year that scope accepts, for the correction worker. Each restates the
same table (`same`, `previous`, `decade`, `custom`), so a new scope or a
change to the decade rule must be made in both. Foundation Task 12 moved the
first to `domain.py` to break an import cycle; the second stayed behind.

The two already differ at the edges. An unparseable decade (the route does
not validate `decade`) makes the filter exclude every album, with a warning
that names the release date rather than the decade; the worker gets no
window. The worker also accepts the year as a string, and the filter does
not.

The fix is one window function in `domain.py`, with both consumers derived
from it and their current outputs pinned by parity tests first.

- [x] **Status:** resolved
**Completed:** 2026-09-23
`domain.release_window` is the rule's one owner; the album filter and the
worker's window end both derive from it.

### F-B22-8: release checks skip the whole job when the cache DB is down -- RESOLVED

`release_checks.run_release_checks` opens a cache connection before its first
MusicBrainz request, and when none is available it logs "Release checks
skipped: the cache DB is unavailable.", marks the job `skipped` and returns.
The reason in its comment is cost: a finding that cannot be persisted buys one
job's display and nothing for the next. The corrections the results page shows
are the product, though, and the cache is only how they are reused. So a
reachable MusicBrainz is left unasked because a different service is down, and
the reader of that page gets no correction at all.

Seen on 2026-09-23. The owner ran the app locally with `ss-postgres` stopped,
and the log showed the skip line after three failed connection attempts. A
later run with Postgres up wrote 60 rows to `original_release_cache` within a
minute of the job finishing. So the worker works, and only the DB-down branch
withholds it.

Impact is local development only. On Fly.io the Postgres machine wakes with
the app, so the branch is not reached in production. That is why this is P2.

- [x] **Status:** resolved
**Completed:** 2026-09-23
`run_release_checks` runs its candidates without a cache connection and
skips only the cache read, the persist and the close.
Source: owner local run, 2026-09-23.

### F-LOAD-1: concurrent-user UX when job slots are full -- RESOLVED

With all `MAX_ACTIVE_JOBS` slots busy (default 5 since 2026-07-31; was
10), users get "Too many requests in progress" with no occupancy hint.
An "N/<cap> slots in use" hint would help, with the cap read from the
configured `MAX_ACTIVE_JOBS` at render time rather than written as a
literal -- deployments that override the env var must show their own
capacity, and a literal silently goes stale at the next default change
(it read "N/10" until 2026-07-31).
- [x] **Status:** resolved
**Completed:** 2026-09-23
both refusals read `routes._capacity_message()`, which states the configured `MAX_ACTIVE_JOBS`.
Source: load testing 2026-03-04.

### F-B21-6: the year gate reads host-local time, the fetch window reads UTC -- RESOLVED

`scrobblescope/routes.py` calls naive `datetime.now()` in three places:
`:135` (the `current_year` template global), `:302` (the results-page year
fallback), and `:436` (the submit-path validation gate). F-SWE-2 corrected
the same pattern in `orchestrator.py` and did not touch `routes.py`.

`:436` is the one with a consequence. It derives `current_year` from
host-local time and refuses any request where `year > current_year`. The data
window for an accepted year is then built in UTC in `fetch_top_albums_async`
(`scrobblescope/orchestrator.py` at the time, now
`scrobblescope/orchestrator/__init__.py`). Gate and window now disagree by the
host's UTC offset, and the disagreement is observable only in the hours
around New Year:

- Host behind UTC: UTC has rolled over, the gate has not. A request for the
  new year is refused as out of range.
- Host ahead of UTC: the gate has rolled over, UTC has not. The request is
  accepted and the orchestrator builds a window entirely in the future, so
  the fetch returns nothing.

The two agreed before F-SWE-2, because both were naive. Fixing the window was
correct; it left the gate behind. **Do not fix this by reverting
`orchestrator.py`** -- move the three call sites to
`datetime.now(timezone.utc)`.

Production runs UTC, so this is a developer-host defect rather than a
production one. That is the reason it is not P0, not a reason to leave it.

- [x] **Status:** resolved
**Completed:** 2026-09-23
every year gate reads `routes._current_year()`, which uses `datetime.now(timezone.utc)`.
Source: WP-1 parallel review.

### F-SWE-5: the two background entry points disagree about terminal job state -- RESOLVED

`heatmap_task` and `background_task` answer the same question two different
ways, and both answers are wrong.

`heatmap.py:218-221` catches every exception and reports
`lastfm_unavailable`. `_fetch_and_process_heatmap` has no inner handler, so
this is the only handler on the path and it fires for any failure at all.
Verified: a `ZeroDivisionError` raised inside the aggregation step reaches
the user as a Last.fm outage message, with `error_source: lastfm` and
`retryable: True`. The app blames a third party for its own bug and invites
a retry that will fail the same way.

`background_task`'s outer handler (`orchestrator.py` at the time, now
`scrobblescope/orchestrator/__init__.py`) has the mirror-image gap: it logs
and sets no job state, so the job never reaches progress 100 and the loading
page polls forever. This half needs `_fetch_and_process`'s inner handler
(same module) to fail first, which nothing observed can cause, so the finding is recorded rather
than treated as blocking. F-SWE-6 used to compound it, because a polled job
never expired; since F-SWE-6 was settled, the stuck job expires
JOB_TTL_SECONDS after its last write.

Fix: give each entry point a terminal state that names what actually
failed, using an `ERROR_CODES` entry for an unclassified internal error
rather than borrowing an upstream one.
- [x] **Status:** resolved
**Completed:** 2026-09-23
both entry points publish `internal_error` from their outer handler (`heatmap._report_heatmap_failure`,
`orchestrator._report_album_failure`); `loading.js` names only a known upstream
Source: SWE_PRINCIPLES_AUDIT.

---
