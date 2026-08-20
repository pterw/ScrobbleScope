# SWE Principles Audit -- ScrobbleScope runtime modules

Executed 2026-08-20 against the charter in `docs/SWE_AUDIT_CHARTER.md`.
Closes FINDINGS.md F-SWE-1.

## Verdict

**Migration is blocked by F-SWE-2.** One net-new correctness defect sits in
`orchestrator.py`, which Batch 21 WP-7 modifies. Charter Section 6 sends that
combination to "fix, or obtain an explicit owner waiver, before WP-1 begins".

The block is narrow and cheap to clear. The defect does not affect the live
site, because the Fly.io container runs UTC and the bug only shows on a
non-UTC host. It does affect every local development machine, including the
owner's. The fix is two lines plus a regression test that mirrors one the
repository already has. The finding below states the case for a waiver as
plainly as the case for the fix; the decision is the owner's.

Five further net-new findings (F-SWE-3 to F-SWE-7) are record-and-continue.
None of them blocks WP-1.

## Provenance

Recorded from live commands, per charter Section 2a.

```
git rev-parse --abbrev-ref HEAD          -> wip/batch-21
git rev-parse HEAD                       -> 1994673878020e3fe612e1eaff925b17fba96567
git status --porcelain                   -> (empty)
git ls-files 'scrobblescope/*.py' app.py -> 14 files
```

The worktree was clean before grading began and clean after it finished.

**The graded tree is the same code as `bb187ae`.** `git diff --name-only
bb187ae HEAD -- 'scrobblescope/*.py' app.py tests/` returns nothing. The five
commits between `main` and this SHA change documentation only. A grade
recorded here therefore also describes `main` as it stands today.

**Module list confirmed.** 13 graded modules, plus `scrobblescope/__init__.py`
which is still 0 bytes and correctly carries no matrix row.

**Principle count confirmed.** `AGENT_NOTES.md` Owner Preferences names ten:
DRY, SoC, SRP, KISS, Dependency Inversion, Composition over Inheritance, Clean
Architecture, Boy Scout Rule, Least Knowledge, Fail Fast. 13 x 10 = **130
cells, all filled.**

**Staleness warning.** WP-7 modifies `routes.py` and `orchestrator.py`. The
rows for those two modules expire when WP-7 lands and must be re-graded, not
carried forward.

## Discovery commands and their output

Both commands from charter Section 5c were run from the repository root,
exactly as written.

Longest function definitions:

```
14 files, 99 function definitions
 151  scrobblescope/orchestrator.py:719  _fetch_and_process
 112  scrobblescope/routes.py:405  results_loading
 109  scrobblescope/heatmap.py:89  _fetch_and_process_heatmap
 108  scrobblescope/orchestrator.py:274  _run_spotify_batch_detail_phase
 107  scrobblescope/orchestrator.py:513  process_albums
  89  scrobblescope/routes.py:268  results_complete
  81  scrobblescope/routes.py:520  heatmap_loading
  79  scrobblescope/orchestrator.py:193  _run_spotify_search_phase
  78  scrobblescope/orchestrator.py:433  _build_results
  78  scrobblescope/lastfm.py:169  fetch_all_recent_tracks_async
  73  scrobblescope/lastfm.py:72  fetch_recent_tracks_page_async
  71  scrobblescope/orchestrator.py:56  fetch_top_albums_async
  61  scrobblescope/utils.py:286  retry_with_semaphore
  55  scrobblescope/spotify.py:91  fetch_spotify_album_details_batch
  50  scrobblescope/heatmap.py:37  _aggregate_daily_counts
```

Broad exception catches: **17**, matching the 2026-07-24 recount in F-MAS-4.
Locations are listed under "Broad catches" below, with a judgment on each,
which is the part F-MAS-4 never carried.

## The matrix

13 graded modules by 10 principles. Grades follow charter Section 5a. An A
carries the letter alone, because an A records the absence of a
counter-example and an absence has no line to cite. B, C, D and N/A cells
carry their evidence in "Cell evidence" below.

Key: DI = Dependency Inversion, CoI = Composition over Inheritance,
CA = Clean Architecture, BSR = Boy Scout Rule, LoD = Least Knowledge,
FF = Fail Fast.

| Module | DRY | SoC | SRP | KISS | DI | CoI | CA | BSR | LoD | FF |
|---|---|---|---|---|---|---|---|---|---|---|
| `app.py` | A | B | B | A | B | N/A | A | A | A | **C** |
| `cache.py` | A | A | A | A | B | N/A | A | A | A | B |
| `config.py` | A | A | A | A | A | N/A | A | A | A | **C** |
| `domain.py` | B | A | A | A | N/A | N/A | A | N/A | A | B |
| `errors.py` | A | A | A | A | N/A | A | A | A | A | A |
| `heatmap.py` | B | A | A | A | B | N/A | A | A | A | **C** |
| `lastfm.py` | A | A | A | A | B | N/A | A | N/A | A | B |
| `orchestrator.py` | **C** | **D** | **D** | B | B | N/A | A | A | B | **C** |
| `repositories.py` | A | A | **C** | A | B | N/A | A | A | A | B |
| `routes.py` | B | B | B | A | B | N/A | A | A | B | B |
| `spotify.py` | A | A | A | A | B | N/A | A | N/A | A | **C** |
| `utils.py` | A | **C** | B | A | B | A | A | N/A | B | B |
| `worker.py` | A | A | A | A | B | N/A | A | N/A | A | A |

Distribution: **A 74, B 28, C 8, D 2, N/A 18 = 130.**

Ten C and D cells. Two map to an existing open finding; eight produce six
net-new findings. No cell was graded C or D without a disposition.

## Cell evidence

Only B, C, D and N/A cells appear here. Every unlisted cell is an A.

### `app.py`

- **SoC B, SRP B** -- `app.py:12-75` runs `load_dotenv`, console
  reconfiguration, `os.system("")`, `os.makedirs` and full logging setup at
  import, before the factory is reached. Known: AUDIT_2026-02-27 item 3,
  "app.py performs side-effectful logging/config setup at import time". Not
  re-raised.
- **DI B** -- `create_app` imports `scrobblescope.routes` inside the function
  body (`app.py:131`) rather than at module scope. A deliberate cycle-break,
  contained to one line.
- **CoI N/A** -- no classes.
- **BSR A** -- two commits in the window. `21a3b4c` widened log rotation and
  documented the reason inline; the SECRET_KEY validator arrived with tests.
  Both left the file better than they found it.
- **FF C** -- `ensure_api_keys()` is called only under the `__main__` guard
  (`app.py:140-145`), and production starts with `gunicorn app:app`
  (`Dockerfile:15`). See **F-SWE-4**.

### `cache.py`

- **DI B** -- `_DATABASE_URL` is captured at import (`cache.py:18`). Already
  declined, with the Windows reason recorded at `cache.py:13-17` and in
  REPOSITORY_SYNTHESIS 7.8.
- **CoI N/A** -- no classes.
- **FF B** -- `_get_db_connection` returns `None` on every failure instead of
  raising (`cache.py:36-69`). Fail-open by intent, the three failure classes
  are logged under distinct labels, and callers degrade correctly.

### `config.py`

- **CoI N/A** -- no classes.
- **FF C** -- `ensure_api_keys` is defined at `config.py:37` and never reached
  in production. Same defect as the `app.py` FF cell. See **F-SWE-4**. The
  module's other startup behaviour is correct: `int(os.getenv(...))` at import
  raises immediately on a malformed override, which is what Fail Fast asks
  for.

### `domain.py`

- **DRY B** -- `normalize_track_name` (`domain.py:65-69`) repeats the
  NFKC-normalize, punctuation-translate, split-and-rejoin sequence that the
  inner `clean` already implements (`domain.py:37-48`). A change to the
  normalization rule must be made in both places. Five lines, obvious on
  sight, and the two functions have genuinely different signatures. Graded to
  the lower severity per the rubric's tie-break.
- **DI N/A, CoI N/A** -- a two-function leaf with no dependencies and no
  classes.
- **BSR N/A** -- no commits since 2026-03-01, so the principle has no window
  to judge.
- **FF B** -- an album named entirely from metadata words normalizes to the
  empty string rather than raising. Contained, and the dating consequence is
  already tracked as F-DATA-1.

### `errors.py`

The cleanest module in the matrix alongside `worker.py`. It is a data table
plus one exception class, it declares its leaf status in its own docstring
(`errors.py:6`), and the code matches the claim.

- **DI N/A** -- imports nothing.
- **CoI A** -- `SpotifyUnavailableError(RuntimeError)` at `errors.py:45`.
  Subclassing an exception is the correct use of inheritance; composition has
  no purchase here, so this is an A rather than an N/A.

### `heatmap.py`

- **DRY B** -- the win32 event-loop guard at `heatmap.py:211-215` duplicates
  `orchestrator.py:892-896`. Known as F-B18-7, absorbed into F-B20-2. Not
  re-raised.
- **DI B** -- concrete module imports throughout, consistent with the project.
- **BSR A** -- three commits. `ccb000f` is the model case: it fixed the naive
  timezone bug and added `test_utc_decode_invariant_against_local_tz_drift`
  as a pinned regression.
- **FF C** -- `heatmap.py:218-221` catches every exception and reports it as
  `lastfm_unavailable`. `_fetch_and_process_heatmap` has no inner handler, so
  this is the only handler on the path. See **F-SWE-5**. F-B21-1 also lives in
  this function (`heatmap.py:211-216`, loop built outside the `try`); it is
  open and is not re-raised here.

### `lastfm.py`

- **DI B** -- concrete imports.
- **BSR N/A** -- no commits in the window.
- **FF B** -- `check_user_exists` returns `exists=True` when the lookup fails
  (`lastfm.py:66-69`), so a broken check does not block a search. The choice is
  commented at the site. One inconsistency is worth a reader's attention: the
  same HTTP 404 produces `exists=False` here and a raised `ValueError` in
  `fetch_recent_tracks_page_async` (`lastfm.py:111-114`). Both are defensible
  in isolation, and nothing today has to work around the difference.

### `orchestrator.py`

- **DRY C** -- the Last.fm fetch window is built twice, and the two copies
  disagree. `orchestrator.py:70-71` uses naive `datetime`; `heatmap.py:116-122`
  uses explicit UTC. See **F-SWE-2**.
- **SoC D, SRP D** -- 916 lines carrying workflow control, business rules,
  result shaping and error classification. This is the module's shape, not an
  instance in it. Maps to open **F-B20-2**; no new entry.
- **KISS B** -- `orchestrator.py:827-835` writes progress 60, 80 and 90 with no
  work between the three calls. Harmless, but it makes the progress bar report
  stages that do not exist.
- **DI B** -- concrete imports.
- **CoI N/A** -- no classes.
- **CA A** -- the import set matches SESSION_CONTEXT Section 4 exactly, and the
  graph stays acyclic.
- **BSR A** -- one commit in the window, `01a7904`, which fixed nested-dict
  aliasing and cited the finding it closed.
- **LoD B** -- `orchestrator.py:11-16` imports four underscore-prefixed names
  from `cache.py`. Reaching past a module's public surface normally earns a C,
  but every function in `cache.py` is underscore-prefixed, so there is no
  public surface to prefer, there is exactly one importer, and the direction
  agrees with the documented graph. Contained; stated rather than raised.
- **FF C** -- `background_task` (`orchestrator.py:912-913`) logs an unhandled
  error and leaves the job non-terminal. See **F-SWE-5**.

### `repositories.py`

- **SRP C** -- `get_job_progress`, `get_job_unmatched` and `get_job_context`
  each write `updated_at` while their docstrings claim only to return a copy
  (`repositories.py:163`, `:175`, `:199`). See **F-SWE-6**.
- **DI B** -- `JOBS` and `jobs_lock` are module-level globals
  (`repositories.py:10-11`). Known as F-MAS-5 and accepted for the
  single-worker deployment.
- **CoI N/A** -- no classes.
- **FF B** -- every mutator returns `False` for an unknown job rather than
  raising. The contract is uniform across all eight mutators and each
  docstring states it.

### `routes.py`

- **DRY B** -- `results_loading` (`routes.py:458-502`) and `heatmap_loading`
  (`routes.py:568-598`) repeat the same protocol: clean up expired jobs,
  acquire a slot, create a job, start a thread, delete the job if the start
  fails. The bodies differ because one renders HTML and the other returns
  JSON, and the shared part is about eight lines.
- **SoC B, SRP B** -- `results_loading` is 112 lines covering form parsing,
  three validation passes, slot acquisition, job creation, thread start and
  template rendering. ROUTES_SOC_AUDIT_2026-02-21 extracted four helpers from
  this file and recorded in its Section 4 what it deliberately left. The
  remaining shape is readable and linear.
- **DI B** -- `background_task` and `heatmap_task` are imported concretely
  (`routes.py:6-8`), so the HTTP layer names its background workers directly.
- **CoI N/A** -- no classes.
- **LoD B** -- `_extract_job_params` (`routes.py:34-46`) knows the internal
  shape of the `params` sub-dict. Contained to one helper, which is why the
  helper exists.
- **FF B** -- `unmatched_view` calls `int(year)` at `routes.py:384` without the
  `None` guard that `results_complete` applies to the same field at
  `routes.py:301-302`. A heatmap job has no `year`, so posting a heatmap
  `job_id` to `/unmatched_view` returns HTTP 500; verified against a live test
  client. No link in the app produces that request, and the 500 handler renders
  a friendly page, so the cost today is a generic error page instead of a
  specific one.

### `spotify.py`

- **DI B** -- concrete imports.
- **BSR N/A** -- no commits in the window.
- **FF C** -- two problems in one cell. `spotify.py:26-27` validates
  credentials with `assert`, which `python -O` removes, and `spotify.py:67-68`
  collapses every non-200, non-429 response into the same value a genuine
  empty result produces. See **F-SWE-3** and **F-SWE-4**.

### `utils.py`

- **SoC C** -- one module holds five unrelated concerns: rate limiting
  (`utils.py:29-121`), HTTP session construction (`:155-188`), an in-memory
  response cache (`:192-242`), duration formatting for display (`:245-283`)
  and a generic async retry loop (`:286-346`). See **F-SWE-7**.
- **SRP B** -- the module mixes concerns, but each individual function does one
  job and does it clearly.
- **DI B** -- `_LASTFM_THROTTLE` and `_SPOTIFY_THROTTLE` are constructed at
  import (`utils.py:81-82`).
- **CoI A** -- `_ThrottledLimiter` (`utils.py:59-78`) wraps a throttle and a
  limiter instead of subclassing `AsyncLimiter`. This is the cleanest single
  design decision in the audited code, and the reason the per-loop limiter
  problem stayed solvable.
- **BSR N/A** -- no commits in the window.
- **LoD B** -- `get_cached_response` returns a live reference into the cache
  (`utils.py:200-212`). The docstring says so, and no current caller mutates
  it.
- **FF B** -- `retry_with_semaphore` swallows every exception outside the
  `reraise` tuple (`utils.py:340-341`). The behaviour is a parameter, and
  `lastfm.py:142` uses it to let `ValueError` through.

### `worker.py`

42 lines, one concern, and the resource protocol is correct:
`start_job_thread` releases the slot and re-raises so the caller can react
without leaking (`worker.py:37-42`).

- **DI B** -- imports `MAX_ACTIVE_JOBS` concretely to size the semaphore.
- **CoI N/A** -- no classes.
- **BSR N/A** -- no commits in the window.

## Broad catches: is each one justified?

F-MAS-4 counts these. The charter asks whether each is earned. All 17 were
read in context. **Fifteen are justified. Two are not.**

| Location | Verdict |
|---|---|
| `cache.py:51` | Justified -- connection retry, logged, degrades to `None`. |
| `cache.py:126` | Justified -- cleanup is explicitly non-fatal. |
| `heatmap.py:218` | **Not justified** -- relabels every error as a Last.fm outage. F-SWE-5. |
| `lastfm.py:66` | Justified -- fail-open user check, commented at the site. |
| `lastfm.py:126` | Justified -- malformed JSON, logs the body prefix. |
| `orchestrator.py:546` | Justified -- DB lookup failure, records a job stat. |
| `orchestrator.py:599` | Justified -- DB persist failure, records a job stat. |
| `orchestrator.py:851` | Justified -- top-level handler that classifies before reporting. |
| `orchestrator.py:912` | **Not justified** -- logs only, leaves the job non-terminal. F-SWE-5. |
| `routes.py:156` | Justified -- returns 503. |
| `routes.py:453` | Justified -- optional check, proceeds and logs. |
| `routes.py:496` | Justified -- deletes the orphaned job, renders an error. |
| `routes.py:542` | Justified -- returns 503. |
| `routes.py:586` | Justified -- deletes the orphaned job, returns 500. |
| `utils.py:138` | Justified -- captures for the caller, which re-raises. |
| `utils.py:340` | Justified -- the retry loop's purpose, with `reraise` as the escape. |
| `worker.py:40` | Justified -- releases the slot and re-raises. |

The pattern is worth recording. Every catch that classifies the failure before
reporting it is sound, and both unjustified catches are the ones that report a
cause they never established.

## Test vacuity

`AGENT_NOTES.md` requires that every test fail if the function under test is
deleted. The charter makes any test that survives such a deletion a net-new
finding.

This was measured, not judged. A copy of the tree was made outside the
repository. Each top-level function in the 13 graded modules was replaced in
turn with `raise AssertionError("DELETED")`, and the 237 runtime tests were run
against each mutation.

**81 functions mutated. 0 deletions went unnoticed.**

No net-new vacuity finding. The audited worktree was untouched by this
procedure and verified clean afterwards.

One process note for whoever repeats this. A first run was killed by a timeout
and left one module mutated on disk, which silently shifted the line numbers
reported for the next module. That module was re-run from a verified-clean
copy. Compare each mutated file against the repository before trusting a
result.

## Two summary questions

### Which principle is weakest across the audited runtime modules?

**Fail Fast**, and not narrowly. It holds five of the eight C grades and earns
only two A grades across 13 modules, the worst ratio of any principle. Every
other principle is either broadly upheld or fails in one module for one
recorded reason.

The failures share a shape. The code is careful about catching problems and
careless about preserving what the problem was. A Spotify server error becomes
the same `None` as "no such album" (F-SWE-3). Any heatmap failure becomes
"Last.fm is currently unavailable" (F-SWE-5). A missing API key becomes a
per-request failure hours after a startup check would have caught it
(F-SWE-4). In each case the information needed to report the truth existed at
the point of the catch and was discarded there.

**The single change that would most improve it:** make a transient upstream
failure distinguishable from a terminal negative result, and route both
through the `ERROR_CODES` table in `errors.py` that already exists for exactly
this purpose. Concretely, give the `retry_with_semaphore` callers a third state
besides "done" and "retry after N seconds", and have each background entry
point report the code that matches what actually failed. That one change
addresses three of the five Fail Fast C cells.

The cheapest single change is a different one and worth doing regardless: call
`ensure_api_keys()` from `create_app()`. One line closes two C cells.

### Has code quality drifted, held, or improved since the 2026-02 audits?

**Held on the old problems; improved on everything new.** Three independent
lines of evidence point the same way.

*The February findings are all still open, and none has worsened.* The four
runtime items in AUDIT_2026-02-27 -- the oversized orchestrator, the global
`JOBS` state, `app.py` import-time side effects, and the broad catches -- are
each still present and each still tracked (F-B20-2, F-MAS-5, the un-numbered
`app.py` item, F-MAS-4). `orchestrator.py` measured about 906 lines in February
and 916 now: ten lines of drift over six months, against a module that gained
no new responsibility. That is a stable defect, not a growing one.

*Code written since February grades better than code written before it.*
`heatmap.py`, `worker.py` and `errors.py` all post-date the February sweep.
`errors.py` and `worker.py` are the two cleanest modules in this matrix, and
`heatmap.py` carries one C. The newest code is also the best documented: the
`heatmap.py` module docstring states its own dependency chain, and
`config.py:22-30` explains a constant by citing the load test that set it.

*Test discipline improved measurably, not just by reputation.*
TEST_QUALITY_AUDIT_2026-02-21 found and repaired five vacuous tests. The
mutation run above found zero across 81 functions. The suite grew from 576
passing at the 2026-08-11 synthesis to 590 now, and the F-B19-6 fix shipped
with a named regression test that still pins the behaviour it protects.

This reckons with REPOSITORY_SYNTHESIS_2026-08-11 rather than treating February
as the last word. That synthesis recorded six live discrepancies in its
Section 3; all six were remediated within three days, and its own status note
says so. Its Section 7 structural risks remain accurate and remain open, which
is consistent with the reading above: the known structural debt is stable and
tracked, while the delivery process around it has tightened.

One qualification. F-SWE-2 is a bug that was fixed in one module in February
and left standing in its twin, and nothing caught that for six months. The
February-era defects are not growing, but neither is anyone sweeping for
siblings when one instance gets fixed.

## Net-new findings

Six, written into `FINDINGS.md` as `F-SWE-N` entries with
`Source: SWE_PRINCIPLES_AUDIT`.

| ID | Module | Severity | Effect on WP-1 |
|---|---|---|---|
| **F-SWE-2** | `orchestrator.py` | P1 | **Blocks.** Correctness defect in a module WP-7 modifies. |
| **F-SWE-3** | `spotify.py` | P1 | Record and continue -- module untouched by Batch 21. |
| **F-SWE-4** | `app.py`, `config.py` | P1 | Record and continue -- modules untouched. |
| **F-SWE-5** | `heatmap.py`, `orchestrator.py` | P1 | Record and continue -- see the note below. |
| **F-SWE-6** | `repositories.py` | P2 | Record and continue. |
| **F-SWE-7** | `utils.py` | P2 | Backlog. |

Two of these needed a judgment call about where the defect lives. Both calls
are stated here so the owner can overrule either one.

**F-SWE-3** is filed against `spotify.py`, not `orchestrator.py`. The user sees
the wrong label at `orchestrator.py:253-262`, which WP-7 modifies, but
`orchestrator.py` behaves correctly given what it receives: the distinction is
already gone by then, discarded at `spotify.py:67-68`. Filing it against the
module that loses the information keeps the gate honest. Reading it the other
way would make it blocking.

**F-SWE-5** spans `heatmap.py` and `orchestrator.py`, and `orchestrator.py` is
a WP-7 module. It is filed as record-and-continue because the
`orchestrator.py` half needs the inner handler at `orchestrator.py:851` to fail
first, which nothing observed can cause. The `heatmap.py` half is the reachable
one, and `heatmap.py` is untouched by the batch. If the owner reads the
orchestrator half as independently reachable, this finding blocks too.

### F-SWE-2: the album year window is built from naive datetimes

`orchestrator.py:70-71` builds the Last.fm fetch window with naive
`datetime(year, 1, 1)` and `datetime(year, 12, 31, 23, 59, 59)`. Calling
`.timestamp()` on a naive datetime applies the host's local zone, so the window
shifts by the host's UTC offset. The same timestamps are reused at
`orchestrator.py:100` to filter individual scrobbles, so the shift is applied
twice.

Measured on the development host, which runs UTC-5:

```
orchestrator from_ts : 1704085200 -> 2024-01-01 05:00:00+00:00 UTC
UTC-correct  from_ts : 1704067200 -> 2024-01-01 00:00:00+00:00 UTC
window start skew    : +18000 seconds (+5.0 hours)
```

Five hours of scrobbles are attributed to the wrong year at each boundary.

This is the defect F-B19-6 fixed in `heatmap.py`. `git show --stat ccb000f`
confirms that fix touched `scrobblescope/heatmap.py` and `tests/test_heatmap.py`
and nothing else. `heatmap.py:116-122` has used explicit UTC ever since;
`orchestrator.py` was never revisited. `AGENTS.md` anti-pattern 6 has since
registered the naive-timezone pattern repository-wide, citing the heatmap
regression test as the canonical example.

Production is unaffected today. The Fly.io container runs UTC, so the offset is
zero there. Every non-UTC host is affected, which includes the owner's Windows
development machine, so local verification of album results has been running
against a shifted window.

Fix: add `tzinfo=timezone.utc` to both constructors and pin it with a test
modelled on `test_utc_decode_invariant_against_local_tz_drift`.

**Case for a waiver:** no live user is affected, WP-7 opens this file anyway,
and the change is two lines. **Case against:** the two lines are smaller than
the paperwork, `orchestrator.py` is about to be edited by an agent that will
read the surrounding code as correct, and the last time this bug was
half-fixed it survived six months.

## Charter compliance

- 130 of 130 cells filled. No module dropped, no coverage cut.
- Single session. Charter Section 8's split provision was not needed.
- Read-only. No production code was changed. The mutation testing ran on a copy
  outside the repository; the audited worktree was verified clean before and
  after.
- Baseline honoured. F-B20-2, F-B18-7, F-MAS-4, F-MAS-5, F-DATA-1, F-B21-1 and
  the AUDIT_2026-02-27 `app.py` item were each recognised and cited rather than
  re-reported. The deliberate declines in ROUTES_SOC_AUDIT Section 4 and in the
  `AGENT_NOTES.md` architectural constraints were respected.
- F-B21-1 keeps its recorded P1 disposition. This audit does not re-triage it,
  and it does not block WP-1.
