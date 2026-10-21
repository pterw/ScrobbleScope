# Last.fm scrobbles and one album aggregate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hand the album and heatmap pipelines normalized listening records (`Play`) instead of raw Last.fm pages, give the album calculation one typed answer and one publish step that a Spotify export can reuse, make the cross-module private names public, and take every Last.fm username out of the logs.

**Architecture:** Five tasks on `refactor/lastfm-scrobbles`, each its own atomic commit. Task 1 (23a) pins today's job results through the Last.fm HTTP edge so the same tests run unchanged before and after the refactor. Task 2 removes usernames from logs. Task 3 (23b) renames the private names that cross modules and adds a guard test. Task 4 (23c) adds the leaf module `scrobblescope/plays.py` and `lastfm.fetch_scrobbles`. Task 5 (23d) adds `AlbumSelection`, `select_albums` and `finish_album_job`, the one publish step. The design is `.superpowers/sdd/2026-09-29-pr245-fixes/task-23-design.md` (checked against `C:/ssw/kb`, see "Assumptions checked"); the tranche order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` (PR #4).

**Tasks 2-5 assume PR #3 (the album request module) has merged.** They are written against #3's approved plan (`.superpowers/sdd/2026-10-20-album-request-module/plan-draft.md`), not against 5dde407, wherever the two differ: the thread entry points take a job id alone, the Last.fm pre-check lives in `routes/precheck.py`, and the album request is one `AlbumRequest` object. Task 1 does not depend on #3 and lands first; one line of it changes when #3 merges. "Dependence on PR #3" lists every call site.

**Tech Stack:** Python 3.13, asyncio/aiohttp, Flask, pytest with pytest-asyncio, ruff, pre-commit, docsync (`scripts/doc_state_sync.py`), Mermaid diagrams under `docs/architecture/`.

## Global Constraints

- Every commit is atomic and carries its own untagged PLAYBOOK Section 4 entry, placed directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` line (AGENTS.md "Side-Task Handling"). The entry heading is `### <ISO date of the commit> - <title given in the task>`; the body gives the scope, the owner intent, what changed, deviations, the mutation evidence and `Validation: pytest -q -- **N passed**` (xfailed tests are not counted in N).
- Commit procedure, every commit, in this order (AGENTS.md "Commit Rules"): write the Section 4 entry; `pytest -q` and measure N; `doc_state_sync.py --fix --test-count N` (bare `--fix` when N is unchanged); stage by name, never `git add -A` or `git add .`; `pre-commit run --all-files` and re-stage anything a hook rewrote; `doc_state_sync.py --check` exits 0; commit.
- Commit subject `<type>(<scope>): <Capitalised imperative>`, at most 72 characters (each task gives its subject, measured); body explains why and, in Tasks 3-5, names every existing test file or test it edited (owner ruling 2026-09-29, recorded in `BATCH23_DEFINITION.md`: a WP-0 seam refactor commit may edit existing tests). No `Co-authored-by` trailer.
- From the linked worktree `C:/ssw/lfs`, every Python command uses the primary checkout's interpreter. In every command below, `PY`, `RUFF` and `PRECOMMIT` are shell variables; set them once per shell:
  `PY="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"`, `RUFF="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/ruff.exe"`, `PRECOMMIT="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe"`. Always quote them: `"$PY" -m pytest ...`.
- Markdown is ASCII only (`--`, never an em dash). Cite code by name, not line number.
- New tests assert intended behaviour, not the code as written (owner, 2026-10-20), and each comes with mutation evidence: the planted defect named and the test shown failing. A test that pins a behaviour an owner ruling is about to change asserts the ruled behaviour and carries `xfail(strict=True)` until the commit that changes it removes the marker.
- A refactor starts from parity tests in a preceding commit (AGENTS.md "Refactor requires parity tests"): Task 1 precedes Tasks 3-5.
- Use the Python 3.13 spellings the hygiene PR (#2) establishes: `from datetime import UTC` and `datetime.now(UTC)`, never `timezone.utc`, in every line this plan adds.
- Log lines name a job id, an exception class, counts and elapsed time. They never carry a Last.fm username (nor a request-cache key, which embeds one), or an artist, album or track name (F-B23-40; `BATCH23_DEFINITION.md` "Data handling").
- Hosting cost ceiling (spec): nothing here keeps the production database awake, adds a machine or adds a service. This PR adds no database traffic; Task 4 measures the extra memory the normalized records hold.
- This PR changes no template, stylesheet or script. The Mermaid blocks it edits are checked in Task 3 and Task 4 with the Mermaid validator the controller has (the `validate_and_render_mermaid_diagram` tool) before the commit.
- `WT003 refactor/lastfm-scrobbles` and `WT010` are expected advisories from the `worktree-alignment` hook; the hook still passes.
- Do not push. The controller pushes after the one whole-PR review the spec's review policy requires for this PR (five commits deep) and opens the PR.
- Branch and merge order (tranche master plan): this plan is committed first on the branch. Task 1 branches from `main` after PR #256 and PR #2 merge. Tasks 2-5 are written for `main` after PR #3 (the album request module) merges, and may not be started before it has.
- Scope of the `BATCH23_DEFINITION.md` amendments: the tranche spec's documentation rule says "When a seam changes what a Batch 23 work package may assume, the same PR amends `BATCH23_DEFINITION.md`" (and names #4 for WP-2's record). So this PR amends WP-2 (Task 4 Step 13: the record, the one aggregator, the daily counts) and the WP-3 text that Tasks 4-5 make untrue (Task 5 Step 10: WP-3's first bullet, which describes the partition and publish steps the export job now reuses, and the start of its acceptance, which names `fetch_all_recent_tracks_async`; also WP-2's acceptance sentence about `partition_albums_by_threshold`). WP-6's sentence about original track names is untouched: PR #6 amends WP-6. Dated plans, including the unexecuted Spotify-export plan, stay as history and are not annotated.

---

## Assumptions checked against `C:/ssw/kb` (5dde407)

The design predates PR #245. Each assumption in its section 1 table, and the other claims this plan relies on, was looked up in `C:/ssw/kb`.

| Assumption | Held? | What `C:/ssw/kb` shows | Effect on this plan |
|---|---|---|---|
| A22-1: a job module with phase, stat, unmatched, succeed, fail | Held | `scrobblescope/jobs.py`: `advance`, `report_phase(job_id, phase, done, total, message)`, `record_stat`, `record_partial_source(job_id, source)` (new since the design), `record_unmatched(job_id, key, payload)`, `succeed(job_id, results, message)`, `fail(job_id, error_code, username=None, retry_after=None)`, `progress`, `context`, `unmatched` | Code below uses these names |
| A22-2: `succeed` stores results and 100% in one write | Held | `jobs.succeed` applies both in one `_write` and clears the phase | The "no album passes" terminal is one `jobs.succeed(job_id, [], message)` |
| A22-3: both progress callbacks take three ints | Held | `fetch_all_recent_tracks_async` calls `progress_cb(done, total, received)`; no `_notify_progress_cb` | `fetch_scrobbles` forwards the callback untouched |
| A22-4: tests read job state through a public read API | Held, renamed | `get_job_context` is now `jobs.context` and `jobs.progress` | Tests below use them |
| A18-1: typed provider failures exist | Held, different shape | `errors.py`: `ClassifiedError`, `UserNotFoundError`, `PrivateProfileError`, `ProviderError(source, kind)` whose code `lastfm_unavailable` is in `ERROR_CODES`, and `classify_exception_to_error_code` | `fetch_scrobbles` raises `ProviderError("lastfm", "unavailable")`; nothing new in `errors.py` |
| A18-2: exhausting retries on page 1 raises the typed failure | Did NOT hold | `fetch_all_recent_tracks_async` still returns `([], {"status": "error", "reason": "lastfm_unavailable"})` | The conversion to `ProviderError` is added in `fetch_scrobbles` (Task 4) |
| A18-3: the page layer raises typed not-found and private failures | Held | `fetch_recent_tracks_page_async` raises `UserNotFoundError` (404) and `PrivateProfileError` (error 17) and passes both as `reraise` | Page layer unchanged |
| A18-4: the two `return []` after a Spotify failure may become exceptions | Not done | `_process_filtered_albums` still calls `jobs.fail("spotify_unavailable")` and returns `[]` | Out of scope; left as is |
| Design section 6: the cancel-and-drain helper moves to a public home | Already done | `utils.cancel_and_drain` is public, used by `lastfm.py`, `spotify.py` and the orchestrator phases; `tests/test_utils.py` has two direct tests | Dropped from Task 3 |
| Design sections 7-8: the private names crossing modules | Held, re-measured | An `ast` walk of 5dde407 finds exactly these cross-package private reads: `release_checks` imports `cache._get_db_connection`, `_batch_lookup_original_release`, `_batch_persist_original_release` and `domain._matches_release_criteria`; `orchestrator/__init__` imports `cache._batch_lookup_metadata`, `_batch_lookup_original_release`, `_batch_persist_metadata`, `_cleanup_stale_metadata`, `_get_db_connection`; `orchestrator/_results.py` imports `domain._matches_release_criteria`; `orchestrator/_cache.py` reads the same cache names through `_orchestrator`; `routes/api.py` takes `CHECK_UNCHECKED` and `STATUS_PENDING` from the thread-owning `release_checks` | Task 3 renames exactly these |
| Design 4.3: two log lines echo response text | Obsolete | Task 25 already changed both to size and content type only | Not in this plan |
| Design 4.3: usernames in two `lastfm.py` lines | Held, and more were found | An `ast` walk finds eleven lines in five files at 5dde407: `lastfm.py` (two), `heatmap.py` (fetch timing, "ready" with the scrobble total, `_report_heatmap_failure`), `orchestrator/__init__.py` (a DEBUG line, `_fetch_and_process`, `_report_album_failure`), `routes/heatmap_flow.py` (two) and `routes/album_flow.py` (the registration-year warning). A twelfth carrier is invisible to the walk: `utils.get_cached_response` logs the cache key, which embeds `user:<name>`. PR #3 removes three of the eleven (the two route pre-check lines move into class-only `routes/precheck.py`; the registration-year warning goes with the old fallback) | Task 2 fixes the nine that remain, in four files |
| Design: 13 `fetch_top_albums_async` patch sites in `test_orchestrator_fetch_and_process.py` | Drifted | 17 lines name it; 9 tests in `test_lastfm_logic.py` patch `orchestrator.fetch_all_recent_tracks_async`; 8 in `test_heatmap.py` patch `heatmap.fetch_all_recent_tracks_async`; one each in `test_pipeline_integration.py` and `test_provider_fixtures.py` | Tasks 4 and 5 edit those, counted |
| Design: `_process_filtered_albums` takes nine parameters | Drifted | It takes ten: PR #256 added `include_unmatched` | `finish_album_job` carries `include_unmatched` through |
| Design: `_record_lastfm_stats` records stats and a warning | Held, extended | It also writes `partial_data_sources` through `jobs.record_partial_source`, pinned by `test_lastfm_page_loss_is_recorded_as_a_kind_beside_its_sentence` | Task 5 replaces that test and keeps the behaviour |
| Owner rulings of 2026-09-29: seam commits may edit tests; the now-playing entry leaves `total_scrobbles` | Held | `BATCH23_DEFINITION.md` Intended outcome and Batch acceptance already carry the test ruling; the now-playing ruling is in `task-23-brief.md` | Task 4 flips the count; no definition change for the test ruling |
| `loading.js` and `results.html` read the stats | Held | `loading.js` reveals `stats.total_scrobbles`, `stats.pages_fetched`, `stats.albums_passing_filter`; `results.html` sums `play_count`, which never included the now-playing entry | Stat names are unchanged |
| Hygiene PR #2 respells `timezone.utc` | New fact | Ruff `target-version = "py313"` rewrites it to `datetime.UTC` | All new code here uses `UTC` |

## Dependence on PR #3 (album request module)

Tasks 2-5 assume PR #3 has merged. What #3's approved plan changes, and what it leaves alone, as far as this plan is concerned:

- **Thread entry points take a job id alone.** `orchestrator.background_task(job_id)` and `heatmap.heatmap_task(job_id)` read their parameters from the job record (`jobs.params(job_id)`; the album one through `AlbumRequest.from_params`). Admission stores the record. So a test that reaches a log line through a thread entry point must create a job record that carries the value under test (here the username).
- **Unchanged by #3:** `_fetch_and_process(job_id, username, year, sort_mode, release_scope, decade, release_year, min_plays, min_tracks, limit_results, include_unmatched=...)` keeps today's positional order; `_report_album_failure(job_id, username, year)` and `_report_heatmap_failure(job_id, username, exc)` keep their signatures; `_fetch_and_process_heatmap(job_id, username)` is unchanged. Every test that calls one of these directly needs no edit.
- **New route module.** `routes/precheck.py` answers the album, heatmap and validate routes from one Last.fm lookup and logs the exception class only, with its own username-absent test. The two heatmap pre-check lines and the album route's registration-year warning leave the tree (three of the eleven lines F-B23-40 named).
- **Job records.** `TEST_JOB_PARAMS` (username `testuser`, year 2025) gains `"mode": "album"`; a heatmap job record is `{"username": ..., "mode": "heatmap"}`.
- **`AlbumRequest`** (`scrobblescope/album_request.py`) is a frozen object of ten fields: `username` (`None` for a request with no Last.fm user, which is the export job's case), `year`, `sort_mode`, `include_unmatched`, `release_scope`, `decade`, `release_year`, `min_plays`, `min_tracks`, `limit_results`. `parse_album_request(form, *, current_year, require_username=True)` builds one; with `require_username=False` the username is `None`.

| Task | What changes after #3, and the edit |
|---|---|
| 1 (23a) | Written for `main` before #3. `_run_album_job` calls `_fetch_and_process`, whose signature #3 leaves alone: no edit. `_run_heatmap_task` calls `heatmap_task(job_id, "parity_user")`: after #3 it is `heatmap_task(job_id)` (the job it creates already carries the username and `"mode": "heatmap"`). That is the one line, used by `test_an_unusable_first_page_ends_the_heatmap_as_lastfm_unavailable` and `test_a_user_not_found_on_a_later_page_ends_the_heatmap_as_user_not_found`. Task 1 is committed before #3 merges, so Task 2 makes the edit (its Step 1b). No assertion changes. |
| 2 (logs) | Written for the post-#3 tree. Eight username lines in three files plus the cache-hit line in `utils.py` (nine, four files). The route lines and the registration-year warning are #3's and are not in the table or the tests. `heatmap_task(job_id)` and `background_task(job_id)` are called with the id alone, from a job record that carries `LISTENER` (`jobs.create({"username": LISTENER, "mode": "heatmap"})`; `jobs.create({**TEST_JOB_PARAMS, "username": LISTENER})`), and each test asserts the record holds the name first, so the test cannot pass because the name never reached the code. |
| 3 (23b) | No semantic dependency: import lines and names. A textual rebase only; re-run the guard test, which lists any private read #3 introduced. |
| 4 (23c) | `test_lastfm_outage_crash_publishes_lastfm_unavailable` calls `heatmap_task(job_id)` on a heatmap job record, not `heatmap_task(job_id, "user")`. The tests that call `_fetch_and_process(job_id, "user", 2025, "playcount", "all")` keep that positional form; this task edits only what they patch. `_fetch_job_albums` is still called from `_fetch_and_process` as #3 left it. |
| 5 (23d) | `finish_album_job(job_id, selection, album, *, overall_start_time)` takes #3's `AlbumRequest` as one parameter (decision below). `_fetch_and_process` builds one from its positional parameters before the call. |

**Decision for Task 5.** `finish_album_job` takes the `AlbumRequest`, not seven keywords. Reasons: it is the shape #3 made for exactly this second caller (`username` is `None` for an export, which is the WP-3 use, and `parse_album_request(..., require_username=False)` already builds it); seven keywords would be a second copy of the request's field list that drifts the day a field is added; the minimums in the object (`min_plays`, `min_tracks`) are applied by `select_albums` before the call and `finish_album_job` ignores them. The WP-3 text that follows is in Task 5 Step 10.

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `tests/helpers.py` (modify) | `FakeLastfm`, `lastfm_edge`, `lastfm_page`, `lastfm_track`, `lastfm_now_playing`; later `lastfm_albums` | 1, 5 |
| `tests/test_lastfm_job_results.py` (create) | Job results through the Last.fm HTTP edge, both pipelines | 1 (markers removed in 4) |
| `tests/test_log_privacy.py` (create) | No username in any log record, the request-cache hit line included | 2 |
| `scrobblescope/utils.py` (modify) | `get_cached_response`'s hit line stops writing the cache key | 2 |
| `scrobblescope/api_logging.py` (modify) | `RedactingFormatter` docstring stops listing that line as a carrier | 2 |
| `tests/services/test_failure_logging.py` (modify) | `_assert_type_only_at_error` can also assert a username is absent | 2 |
| `scrobblescope/release_status.py` (create) | The eight release-check wire strings, a leaf | 3 |
| `tests/test_module_boundaries.py` (create) | AST guard: no private cross-module reads; wire strings pinned; page layer private | 3, 4 |
| `scrobblescope/plays.py` (create) | `Play`, `Window`, `AlbumTally`, `AlbumAggregate`, `aggregate_albums`, `aggregate_daily_counts`, `zero_fill_daily_counts`; later `AlbumSelection`, `select_albums`. Imports `domain` and `unmatched` only | 4, 5 |
| `tests/test_plays.py` (create) | The pure calculations | 4, 5 |
| `scrobblescope/lastfm.py` (modify) | `FetchSummary`, `ScrobbleFetch`, `fetch_scrobbles`; pages stay inside | 2, 4 |
| `scrobblescope/heatmap.py` (modify) | Consumes plays; loses `_aggregate_daily_counts` and `_zero_fill_daily_counts` | 2, 4 |
| `scrobblescope/orchestrator/__init__.py` (modify) | `fetch_top_albums_async`, `finish_album_job(job_id, selection, album, ...)`; loses `_fetch_job_albums`, `_record_lastfm_stats`, `_cap_threshold_exclusions` | 2-5 |
| `tests/services/test_finish_album_job.py` (create) | The publish step | 5 |
| `docs/architecture/*.md`, `.claude/SESSION_CONTEXT.md`, `BATCH23_DEFINITION.md`, `docs/agents/FINDINGS.md`, `docs/agents/PLAYBOOK.md` | Follow the code in the same commit | each |

---

### Task 1: Pin Last.fm-derived job results (23a)

**Touches:** `tests/helpers.py`, `tests/test_lastfm_job_results.py` (new), `docs/agents/PLAYBOOK.md`.
**After:** none (branch from `main` after PR #256 and PR #2 merge).

**Files:**
- Modify: `tests/helpers.py` (imports, then new helpers at the end)
- Create: `tests/test_lastfm_job_results.py`
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry)

**Interfaces:**
- Consumes: `orchestrator._fetch_and_process`, `heatmap._fetch_and_process_heatmap`, `heatmap.heatmap_task`, `jobs.create/progress/context/unmatched`, and the real `lastfm.fetch_all_recent_tracks_async` and `fetch_recent_tracks_page_async`.
- Produces: `tests.helpers.FakeLastfm`, `lastfm_edge`, `lastfm_page`, `lastfm_track`, `lastfm_now_playing` -- Tasks 2 and 4 reuse them. The tests patch only the network edge (`lastfm.create_optimized_session`, the limiter, the cache, `asyncio.sleep`), so they run unchanged against Tasks 4 and 5. Five tests assert behaviour that Task 4 changes (owner rulings of 2026-09-29 and the design's section 3.4); they carry `xfail(strict=True)` and Task 4 removes the markers.

Why: AGENTS.md "Refactor requires parity tests". Today the aggregation is covered only by tests that hand `fetch_top_albums_async` already-fetched pages, a seam Task 4 removes. These tests sit below both pipelines, at the HTTP edge, so one suite proves the refactor.

- [ ] **Step 1: Add the Last.fm edge helpers**

At the top of `tests/helpers.py` replace the first line (`from unittest.mock import AsyncMock`) with:

```python
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch
```

Append at the end of the file:

```python
# ---------------------------------------------------------------------------
# The Last.fm HTTP edge, for tests that run a whole pipeline
# ---------------------------------------------------------------------------


class FakeLastfm:
    """Scripted Last.fm answers, one per page number.

    ``pages`` maps a page number to the JSON body served for it with HTTP 200.
    ``statuses`` maps a page number to a non-200 status, which wins over a
    body. A page named in neither answers HTTP 500, as an outage would. The
    page numbers asked for are kept in ``requested``.
    """

    def __init__(self, pages, statuses=None):
        self.pages = pages
        self.statuses = statuses or {}
        self.requested = []

    def get(self, url, params=None, **kwargs):
        """Answer one ``session.get`` the way the page layer reads it."""
        page = params["page"]
        self.requested.append(page)
        resp = AsyncMock()
        resp.status = self.statuses.get(page, 200 if page in self.pages else 500)
        resp.json = AsyncMock(return_value=self.pages.get(page))
        resp.text = AsyncMock(return_value="")
        resp.content_type = "application/json"
        resp.headers = {}
        return make_response_context(resp)


@contextlib.contextmanager
def lastfm_edge(fake):
    """Route every Last.fm request to ``fake``; nothing else is patched.

    The session, the rate limiter, the request cache and ``asyncio.sleep`` (the
    retry back-off) are the network edge; the page layer, the pagination and
    everything above them run for real.
    """
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=fake)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    with (
        patch(
            "scrobblescope.lastfm.create_optimized_session", return_value=session_cm
        ),
        patch(
            "scrobblescope.lastfm.get_lastfm_limiter", return_value=NoopAsyncContext()
        ),
        patch("scrobblescope.lastfm.get_cached_response", return_value=None),
        patch("scrobblescope.lastfm.set_cached_response"),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        yield fake


def lastfm_page(tracks, number=1, total=1):
    """One ``user.getrecenttracks`` page; ``tracks`` is served exactly as given."""
    return {
        "recenttracks": {
            "@attr": {"page": str(number), "totalPages": str(total)},
            "track": tracks,
        }
    }


def lastfm_track(artist, album, name, when):
    """One dated scrobble; ``when`` is a tz-aware ``datetime``."""
    return {
        "artist": {"#text": artist},
        "album": {"#text": album},
        "name": name,
        "date": {"uts": str(int(when.timestamp()))},
    }


def lastfm_now_playing(artist, album, name):
    """The entry Last.fm adds for a track playing now: no ``date`` field."""
    return {
        "artist": {"#text": artist},
        "album": {"#text": album},
        "name": name,
        "@attr": {"nowplaying": "true"},
    }
```

- [ ] **Step 2: Write the parity tests**

Create `tests/test_lastfm_job_results.py`:

```python
"""Last.fm in, job results out: both pipelines pinned at their one stable seam.

Every test fakes only the Last.fm HTTP edge (``tests.helpers.lastfm_edge``) and
reads the answer from the job the pipeline publishes. Nothing here imports a
function that sits between the page layer and the job, so the suite means the
same thing before and after the scrobbles-not-pages refactor (Batch 23 WP-0,
Task 23). Five tests assert a behaviour the refactor changes by owner ruling
(2026-09-29) and are marked ``xfail(strict=True)``; the refactor's commit
removes each marker.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.domain import normalize_name, normalize_track_name
from scrobblescope.heatmap import _fetch_and_process_heatmap, heatmap_task
from scrobblescope.orchestrator import _fetch_and_process
from tests.helpers import (
    TEST_JOB_PARAMS,
    FakeLastfm,
    lastfm_edge,
    lastfm_now_playing,
    lastfm_page,
    lastfm_track,
)

YEAR = 2023


def _at(month, day, hour=12, minute=0, second=0, year=YEAR):
    """A UTC moment inside (by default) the year the album job asks for."""
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


def _album_plays(artist, album, titles, each, day=15):
    """``each`` scrobbles of every title, on June ``day`` 2023, at distinct seconds."""
    sequence = [title for title in titles for _ in range(each)]
    return [
        lastfm_track(artist, album, title, _at(6, day, minute=n // 60, second=n % 60))
        for n, title in enumerate(sequence)
    ]


async def _run_album_job(fake, *, min_plays=10, min_tracks=3, year=YEAR):
    """Run the album pipeline up to enrichment and return what it published.

    ``process_albums`` (Spotify, Deezer and the cache) is replaced by a mock
    that records the albums it was handed. PR #3 (the album request module)
    leaves ``_fetch_and_process``'s signature alone, so this helper needs no
    edit when it merges.
    """
    job_id = jobs.create({**TEST_JOB_PARAMS, "year": year})
    process = AsyncMock(return_value=[])
    with (
        lastfm_edge(fake),
        patch("scrobblescope.orchestrator.process_albums", process),
        patch("scrobblescope.orchestrator.enqueue_release_check") as enqueue,
    ):
        await _fetch_and_process(
            job_id,
            "parity_user",
            year,
            "playcount",
            "all",
            min_plays=min_plays,
            min_tracks=min_tracks,
        )
    return job_id, process, enqueue


def _handed_to_enrichment(process):
    """The eligible albums ``process_albums`` was awaited with (exactly once)."""
    process.assert_awaited_once()
    return process.await_args.args[1]


# ---------------------------------------------------------------------------
# Album pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_album_counts_come_from_the_scrobbles_on_every_page():
    """
    GIVEN one album scrobbled across two pages
    WHEN the album job runs
    THEN the album carries every scrobble from both pages, its distinct tracks
    and the names as Last.fm spelled them, and the job stats agree.

    Planted defect: aggregate only the first page.
    """
    titles = ["Paranoid Android", "Karma Police", "Airbag", "Exit Music"]
    first = _album_plays("Radiohead", "OK Computer", titles, 4)
    second = _album_plays("Radiohead", "OK Computer", titles[:1], 2, day=16)
    fake = FakeLastfm({1: lastfm_page(first, 1, 2), 2: lastfm_page(second, 2, 2)})

    job_id, process, _ = await _run_album_job(fake)

    album = _handed_to_enrichment(process)[normalize_name("Radiohead", "OK Computer")]
    assert album["play_count"] == 18
    assert dict(album["track_counts"]) == {
        normalize_track_name("Paranoid Android"): 6,
        normalize_track_name("Karma Police"): 4,
        normalize_track_name("Airbag"): 4,
        normalize_track_name("Exit Music"): 4,
    }
    assert (album["original_artist"], album["original_album"]) == (
        "Radiohead",
        "OK Computer",
    )
    stats = jobs.progress(job_id)["stats"]
    assert stats["unique_albums"] == 1
    assert stats["albums_passing_filter"] == 1
    assert stats["albums_below_threshold"] == 0
    assert stats["pages_fetched"] == 2


@pytest.mark.asyncio
async def test_a_lone_track_object_counts_as_one_scrobble():
    """
    GIVEN Last.fm serves a page's only scrobble as a bare object, not a list
    WHEN the album job runs
    THEN that scrobble is counted once.

    Planted defect: stop normalizing the lone object, so the page is refused.
    """
    lone = lastfm_track("Mitski", "Laurel Hell", "Working for the Knife", _at(6, 15))
    fake = FakeLastfm({1: lastfm_page(lone)})

    _, process, _ = await _run_album_job(fake, min_plays=1, min_tracks=1)

    album = _handed_to_enrichment(process)[normalize_name("Mitski", "Laurel Hell")]
    assert album["play_count"] == 1


@pytest.mark.asyncio
async def test_the_now_playing_entry_is_not_an_album_play():
    """
    GIVEN a now-playing entry followed by twelve completed scrobbles
    WHEN the album job runs
    THEN the album has twelve plays, not thirteen.

    Planted defect: count the entry that has no date.
    """
    tracks = [lastfm_now_playing("Artist Z", "Album Z", "Playing Now")]
    tracks += _album_plays("Artist Z", "Album Z", ["One", "Two", "Three"], 4)
    fake = FakeLastfm({1: lastfm_page(tracks)})

    _, process, _ = await _run_album_job(fake)

    album = _handed_to_enrichment(process)[normalize_name("Artist Z", "Album Z")]
    assert album["play_count"] == 12


@pytest.mark.xfail(
    strict=True,
    reason="Task 4 (23c) flips this: owner ruling 2026-09-29, the now-playing "
    "entry is not a scrobble, so it leaves total_scrobbles",
)
@pytest.mark.asyncio
async def test_the_scrobble_total_counts_completed_scrobbles_only():
    """
    GIVEN a now-playing entry followed by twelve completed scrobbles
    WHEN the album job runs
    THEN the job's scrobble total is twelve.

    Planted defect: count the entry that has no date.
    """
    tracks = [lastfm_now_playing("Artist Z", "Album Z", "Playing Now")]
    tracks += _album_plays("Artist Z", "Album Z", ["One", "Two", "Three"], 4)
    fake = FakeLastfm({1: lastfm_page(tracks)})

    job_id, _, _ = await _run_album_job(fake)

    assert jobs.progress(job_id)["stats"]["total_scrobbles"] == 12


@pytest.mark.asyncio
async def test_scrobbles_outside_the_year_are_not_counted():
    """
    GIVEN a page holding twelve scrobbles from three years earlier and twelve
    from the year asked for
    WHEN the album job runs for that year
    THEN only the album listened to in that year reaches enrichment, while the
    job's scrobble total still counts every dated entry Last.fm returned.

    Planted defects: skip the window filter; or count only the entries inside
    the window in the scrobble total.
    """
    earlier = [
        lastfm_track("Artist X", "Album X", f"t{n}", _at(6, 15, second=n, year=2020))
        for n in range(12)
    ]
    current = _album_plays("Artist Y", "Album Y", ["a", "b", "c"], 4)
    fake = FakeLastfm({1: lastfm_page(earlier + current)})

    job_id, process, _ = await _run_album_job(fake)

    assert set(_handed_to_enrichment(process)) == {
        normalize_name("Artist Y", "Album Y")
    }
    assert jobs.progress(job_id)["stats"]["total_scrobbles"] == 24


@pytest.mark.asyncio
async def test_the_year_window_includes_its_first_and_last_second():
    """
    GIVEN scrobbles at the last second before the year, its first second, its
    last second and the first second after it
    WHEN the album job runs for that year
    THEN exactly the two inside it are counted, both ends inclusive.

    Planted defect: treat the window's start as exclusive.
    """
    moments = {
        "Before": datetime(YEAR - 1, 12, 31, 23, 59, 59, tzinfo=UTC),
        "Edge Start": datetime(YEAR, 1, 1, 0, 0, 0, tzinfo=UTC),
        "Edge End": datetime(YEAR, 12, 31, 23, 59, 59, tzinfo=UTC),
        "After": datetime(YEAR + 1, 1, 1, 0, 0, 0, tzinfo=UTC),
    }
    tracks = [
        lastfm_track("Edge Artist", name, "Song", when)
        for name, when in moments.items()
    ]
    fake = FakeLastfm({1: lastfm_page(tracks)})

    _, process, _ = await _run_album_job(fake, min_plays=1, min_tracks=1)

    kept = {a["original_album"] for a in _handed_to_enrichment(process).values()}
    assert kept == {"Edge Start", "Edge End"}


@pytest.mark.asyncio
async def test_an_entry_with_no_album_artist_or_track_name_is_not_an_album_play():
    """
    GIVEN twelve scrobbles with an empty album, twelve with an empty artist and
    twelve with an empty track name, beside one real album
    WHEN the album job runs
    THEN only the real album is aggregated: an album needs all three names.

    Planted defect: drop the guard that requires all three names.
    """
    no_album = [
        lastfm_track("Someone", "", f"t{n}", _at(6, 15, second=n)) for n in range(12)
    ]
    no_artist = [
        lastfm_track("", "Orphan", f"t{n}", _at(6, 16, second=n)) for n in range(12)
    ]
    no_track = [
        lastfm_track("Someone", "Untitled", "", _at(6, 17, second=n))
        for n in range(12)
    ]
    real = _album_plays("Real Artist", "Real Album", ["a", "b", "c"], 4)
    fake = FakeLastfm({1: lastfm_page(no_album + no_artist + no_track + real)})

    _, process, _ = await _run_album_job(fake)

    assert set(_handed_to_enrichment(process)) == {
        normalize_name("Real Artist", "Real Album")
    }


@pytest.mark.xfail(
    strict=True,
    reason="Task 4 (23c) flips this: a scrobble with no album field at all is "
    "not an album play (design section 3.4, item 2)",
)
@pytest.mark.asyncio
async def test_an_entry_with_no_album_field_is_not_an_album_play():
    """
    GIVEN twelve scrobbles whose JSON has no ``album`` key at all
    WHEN the album job runs
    THEN no album is aggregated from them.

    Planted defect: invent an album named "..." for an entry that has none.
    """
    tracks = [
        {
            "artist": {"#text": "Keyless"},
            "name": f"t{n}",
            "date": {"uts": str(int(_at(6, 15, second=n).timestamp()))},
        }
        for n in range(12)
    ]
    fake = FakeLastfm({1: lastfm_page(tracks)})

    job_id, _, _ = await _run_album_job(fake)

    assert jobs.progress(job_id)["stats"]["unique_albums"] == 0


@pytest.mark.asyncio
async def test_the_first_casing_seen_names_the_album():
    """
    GIVEN one album scrobbled under two casings
    WHEN the album job runs
    THEN it is one album, and the casing of its first scrobble is its name.

    Planted defect: let the last casing seen replace the first.
    """
    tracks = [
        lastfm_track("Mitski", "Be The Cowboy", f"t{n}", _at(6, 15, second=n))
        for n in range(6)
    ] + [
        lastfm_track("MITSKI", "be the cowboy", f"u{n}", _at(6, 16, second=n))
        for n in range(6)
    ]
    fake = FakeLastfm({1: lastfm_page(tracks)})

    _, process, _ = await _run_album_job(fake)

    albums = _handed_to_enrichment(process)
    assert len(albums) == 1
    album = next(iter(albums.values()))
    assert album["play_count"] == 12
    assert (album["original_artist"], album["original_album"]) == (
        "Mitski",
        "Be The Cowboy",
    )


@pytest.mark.asyncio
async def test_a_dropped_page_makes_the_album_job_partial_and_says_so():
    """
    GIVEN a three-page fetch whose third page never answers
    WHEN the album job runs
    THEN the job still produces its albums from the two pages it read, and
    records the notice the Results page shows, the number of pages dropped and
    fetched, and that the loss came from Last.fm.

    Planted defect: forget to record that the loss came from Last.fm.
    """
    titles = ["a", "b", "c"]
    fake = FakeLastfm(
        {
            1: lastfm_page(_album_plays("Artist", "Album", titles, 3), 1, 3),
            2: lastfm_page(_album_plays("Artist", "Album", titles, 1, day=16), 2, 3),
        }
    )

    job_id, process, _ = await _run_album_job(fake)

    album = _handed_to_enrichment(process)[normalize_name("Artist", "Album")]
    assert album["play_count"] == 12
    stats = jobs.progress(job_id)["stats"]
    assert stats["partial_data_warning"] == (
        "Note: 1 of 3 Last.fm pages failed to load (33% data loss). "
        "Results may be incomplete."
    )
    assert stats["pages_dropped"] == 1
    assert stats["pages_fetched"] == 2
    assert stats["partial_data_sources"] == ["lastfm"]


@pytest.mark.asyncio
async def test_when_every_album_is_below_a_minimum_the_job_ends_with_the_report():
    """
    GIVEN two albums, one two plays short and one a track short
    WHEN the album job runs
    THEN each is recorded as a below-threshold exclusion with its shortfall,
    the job ends at 100% with the empty-result message and no error, and
    enrichment and the correction worker are never reached.

    Planted defect: leave the job running when nothing passes.
    """
    short_plays = _album_plays("Quiet Artist", "Quiet Album", ["a", "b", "c"], 3)[:8]
    short_tracks = _album_plays("Narrow Artist", "Narrow Album", ["a", "b"], 6)
    fake = FakeLastfm({1: lastfm_page(short_plays + short_tracks)})

    job_id, process, enqueue = await _run_album_job(fake)

    context = jobs.context(job_id)
    assert context["progress"]["progress"] == 100
    assert context["progress"]["error"] is False
    assert (
        context["progress"]["message"] == "No albums found for the specified criteria."
    )
    assert context["results"] == []
    quiet = context["unmatched"]["|".join(normalize_name("Quiet Artist", "Quiet Album"))]
    narrow = context["unmatched"][
        "|".join(normalize_name("Narrow Artist", "Narrow Album"))
    ]
    assert quiet["reason_code"] == "below_threshold"
    assert quiet["shortfall"] == "2 plays short"
    assert narrow["shortfall"] == "1 track short"
    stats = context["progress"]["stats"]
    assert stats["albums_below_threshold"] == 2
    assert stats["albums_passing_filter"] == 0
    process.assert_not_awaited()
    enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_an_album_exactly_at_both_minimums_is_eligible():
    """
    GIVEN an album with exactly ten plays on exactly three tracks and another
    with nine
    WHEN the album job runs with the default minimums
    THEN the first is eligible and the second is excluded: the minimums are inclusive.

    Planted defect: make the play minimum exclusive.
    """
    exact = _album_plays("Exact", "At Limit", ["a", "b", "c"], 4)[:10]
    short = _album_plays("Short", "One Short", ["a", "b", "c"], 3)
    fake = FakeLastfm({1: lastfm_page(exact + short)})

    job_id, process, _ = await _run_album_job(fake)

    assert set(_handed_to_enrichment(process)) == {normalize_name("Exact", "At Limit")}
    assert "|".join(normalize_name("Short", "One Short")) in jobs.unmatched(job_id)


@pytest.mark.asyncio
async def test_an_unusable_first_page_ends_the_album_job_as_lastfm_unavailable():
    """
    GIVEN Last.fm never answers the first page
    WHEN the album job runs
    THEN it ends in a retryable lastfm_unavailable error with no results, no
    unmatched report, no enrichment and no correction-worker hand-off.

    Planted defect: carry on as if the fetch had succeeded.
    """
    job_id, process, enqueue = await _run_album_job(FakeLastfm({}))

    context = jobs.context(job_id)
    assert context["progress"]["error"] is True
    assert context["progress"]["error_code"] == "lastfm_unavailable"
    assert context["progress"]["retryable"] is True
    assert context["results"] == []
    assert context["unmatched"] == {}
    process.assert_not_awaited()
    enqueue.assert_not_called()


@pytest.mark.xfail(
    strict=True,
    reason="Task 4 (23c) flips this: a failed fetch writes nothing before it "
    "raises (design section 3.4, item 4)",
)
@pytest.mark.asyncio
async def test_a_failed_lastfm_job_records_no_listening_stats():
    """
    GIVEN Last.fm never answers the first page
    WHEN the album job runs
    THEN the job carries no listening totals: it has nothing to report.

    Planted defect: write zeroed totals before checking the fetch.
    """
    job_id, _, _ = await _run_album_job(FakeLastfm({}))

    stats = jobs.progress(job_id)["stats"]
    assert "total_scrobbles" not in stats
    assert "unique_albums" not in stats


@pytest.mark.asyncio
async def test_a_user_not_found_on_a_later_page_ends_the_album_job_as_user_not_found():
    """
    GIVEN the first page answers and a later page is a 404
    WHEN the album job runs
    THEN the job ends as user_not_found, not as a partial run.

    Planted defect: retry a 404 like an outage and drop the page.
    """
    fake = FakeLastfm(
        {1: lastfm_page(_album_plays("Artist", "Album", ["a", "b", "c"], 4), 1, 3)},
        statuses={3: 404},
    )

    job_id, process, _ = await _run_album_job(fake)

    progress = jobs.progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "user_not_found"
    process.assert_not_awaited()


@pytest.mark.xfail(
    strict=True,
    reason="Task 4 (23c) flips this: one unreadable entry is dropped and "
    "counted, it does not fail the job (design section 3.4, item 3)",
)
@pytest.mark.asyncio
async def test_one_unreadable_timestamp_does_not_fail_the_album_job():
    """
    GIVEN twelve good scrobbles and one whose timestamp is not a number
    WHEN the album job runs
    THEN the twelve are counted and the job succeeds.

    Planted defect: let the unreadable entry raise out of the aggregation.
    """
    bad = lastfm_track("Artist", "Album", "bad", _at(6, 15))
    bad["date"]["uts"] = "not-a-number"
    tracks = _album_plays("Artist", "Album", ["a", "b", "c"], 4) + [bad]
    fake = FakeLastfm({1: lastfm_page(tracks)})

    _, process, _ = await _run_album_job(fake)

    album = _handed_to_enrichment(process)[normalize_name("Artist", "Album")]
    assert album["play_count"] == 12


# ---------------------------------------------------------------------------
# Heatmap pipeline
# ---------------------------------------------------------------------------


def _utc_noon(days_ago):
    """Noon UTC, ``days_ago`` days before today (UTC)."""
    day = datetime.now(UTC).date() - timedelta(days=days_ago)
    return datetime(day.year, day.month, day.day, 12, tzinfo=UTC)


async def _run_heatmap_job(fake):
    """Run the heatmap pipeline against ``fake`` and return its job id."""
    job_id = jobs.create({"username": "parity_user", "mode": "heatmap"})
    with lastfm_edge(fake), patch("scrobblescope.heatmap.cleanup_expired_cache"):
        await _fetch_and_process_heatmap(job_id, "parity_user")
    return job_id


def _run_heatmap_task(fake):
    """Run the heatmap thread entry point, its failure backstop included."""
    job_id = jobs.create({"username": "parity_user", "mode": "heatmap"})
    with (
        lastfm_edge(fake),
        patch("scrobblescope.heatmap.cleanup_expired_cache"),
        patch("scrobblescope.heatmap.release_job_slot"),
    ):
        heatmap_task(job_id, "parity_user")
    return job_id


@pytest.mark.asyncio
async def test_each_scrobble_is_counted_on_its_utc_day():
    """
    GIVEN two scrobbles yesterday, one today and a now-playing entry
    WHEN the heatmap job runs
    THEN the 365-day result counts them per UTC day, with the busiest day, the
    active days and the total.

    Planted defect: leave today out of the window.
    """
    yesterday, today = _utc_noon(1), _utc_noon(0)
    tracks = [
        lastfm_track("A", "B", "C", yesterday),
        lastfm_track("A", "B", "C", yesterday + timedelta(minutes=1)),
        lastfm_track("A", "B", "C", today),
        lastfm_now_playing("A", "B", "Playing Now"),
    ]

    job_id = await _run_heatmap_job(FakeLastfm({1: lastfm_page(tracks)}))

    result = jobs.context(job_id)["results"]
    assert len(result["daily_counts"]) == 365
    assert result["daily_counts"][yesterday.date().isoformat()] == 2
    assert result["daily_counts"][today.date().isoformat()] == 1
    assert (result["total_scrobbles"], result["max_count"]) == (3, 2)
    assert jobs.progress(job_id)["stats"]["active_days"] == 2


@pytest.mark.asyncio
async def test_a_scrobble_with_no_album_or_artist_still_counts_on_the_heatmap():
    """
    GIVEN a scrobble whose album and artist are empty
    WHEN the heatmap job runs
    THEN it is counted: the heatmap needs only the date.

    Planted defect: require an album name, as the album calculation does.
    """
    tracks = [lastfm_track("", "", "Untitled", _utc_noon(2))]

    job_id = await _run_heatmap_job(FakeLastfm({1: lastfm_page(tracks)}))

    assert jobs.context(job_id)["results"]["total_scrobbles"] == 1


@pytest.mark.asyncio
async def test_the_heatmap_window_is_365_days_ending_today():
    """
    GIVEN a scrobble on the window's first day and one the day before it
    WHEN the heatmap job runs
    THEN only the first is counted.

    Planted defect: start the window one day late.
    """
    first_day, before = _utc_noon(364), _utc_noon(365)
    tracks = [
        lastfm_track("A", "B", "C", first_day),
        lastfm_track("A", "B", "C", before),
    ]

    job_id = await _run_heatmap_job(FakeLastfm({1: lastfm_page(tracks)}))

    result = jobs.context(job_id)["results"]
    assert result["total_scrobbles"] == 1
    assert result["daily_counts"][first_day.date().isoformat()] == 1
    assert result["from_date"] == first_day.date().isoformat()


@pytest.mark.asyncio
async def test_a_dropped_page_makes_the_heatmap_partial_and_says_so():
    """
    GIVEN a three-page fetch whose third page never answers
    WHEN the heatmap job runs
    THEN it succeeds from the two pages read, with the heatmap's notice and the
    page counts recorded.

    Planted defect: change the notice's wording.
    """
    fake = FakeLastfm(
        {
            1: lastfm_page([lastfm_track("A", "B", "C", _utc_noon(1))], 1, 3),
            2: lastfm_page([lastfm_track("A", "B", "C", _utc_noon(2))], 2, 3),
        }
    )

    job_id = await _run_heatmap_job(fake)

    context = jobs.context(job_id)
    assert context["results"]["total_scrobbles"] == 2
    stats = context["progress"]["stats"]
    assert stats["partial_data_warning"] == (
        "Note: 1 of 3 Last.fm pages failed (33% data loss). "
        "Heatmap may be incomplete."
    )
    assert (stats["pages_expected"], stats["pages_received"]) == (3, 2)


def test_an_unusable_first_page_ends_the_heatmap_as_lastfm_unavailable():
    """
    GIVEN Last.fm never answers the first page
    WHEN the heatmap thread entry point runs
    THEN the job ends in a retryable lastfm_unavailable error with no results.

    Planted defect: report the outage as our own internal error.
    """
    job_id = _run_heatmap_task(FakeLastfm({}))

    progress = jobs.progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "lastfm_unavailable"
    assert progress["retryable"] is True
    assert jobs.context(job_id)["results"] == []


def test_a_user_not_found_on_a_later_page_ends_the_heatmap_as_user_not_found():
    """
    GIVEN the first page answers and a later page is a 404
    WHEN the heatmap thread entry point runs
    THEN the job ends as user_not_found, from Last.fm, not retryable.

    Planted defect: classify every escaped exception as internal_error.
    """
    fake = FakeLastfm(
        {1: lastfm_page([lastfm_track("A", "B", "C", _utc_noon(1))], 1, 3)},
        statuses={3: 404},
    )

    job_id = _run_heatmap_task(fake)

    progress = jobs.progress(job_id)
    assert progress["error_code"] == "user_not_found"
    assert progress["error_source"] == "lastfm"
    assert progress["retryable"] is False


@pytest.mark.xfail(
    strict=True,
    reason="Task 4 (23c) flips this: one unreadable entry is dropped and "
    "counted, it does not fail the job (design section 3.4, item 3)",
)
@pytest.mark.asyncio
async def test_one_unreadable_timestamp_does_not_fail_the_heatmap():
    """
    GIVEN a good scrobble and one whose timestamp is not a number
    WHEN the heatmap job runs
    THEN the good one is counted and the job succeeds.

    Planted defect: let the unreadable entry raise out of the aggregation.
    """
    bad = lastfm_track("A", "B", "C", _utc_noon(1))
    bad["date"]["uts"] = "not-a-number"
    tracks = [lastfm_track("A", "B", "C", _utc_noon(2)), bad]

    job_id = await _run_heatmap_job(FakeLastfm({1: lastfm_page(tracks)}))

    assert jobs.context(job_id)["results"]["total_scrobbles"] == 1
```

Five tests carry `xfail(strict=True)`: the scrobble total, the entry with no album field, the failed-job stats, and the unreadable timestamp in each pipeline. Task 4 removes all five markers.

- [ ] **Step 3: Run the suite; the new tests pass on today's code**

Run: `"$PY" -m pytest tests/test_lastfm_job_results.py -q -p no:cacheprovider -rx`
Expected: `18 passed, 5 xfailed`, with the five xfails listed (`test_the_scrobble_total_counts_completed_scrobbles_only`, `test_an_entry_with_no_album_field_is_not_an_album_play`, `test_a_failed_lastfm_job_records_no_listening_stats`, and the two `test_one_unreadable_timestamp_does_not_fail_the_*`). A strict xfail that passes is an error, so each of the five fails on today's code for the reason in its docstring. Any other failure is a fault in the test, not in the code: today's code is the reference.

- [ ] **Step 4: Mutation evidence**

For each row: apply the edit to the named file, run the named test, confirm it FAILS, then restore with `git checkout -- <file>` and confirm the test passes again. Run: `"$PY" -m pytest tests/test_lastfm_job_results.py -q -p no:cacheprovider -k <test name>`.

| # | File | Planted defect | Test that must fail |
|---|---|---|---|
| 1 | `scrobblescope/orchestrator/__init__.py`, `fetch_top_albums_async` | `for page in pages:` becomes `for page in pages[:1]:` | `test_album_counts_come_from_the_scrobbles_on_every_page` |
| 2 | `scrobblescope/lastfm.py`, `fetch_recent_tracks_page_async` | delete the call `_normalise_track_list(data)` | `test_a_lone_track_object_counts_as_one_scrobble` |
| 3 | `fetch_top_albums_async` | delete `if not date:` and its `continue` | `test_the_now_playing_entry_is_not_an_album_play` |
| 4 | `fetch_top_albums_async` | `if ts < from_ts or ts > to_ts:` becomes `if ts <= from_ts or ts > to_ts:` | `test_the_year_window_includes_its_first_and_last_second` |
| 5 | `fetch_top_albums_async` | delete that whole `if ts < from_ts or ts > to_ts:` block | `test_scrobbles_outside_the_year_are_not_counted` |
| 6 | `fetch_top_albums_async` | `if alb and art and name:` becomes `if True:` | `test_an_entry_with_no_album_artist_or_track_name_is_not_an_album_play` |
| 7 | `fetch_top_albums_async` | `if "original_artist" not in albums[key]:` becomes `if True:` | `test_the_first_casing_seen_names_the_album` |
| 8 | `_record_lastfm_stats` | delete `jobs.record_partial_source(job_id, "lastfm")` | `test_a_dropped_page_makes_the_album_job_partial_and_says_so` |
| 9 | `scrobblescope/unmatched.py`, `partition_albums_by_threshold` | `if play_count < min_plays:` becomes `<=` | `test_an_album_exactly_at_both_minimums_is_eligible` |
| 10 | `_fetch_job_albums` | delete the `jobs.succeed(job_id, [], "No albums found ...")` line | `test_when_every_album_is_below_a_minimum_the_job_ends_with_the_report` |
| 11 | `_fetch_job_albums` | `fetch_metadata.get("status") == "error"` becomes `== "never"` | `test_an_unusable_first_page_ends_the_album_job_as_lastfm_unavailable` |
| 12 | `lastfm.py`, `fetch_recent_tracks_page_async` | `reraise=(UserNotFoundError, PrivateProfileError)` becomes `reraise=(PrivateProfileError,)` | both `..._on_a_later_page_ends_the_..._as_user_not_found` tests |
| 13 | `scrobblescope/heatmap.py`, `_aggregate_daily_counts` | `from_date <= day <= to_date` becomes `from_date <= day < to_date` | `test_each_scrobble_is_counted_on_its_utc_day` |
| 14 | `_aggregate_daily_counts` | after the `uts` guard add `if not track.get("album", {}).get("#text"): continue` | `test_a_scrobble_with_no_album_or_artist_still_counts_on_the_heatmap` |
| 15 | `_aggregate_daily_counts` | `from_date <= day` becomes `from_date < day` | `test_the_heatmap_window_is_365_days_ending_today` |
| 16 | `_fetch_and_process_heatmap` | "Heatmap may be incomplete." loses its full stop | `test_a_dropped_page_makes_the_heatmap_partial_and_says_so` |
| 17 | `_fetch_and_process_heatmap` | `fetch_metadata.get("status") == "error"` becomes `== "never"` | `test_an_unusable_first_page_ends_the_heatmap_as_lastfm_unavailable` |
| 18 | `_report_heatmap_failure` | replace the classifier call with `error_code = "internal_error"` | `test_a_user_not_found_on_a_later_page_ends_the_heatmap_as_user_not_found` |
| 19 | `fetch_top_albums_async` | `"total_scrobbles": total_tracks,` becomes `"total_scrobbles": sum(a["play_count"] for a in albums.values()),` (12 in-window plays, not the 24 entries returned) | `test_scrobbles_outside_the_year_are_not_counted` |

The five `xfail(strict=True)` tests are proved by their XFAIL status in Step 3 on unmodified code (they fail now) and by Task 4 (they pass after the change, where a leftover marker would turn into a strict XPASS failure).

- [ ] **Step 5: Section 4 entry, gates, commit**

Entry heading: `### <commit date> - Last.fm-derived job results are pinned before the seam work`.
Body:

```
Side task, no batch tag (PR #4 of the pre-Batch-23 tranche, task 23a, review card B-3): parity tests for the Last.fm path ahead of the scrobbles-not-pages refactor.

Owner intent: "Any new tests should always test intended behavior and not that the func/code works as written." AGENTS.md "Refactor requires parity tests".

What changed: `tests/test_lastfm_job_results.py` runs the album and heatmap pipelines with only the Last.fm HTTP edge faked (`tests/helpers.py`: `FakeLastfm`, `lastfm_edge`, `lastfm_page`, `lastfm_track`, `lastfm_now_playing`) and asserts on the job each one publishes: aggregation across pages, the year and 365-day windows, the now-playing entry, empty names, casing, the partial-run notice, the below-threshold report, inclusive minimums, and the three failure endings (outage, user not found, unreadable entry). Five tests assert behaviour that Task 4 changes by owner ruling (2026-09-29) and are `xfail(strict=True)` until then.

Deviations: none. No production file changed.

Mutation evidence: 19 planted defects, each failing its named test (the table is in the plan, Task 1 Step 4).

Validation: `pytest -q` -- **N passed**, 5 xfailed.
```

Run the commit procedure (Global Constraints). Stage: `git add tests/helpers.py tests/test_lastfm_job_results.py docs/agents/PLAYBOOK.md` plus whatever `doc_state_sync.py --fix` rewrote (name each file).
Subject: `test(pipeline): Pin Last.fm-derived job results before the seam work` (68 characters).

---

### Task 2: Last.fm usernames leave every log line (F-B23-40)

**Touches:** `scrobblescope/lastfm.py`, `scrobblescope/heatmap.py`, `scrobblescope/orchestrator/__init__.py`, `scrobblescope/utils.py`, `scrobblescope/api_logging.py` (one docstring), `tests/test_log_privacy.py` (new), `tests/services/test_failure_logging.py` (one helper, three calls), `tests/test_lastfm_job_results.py` (one call, Step 1b), `docs/agents/FINDINGS.md`, `docs/agents/PLAYBOOK.md`.
**After:** Task 1; PR #3 merged (this task is written for the tree #3 leaves).

**Files:**
- Create: `tests/test_log_privacy.py`
- Modify: the five source files above (log lines, and one docstring)
- Modify: `tests/services/test_failure_logging.py` (`_assert_type_only_at_error` and the three tests that call it for a username-bearing line)
- Modify: `tests/test_lastfm_job_results.py` (the `heatmap_task` call in `_run_heatmap_task`, Step 1b)
- Modify: `docs/agents/FINDINGS.md` (F-B23-40), `docs/agents/PLAYBOOK.md`

**Interfaces:**
- Consumes: Task 1's `FakeLastfm`, `lastfm_edge`, `lastfm_page`, `lastfm_track`; PR #3's thread entry points `background_task(job_id)` and `heatmap_task(job_id)`, which read the name from the job record (`jobs.params`).
- Produces: no new names. After this task a log record carries a job id where a line needs correlation, the exception class where it reports a crash, and never the username.

Why: F-B23-40 and `BATCH23_DEFINITION.md` "Data handling": a Last.fm handle paired with a scrobble total is a listener-linked fact, and the export path will share this code. The tranche spec (PR #4 row) says "Last.fm usernames leave the logs (F-B23-40)"; the job id replaces the name where a line needs correlation. The message a browser user reads ("User 'x' was not found on Last.fm.") is not a log line and stays.

What is in this task, and what is not. At 5dde407 an `ast` walk finds eleven log lines in five files that name a username variable, and a twelfth carrier the walk cannot see: `utils.get_cached_response` writes `Cache hit for <url>_..._user:<name>_...` at DEBUG on every cache hit (the cache key embeds the request's query string). PR #3 removes three of the eleven: the registration-year warning in `routes/album_flow.py` (a failed lookup now refuses the search) and the two heatmap pre-check lines in `routes/heatmap_flow.py` (they move into the new `routes/precheck.py` as class-only lines, with #3's own test `test_a_failed_check_logs_the_class_and_never_the_listeners_name`). Those three are #3's; this task neither changes nor tests them. What remains is **nine lines in four files**: eight username lines (`lastfm.py` x2, `heatmap.py` x3, `orchestrator/__init__.py` x3) and the cache-hit line in `utils.py`.

The lines, with their replacements (find each by its text with `git grep -n "<text>" -- scrobblescope`):

| Where | Line today | Replacement |
|---|---|---|
| `lastfm.py`, `fetch_recent_tracks_page_async` | `logging.error(f"Profile of {username} is private on Last.fm")` | `logging.error("Profile went private on Last.fm during a job")` |
| `lastfm.py`, same function | `logging.error(f"User {username} not found on Last.fm")` | `logging.error("User not found on Last.fm during a job")` |
| `heatmap.py`, `_fetch_and_process_heatmap` | `logging.info(f"Heatmap Last.fm fetch for {username}: {fetch_elapsed:.1f}s")` | `logging.info(f"Heatmap Last.fm fetch for job {job_id}: {fetch_elapsed:.1f}s")` |
| `heatmap.py`, same function | `logging.info("Heatmap ready for %s: %s scrobbles", username, total)` | `logging.info("Heatmap job %s is ready", job_id)` (the scrobble total leaves the line) |
| `heatmap.py`, `_report_heatmap_failure` | `log_failure(f"Unhandled error in heatmap task for {username}")` | `log_failure(f"Unhandled error in heatmap task for job {job_id}")` |
| `orchestrator/__init__.py`, `fetch_top_albums_async` | `logging.debug(f"Start fetch_top_albums_async(user={username}, year={year})")` | `logging.debug(f"Start fetch_top_albums_async(year={year})")` |
| `orchestrator/__init__.py`, `_fetch_and_process` | `log_failure(f"Error processing request for {username} in {year}")` | `log_failure(f"Error processing request for job {job_id} in {year}")` |
| `orchestrator/__init__.py`, `_report_album_failure` | `log_failure(f"Unhandled error in background task for {username}/{year}")` | `log_failure(f"Unhandled error in background task for job {job_id}, year {year}")` |
| `utils.py`, `get_cached_response` | `logging.debug(f"Cache hit for {key}")` | `logging.debug("Cache hit for %s", url)` (the URL has no query string; the key never reaches a log) |

The existing tests that look for a fragment (`"Error processing request"`, `"Unhandled error in background"`, `"Unhandled error in heatmap"`) still match.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_log_privacy.py`:

```python
"""A Last.fm username never reaches a log line (F-B23-40).

Each test runs one pipeline, one thread entry point or the Last.fm page layer
with a distinctive username and fails if that string appears in any record at
any level, in its message or in its formatted exception text. Where a line needs
correlation it names the job id instead. The Last.fm pre-check lines of the
routes are PR #3's and are tested there (``tests/test_precheck.py``).
"""

import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.errors import PrivateProfileError, UserNotFoundError
from scrobblescope.heatmap import _fetch_and_process_heatmap, heatmap_task
from scrobblescope.lastfm import fetch_recent_tracks_page_async
from scrobblescope.orchestrator import _fetch_and_process, background_task
from scrobblescope.utils import REQUEST_CACHE, get_cached_response, set_cached_response
from tests.helpers import (
    TEST_JOB_PARAMS,
    FakeLastfm,
    NoopAsyncContext,
    lastfm_edge,
    lastfm_page,
    lastfm_track,
    make_response_context,
)

LISTENER = "zqx_listener_7"


def _logged(caplog):
    """Every record's message and formatted exception text, as one string."""
    return "\n".join(f"{r.getMessage()}\n{r.exc_text or ''}" for r in caplog.records)


def _assert_listener_unlogged(caplog):
    """Fail if the listener's name is anywhere in the log, or nothing was logged."""
    assert caplog.records, "nothing was logged; the test would pass for any code"
    assert LISTENER not in _logged(caplog)


def _error_lines(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]


@pytest.fixture
def empty_request_cache():
    """The request cache is module state: start and leave it empty."""
    REQUEST_CACHE.clear()
    yield
    REQUEST_CACHE.clear()


@pytest.mark.asyncio
async def test_a_heatmap_run_logs_its_job_id_not_its_listener(caplog):
    """
    GIVEN a heatmap run that succeeds
    WHEN it logs its fetch timing and its completion
    THEN the lines name the job, and neither the username nor the scrobble total.

    Planted defect: log "Heatmap ready for <username>: <total> scrobbles", or
    "Heatmap Last.fm fetch for <username>".
    """
    yesterday = datetime.now(UTC).replace(microsecond=0) - timedelta(days=1)
    page = lastfm_page([lastfm_track("A", "B", "C", yesterday)])
    job_id = jobs.create({"username": LISTENER, "mode": "heatmap"})

    with (
        lastfm_edge(FakeLastfm({1: page})),
        patch("scrobblescope.heatmap.cleanup_expired_cache"),
        caplog.at_level(logging.DEBUG),
    ):
        await _fetch_and_process_heatmap(job_id, LISTENER)

    _assert_listener_unlogged(caplog)
    messages = [r.getMessage() for r in caplog.records]
    assert any("Heatmap job" in m and job_id in m and "ready" in m for m in messages)
    assert any("Heatmap Last.fm fetch" in m and job_id in m for m in messages)


@pytest.mark.asyncio
async def test_an_album_run_logs_no_listener(caplog):
    """
    GIVEN an album run that finds nothing to enrich
    WHEN it runs end to end
    THEN no record carries the username.

    Planted defect: restore the username to the fetch_top_albums_async debug line.
    """
    page = lastfm_page([lastfm_track("A", "B", "C", datetime(2023, 6, 15, tzinfo=UTC))])
    job_id = jobs.create(TEST_JOB_PARAMS)

    with lastfm_edge(FakeLastfm({1: page})), caplog.at_level(logging.DEBUG):
        await _fetch_and_process(job_id, LISTENER, 2023, "playcount", "all")

    _assert_listener_unlogged(caplog)


def test_the_heatmap_backstop_logs_the_job_id_not_the_listener(caplog):
    """
    GIVEN a heatmap job whose record carries the listener's name, and a pipeline
    that dies on an unexpected error
    WHEN heatmap_task(job_id) reads the name from the record and its backstop
    reports the failure
    THEN the ERROR line names the job and the exception class, not the username.

    Planted defect: restore the username to _report_heatmap_failure's line.
    """
    job_id = jobs.create({"username": LISTENER, "mode": "heatmap"})
    assert jobs.params(job_id)["username"] == LISTENER

    with (
        patch("scrobblescope.heatmap.release_job_slot"),
        patch("scrobblescope.jobs.start", side_effect=RuntimeError("boom")),
        caplog.at_level(logging.DEBUG),
    ):
        heatmap_task(job_id)

    assert jobs.progress(job_id)["error_code"] == "internal_error"
    _assert_listener_unlogged(caplog)
    assert any(job_id in line for line in _error_lines(caplog))


def test_the_album_backstop_logs_the_job_id_not_the_listener(caplog):
    """
    GIVEN an album job whose record carries the listener's name, and a crash
    that gets past the pipeline's own handler
    WHEN background_task(job_id) reads the name from the record and its
    backstop reports the failure
    THEN the ERROR line names the job and the exception class, not the username.

    Planted defect: restore the username to _report_album_failure's line.
    """
    job_id = jobs.create({**TEST_JOB_PARAMS, "username": LISTENER})
    assert jobs.params(job_id)["username"] == LISTENER

    async def explode(*args, **kwargs):
        raise RuntimeError("boom")

    with (
        patch("scrobblescope.orchestrator.release_job_slot"),
        patch("scrobblescope.orchestrator._fetch_and_process", explode),
        caplog.at_level(logging.DEBUG),
    ):
        background_task(job_id)

    assert jobs.progress(job_id)["error_code"] == "internal_error"
    _assert_listener_unlogged(caplog)
    assert any(job_id in line for line in _error_lines(caplog))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "body", "raises"),
    [(404, None, UserNotFoundError), (403, {"error": 17}, PrivateProfileError)],
    ids=["not-found", "went-private"],
)
async def test_the_page_layer_names_no_listener_when_it_refuses(
    status, body, raises, caplog
):
    """
    GIVEN Last.fm refuses a page mid-job (404, or error 17)
    WHEN the page layer raises its typed failure
    THEN the line it logs does not carry the username.

    Planted defect: restore the username to either refusal line (each case
    catches its own line).
    """
    session = MagicMock()
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=body)
    session.get.return_value = make_response_context(resp)

    with (
        patch("scrobblescope.lastfm.get_cached_response", return_value=None),
        patch(
            "scrobblescope.lastfm.get_lastfm_limiter", return_value=NoopAsyncContext()
        ),
        caplog.at_level(logging.DEBUG),
    ):
        with pytest.raises(raises):
            await fetch_recent_tracks_page_async(
                session, LISTENER, 1, 2, page=1, retries=1
            )

    _assert_listener_unlogged(caplog)


def test_a_cache_hit_logs_no_listener(caplog, empty_request_cache):
    """
    GIVEN a Last.fm answer cached under the listener's request, so its cache key
    embeds ``user:<name>``
    WHEN a repeat lookup hits the cache, with ``get_cached_response`` left real
    (every other test here patches it away and cannot reach this line)
    THEN the hit is logged without the key.

    Planted defect: log the key again, ``f"Cache hit for {key}"``.
    """
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {"method": "user.getinfo", "user": LISTENER, "api_key": "k"}
    set_cached_response(url, {"user": {}}, params)

    with caplog.at_level(logging.DEBUG):
        assert get_cached_response(url, params) == {"user": {}}

    assert any(r.getMessage().startswith("Cache hit") for r in caplog.records)
    _assert_listener_unlogged(caplog)
```

In `tests/services/test_failure_logging.py` give `_assert_type_only_at_error` an optional `listener` and pass it where the line under test used to carry a username. Replace the function's signature and add the check at its top:

```python
def _assert_type_only_at_error(
    caplog, *, error_fragment, exc_name="RuntimeError", listener=None
):
    """Assert the marker is absent from every ERROR record and present in DEBUG.

    When ``listener`` is given, no record at any level may carry that Last.fm
    username either (F-B23-40).
    """
    if listener is not None:
        assert all(listener not in r.getMessage() for r in caplog.records)
    serious = [r for r in caplog.records if r.levelno >= logging.WARNING]
```

(the rest of the function is unchanged). Then pass `listener="testuser"` in `test_album_pipeline_crash_logs_the_class_only_at_error`, `test_album_backstop_logs_the_class_only_at_error` and `test_heatmap_backstop_logs_the_class_only_at_error` (each already calls the function with `"testuser"` as the name it hands the code under test), for example:

```python
    _assert_type_only_at_error(
        caplog, error_fragment="Error processing request", listener="testuser"
    )
```

The heatmap pre-check tests in that file are #3's: their lines are class-only already and need no change.

- [ ] **Step 1b: Adapt Task 1's heatmap helper to PR #3**

In `tests/test_lastfm_job_results.py`, `_run_heatmap_task` calls `heatmap_task(job_id, "parity_user")`. After PR #3 the thread entry point reads the name from the job record, so change the call to `heatmap_task(job_id)`. No assertion changes. Do this before the first test run below. Name the edit in the commit body (an existing test edited: `tests/test_lastfm_job_results.py::_run_heatmap_task`) and in the Section 4 entry's deviations.

- [ ] **Step 2: Run the tests; they fail**

Run: `"$PY" -m pytest tests/test_log_privacy.py tests/services/test_failure_logging.py -q -p no:cacheprovider`
Expected: 10 failures and no other result change. In `tests/test_log_privacy.py` 7: the heatmap run, the album run, both thread-entry backstop tests, both page-layer cases and the cache hit, each an `assert 'zqx_listener_7' not in ...` or a missing job id. In `tests/services/test_failure_logging.py` 3: the album pipeline crash, the album backstop and the heatmap backstop, each failing on `listener not in r.getMessage()`.

- [ ] **Step 3: Change the log lines**

Apply the table above, one line each. Keep every surrounding statement as it is.

- [ ] **Step 4: Correct the formatter's docstring**

In `scrobblescope/api_logging.py` the `RedactingFormatter` docstring lists the cache-hit line as a carrier. Replace

```
    of a failure names its class only: ``utils.log_failure``, and
    ``utils.run_async_in_thread``) and ``utils.get_cached_response``'s debug
    line (its cache key embeds the URL), and any future line that writes an
    exception's message. ``utils.retry_with_semaphore``'s error line (on a
```

with

```
    of a failure names its class only: ``utils.log_failure``, and
    ``utils.run_async_in_thread``), and any future line that writes an
    exception's message. ``utils.get_cached_response``'s debug line was one
    more until it stopped writing the cache key (the key embeds the request's
    query string: the API key and the listener's name).
    ``utils.retry_with_semaphore``'s error line (on a
```

(Check the surrounding lines of the docstring after the edit and re-wrap by hand if ruff format complains; the docstring text, not its wrapping, is the point. `tests/services/test_api_logging.py` feeds the formatter hand-made cache-key strings and does not call `get_cached_response`: it is unaffected.)

- [ ] **Step 5: Run the new tests and the neighbours**

Run: `"$PY" -m pytest tests/test_log_privacy.py tests/services/test_failure_logging.py tests/services/test_api_logging.py tests/test_utils.py tests/test_heatmap.py tests/test_lastfm_job_results.py -q -p no:cacheprovider`
Expected: all pass (`5 xfailed` from Task 1 remain xfailed).

- [ ] **Step 6: Mutation evidence**

Restore each line below to its old form in turn (Step 3's table, "Line today" column), run the named tests with `"$PY" -m pytest <file> -q -p no:cacheprovider -k "<name>"`, confirm each fails, then `git checkout -- <file>` the mutation and re-apply the fix.

| # | Line restored | Test that must fail |
|---|---|---|
| 1 | `lastfm.py` went-private line | `test_the_page_layer_names_no_listener_when_it_refuses[went-private]` |
| 2 | `lastfm.py` not-found line | `test_the_page_layer_names_no_listener_when_it_refuses[not-found]` |
| 3 | `heatmap.py` fetch timing line | `test_a_heatmap_run_logs_its_job_id_not_its_listener` |
| 4 | `heatmap.py` "Heatmap ready for" line | `test_a_heatmap_run_logs_its_job_id_not_its_listener` |
| 5 | `heatmap.py` `_report_heatmap_failure` line | `test_the_heatmap_backstop_logs_the_job_id_not_the_listener` and `test_heatmap_backstop_logs_the_class_only_at_error` |
| 6 | `orchestrator/__init__.py` DEBUG start line | `test_an_album_run_logs_no_listener` |
| 7 | `orchestrator/__init__.py` `_fetch_and_process` handler line | `test_album_pipeline_crash_logs_the_class_only_at_error` |
| 8 | `orchestrator/__init__.py` `_report_album_failure` line | `test_the_album_backstop_logs_the_job_id_not_the_listener` and `test_album_backstop_logs_the_class_only_at_error` |
| 9 | `utils.py` cache-hit line | `test_a_cache_hit_logs_no_listener` |

Rows 5 and 8 each run two tests: the thread-entry test reaches the line with a name read from the job record, the existing test with a name handed in directly; either failing is the proof, both are expected to fail.

- [ ] **Step 7: Findings, Section 4 entry, gates, commit**

In `docs/agents/FINDINGS.md`, F-B23-40: change its status line to `- [x] **Status:** resolved <commit date> by the commit that logs a job id in place of a Last.fm username; the scrobble-total line is gone, and the request-cache hit line no longer writes the cache key (which embeds the name). The route pre-check lines left with PR #3's shared pre-check. Source: review 4 of PR #245 (backend), R4-backend-9.` Leave the entry in place (rotation is at batch close-out, AGENTS.md "Finding-Writing Rules" item 3); if `doc_state_sync.py --check` objects, follow its message.

Entry heading: `### <commit date> - Last.fm usernames leave the log lines`. Body: scope (nine lines in four files: eight username lines in `lastfm.py`, `heatmap.py` and `orchestrator/__init__.py`, and the cache-hit line in `utils.py`; the three route lines that were also in F-B23-40's sweep left with PR #3), owner intent (F-B23-40; the tranche spec's "Last.fm usernames leave the logs"), what changed (the table, and the formatter docstring), deviations (three existing tests in `tests/services/test_failure_logging.py` now also assert that the username is absent; `tests/test_lastfm_job_results.py::_run_heatmap_task` calls `heatmap_task(job_id)` after PR #3, Step 1b; none else), mutation evidence (Step 6), validation.

Commit body names `tests/services/test_failure_logging.py::test_album_pipeline_crash_logs_the_class_only_at_error`, `::test_album_backstop_logs_the_class_only_at_error` and `::test_heatmap_backstop_logs_the_class_only_at_error` (each gains a username-absent assertion through the shared helper), and the Step 1b edit to `tests/test_lastfm_job_results.py::_run_heatmap_task`.
Subject: `fix(logging): Keep Last.fm usernames out of every log line` (58 characters).

---
### Task 3: Make cross-module names public; add `release_status` (23b)

**Touches:** `scrobblescope/cache.py`, `scrobblescope/domain.py`, `scrobblescope/release_checks.py`, `scrobblescope/release_status.py` (new), `scrobblescope/routes/api.py`, `scrobblescope/orchestrator/__init__.py`, `scrobblescope/orchestrator/_cache.py`, `scrobblescope/orchestrator/_results.py`, `scrobblescope/enrichment.py` (one docstring), nine existing test files (listed in Step 8), `tests/test_module_boundaries.py` (new), `.claude/SESSION_CONTEXT.md`, `docs/architecture/runtime-system.md`, `docs/agents/PLAYBOOK.md`.
**After:** Task 2 (shares `orchestrator/__init__.py`); PR #3 merged (a textual rebase only).

**Files:**
- Create: `scrobblescope/release_status.py`, `tests/test_module_boundaries.py`
- Modify: the source files above; the nine test files (mechanical renames, no assertion changes)
- Modify: `.claude/SESSION_CONTEXT.md` Sections 3-4, `docs/architecture/runtime-system.md`, `docs/agents/PLAYBOOK.md`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: public names `cache.get_db_connection`, `cache.batch_lookup_metadata`, `cache.batch_persist_metadata`, `cache.batch_lookup_original_release`, `cache.batch_persist_original_release`, `cache.cleanup_stale_metadata`, `domain.matches_release_criteria`; the leaf module `scrobblescope.release_status` with `CHECK_UNCHECKED`, `CHECK_CONFIRMED`, `CHECK_MOVED_OUT`, `CHECK_UNAVAILABLE`, `STATUS_PENDING`, `STATUS_RUNNING`, `STATUS_DONE`, `STATUS_SKIPPED`; `tests/test_module_boundaries.py` (Task 4 adds a rule to it). Behaviour is unchanged. Metadata-encoding PR #5 reworks `cache.py` on top of these names.

Why: the sweep in "Assumptions checked" found the release worker and the album pipeline reaching into `cache.py` and `domain.py` through underscore names, and `routes/api.py` importing the thread-owning worker for two strings. A private name with two callers in two packages is a public interface that says otherwise (architecture-walk-2, B-7). The drain item of the design is already done (`utils.cancel_and_drain`). The facade shape inside `orchestrator/` (`_cache.py` reading `_orchestrator._name`) stays: it is one package and the module docstring explains why. So do the `routes/` facade reads (`_routes._...`): same package.

- [ ] **Step 1: Write the guard test**

Create `tests/test_module_boundaries.py`:

```python
"""Module boundaries: no module reaches into another module's private names.

A name with a leading underscore belongs to its own module, or, for the
packages ``orchestrator`` and ``routes``, to its own package (their submodules
read the facade's names on purpose; see the ``orchestrator`` module docstring).
These tests walk the source with ``ast`` and fail on the first cross-boundary
read, so the next private name that gains a second caller is caught on the day
it does (architecture-walk-2, B-7).
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "scrobblescope"
ROOT = SRC.parent


def _module_name(path):
    """The dotted module a source file defines (``__init__`` names its package)."""
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _unit(module):
    """The boundary a module sits in: its package, or itself for a lone file."""
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else ""


def _is_private(name):
    return name.startswith("_") and not name.startswith("__")


def _private_reads():
    """Every private name one boundary reads from another, as readable strings."""
    found = []
    for path in sorted(SRC.rglob("*.py")):
        importer = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        aliases = {}
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("scrobblescope")
            ):
                continue
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
                if _is_private(item.name) and _unit(node.module) != _unit(importer):
                    found.append(f"{importer}: from {node.module} import {item.name}")
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and _is_private(node.attr)
                and isinstance(node.value, ast.Name)
            ):
                target = aliases.get(node.value.id)
                if target and _unit(target) != _unit(importer):
                    found.append(f"{importer}: {node.value.id}.{node.attr} ({target})")
    return found


def test_no_module_reads_another_modules_private_name():
    """
    GIVEN every module under scrobblescope/
    WHEN its imports and attribute reads are walked
    THEN none reads an underscore name from a module in another package.

    Planted defect: add ``from scrobblescope.utils import _GlobalThrottle`` to
    ``release_checks.py``; the test names it.
    """
    assert _private_reads() == []


def test_the_routes_never_import_the_correction_worker():
    """
    GIVEN the route modules
    WHEN their imports are read
    THEN none imports ``release_checks``: the routes read its vocabulary from
    ``release_status`` and the job's stats, and never start or touch the
    worker thread.

    Planted defect: add ``from scrobblescope.release_checks import
    enqueue_release_check`` to ``routes/api.py``.
    """
    offenders = []
    for path in sorted((SRC / "routes").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module == (
                "scrobblescope.release_checks"
            ):
                offenders.append(path.name)
    assert offenders == []


def test_release_status_strings_are_the_ones_the_browser_compares():
    """
    GIVEN the release-check vocabulary
    WHEN the Results page's script and the worker are compared with it
    THEN the strings the script tests for are exactly the module's values, and
    the other four are pinned here, because they travel in JSON a page reads.

    Planted defect: change ``CHECK_MOVED_OUT`` to ``"moved-out"``.
    """
    from scrobblescope import release_status

    script = (ROOT / "static/js/results-release-checks.js").read_text(
        encoding="utf-8"
    )
    for value in (
        release_status.CHECK_CONFIRMED,
        release_status.CHECK_MOVED_OUT,
        release_status.STATUS_PENDING,
        release_status.STATUS_RUNNING,
    ):
        assert f"'{value}'" in script
    assert (
        release_status.CHECK_UNCHECKED,
        release_status.CHECK_CONFIRMED,
        release_status.CHECK_MOVED_OUT,
        release_status.CHECK_UNAVAILABLE,
    ) == ("unchecked", "confirmed", "moved_out", "unavailable")
    assert (
        release_status.STATUS_PENDING,
        release_status.STATUS_RUNNING,
        release_status.STATUS_DONE,
        release_status.STATUS_SKIPPED,
    ) == ("pending", "running", "done", "skipped")
```

- [ ] **Step 2: Run it; it fails and names the offenders**

Run: `"$PY" -m pytest tests/test_module_boundaries.py -q -p no:cacheprovider`
Expected: 3 failures. `test_no_module_reads_another_modules_private_name` fails listing exactly these ten reads (the list is the proof the sweep is complete; if it lists more, rename those too; if it lists fewer, PR #3 already moved one):

```
scrobblescope.orchestrator: from scrobblescope.cache import _batch_lookup_metadata
scrobblescope.orchestrator: from scrobblescope.cache import _batch_lookup_original_release
scrobblescope.orchestrator: from scrobblescope.cache import _batch_persist_metadata
scrobblescope.orchestrator: from scrobblescope.cache import _cleanup_stale_metadata
scrobblescope.orchestrator: from scrobblescope.cache import _get_db_connection
scrobblescope.orchestrator._results: from scrobblescope.domain import _matches_release_criteria
scrobblescope.release_checks: from scrobblescope.cache import _batch_lookup_original_release
scrobblescope.release_checks: from scrobblescope.cache import _batch_persist_original_release
scrobblescope.release_checks: from scrobblescope.cache import _get_db_connection
scrobblescope.release_checks: from scrobblescope.domain import _matches_release_criteria
```

`test_the_routes_never_import_the_correction_worker` fails with `['api.py']`; the wire-strings test fails with `ImportError` (no `release_status` yet).

- [ ] **Step 3: Rename the cache and domain names**

Run from the worktree root (Git Bash). It renames each name as a whole word in `scrobblescope/` and `tests/` only; `git grep -w` treats `_` as a word character, so `test_matches_release_criteria_...` is untouched:

```bash
for pair in \
  "_get_db_connection:get_db_connection" \
  "_batch_lookup_metadata:batch_lookup_metadata" \
  "_batch_persist_metadata:batch_persist_metadata" \
  "_batch_lookup_original_release:batch_lookup_original_release" \
  "_batch_persist_original_release:batch_persist_original_release" \
  "_cleanup_stale_metadata:cleanup_stale_metadata" \
  "_matches_release_criteria:matches_release_criteria"; do
  old="${pair%%:*}"; new="${pair##*:}"
  git grep -lw -e "$old" -- scrobblescope tests | xargs -r sed -i -E "s/\b${old}\b/${new}/g"
done
git diff --stat
```

Expected: `git diff --stat` shows `cache.py`, `domain.py`, `release_checks.py`, `enrichment.py` (one docstring), the orchestrator files and the nine test files, and no other file.

Then fix the two places a plain rename is not enough:

1. `scrobblescope/orchestrator/__init__.py`: in the `from scrobblescope.orchestrator._results import (...)` block delete the line `matches_release_criteria,`, and delete `"matches_release_criteria",` from `__all__`. The facade no longer re-exports a domain function; tests import it from `domain`.
2. `tests/services/test_orchestrator_helpers.py`: in its `from scrobblescope.orchestrator import (...)` block delete `matches_release_criteria,`, and add `from scrobblescope.domain import matches_release_criteria` with the file's other `scrobblescope` imports (if the file already has a `from scrobblescope.domain import ...` line, add the name to it).

Then restore import order and formatting:

Run: `"$RUFF" check --select I,F --fix scrobblescope tests && "$RUFF" format scrobblescope tests`
Expected: no remaining findings. (F401 would report an unused name left behind by the edits above.)

- [ ] **Step 4: Add the `release_status` leaf**

Create `scrobblescope/release_status.py`:

```python
"""The release-check vocabulary: the strings the correction worker writes and
the Results page reads.

They are wire values. ``static/js/results-release-checks.js`` compares an
album's ``state`` with ``'confirmed'`` and ``'moved_out'`` and the job's
``status`` with ``'pending'`` and ``'running'``, and ``/api/release_checks``
serves all eight inside JSON. They live in their own module so the routes can
name them without importing the worker, which owns a thread and a queue
(``release_checks.py``).

    release_status <- (leaf)
"""

# Each result's ``release_check`` field, as the results page reads it.
CHECK_UNCHECKED = "unchecked"
CHECK_CONFIRMED = "confirmed"
CHECK_MOVED_OUT = "moved_out"
CHECK_UNAVAILABLE = "unavailable"

# The job's own ``progress.stats.release_check`` status. PENDING is never
# written: it is what the API reports while the key is absent, between a job
# publishing its results and the worker first reporting on them.
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_SKIPPED = "skipped"
```

In `scrobblescope/release_checks.py` delete the two comment blocks and the eight assignments (from `# Each result's ``release_check`` field` down to `STATUS_SKIPPED = "skipped"`) and add, with the other `scrobblescope` imports:

```python
from scrobblescope.release_status import (
    CHECK_CONFIRMED,
    CHECK_MOVED_OUT,
    CHECK_UNAVAILABLE,
    CHECK_UNCHECKED,
    STATUS_DONE,
    STATUS_RUNNING,
    STATUS_SKIPPED,
)
```

(`STATUS_PENDING` is not used by the worker; ruff's F401 in Step 5 confirms the list -- add or drop a name until it is clean.) In `scrobblescope/routes/api.py` change `from scrobblescope.release_checks import CHECK_UNCHECKED, STATUS_PENDING` to `from scrobblescope.release_status import CHECK_UNCHECKED, STATUS_PENDING`. The docstring of `api.release_checks` that points at `scrobblescope/release_checks.py` stays: it names the worker, which is right.

- [ ] **Step 5: Run the guard and the whole suite**

Run: `"$RUFF" check --select I,F --fix scrobblescope tests && "$RUFF" format scrobblescope tests`
Run: `"$PY" -m pytest tests/test_module_boundaries.py -q -p no:cacheprovider`
Expected: `3 passed`.
Run: `"$PY" -m pytest -q -p no:cacheprovider`
Expected: every test passes, the same N as before plus 3, and the same 5 xfailed. No assertion in the nine test files changed: review `git diff -U0 -- tests`; every removed line has an added twin that differs only by the renamed identifier, apart from the one import move in `test_orchestrator_helpers.py`.

- [ ] **Step 6: Mutation evidence**

| # | Plant | Test that must fail |
|---|---|---|
| 1 | in `release_checks.py` add `from scrobblescope.utils import _GlobalThrottle` | `test_no_module_reads_another_modules_private_name` (names `release_checks`) |
| 2 | in `routes/api.py` add `from scrobblescope.release_checks import enqueue_release_check` | `test_the_routes_never_import_the_correction_worker` |
| 3 | in `release_status.py` change `CHECK_MOVED_OUT = "moved_out"` to `"moved-out"` | `test_release_status_strings_are_the_ones_the_browser_compares` |

Apply one, run `"$PY" -m pytest tests/test_module_boundaries.py -q -p no:cacheprovider`, confirm the failure, `git checkout -- <file>` (rows 1-2) or edit back (row 3), confirm `3 passed`.

- [ ] **Step 7: Docs follow the code**

`.claude/SESSION_CONTEXT.md` Section 3: change the `domain.py` line's `_matches_release_criteria` to `matches_release_criteria`; change the `cache.py` line to `# asyncpg DB helpers (get_db_connection, retry/backoff, batch lookup/persist, cleanup_stale_metadata)`; add after the `release_checks.py` line:

```
  release_status.py         # the release-check wire strings (CHECK_*, STATUS_*): the worker writes them, /api/release_checks and the Results page read them
```

Section 4: add `release_status.py <- (leaf)` after `unmatched.py <- (leaf)`; in the `release_checks.py` line insert `release_status` after `musicbrainz`; in the `routes/api.py` line insert `release_status` after `jobs` and drop `release_checks`, giving `routes/api.py           <- domain, jobs, release_status, spotify, utils; routes (facade)`.

`docs/architecture/runtime-system.md`: in the Runtime subgraph add the node `ReleaseStatus[release_status.py<br/>check and status strings]` after the `ReleaseChecks` node; replace the edge `Routes --> ReleaseChecks` with `Routes --> ReleaseStatus`; add `ReleaseChecks --> ReleaseStatus` beside the other `ReleaseChecks -->` edges; add `ReleaseStatus` to the `class ... runtime` list. The "eleven nodes import config" paragraph stays true (the new module imports nothing); re-check it with a module-level `ast` walk for `scrobblescope.config` imports and say so in the Section 4 entry. Render the edited Mermaid block with the Mermaid validator tool and fix any error before committing.

Sweep: `git grep -nw -e _get_db_connection -e _batch_lookup_metadata -e _batch_persist_metadata -e _batch_lookup_original_release -e _batch_persist_original_release -e _cleanup_stale_metadata -e _matches_release_criteria -- . ':!docs/history' ':!docs/logarchive' ':!docs/superpowers/plans'`
Expected: one hit, `BATCH23_DEFINITION.md` ("Move `_matches_release_criteria` into `scrobblescope/domain.py`", a checked, dated Part A record): a point-in-time statement, left as written.

- [ ] **Step 8: Section 4 entry, gates, commit**

Entry heading: `### <commit date> - Names that cross modules are public`. Body: scope (seven renames, one new leaf, one guard test), owner intent ("seams worth doing before feature work are done now", 2026-09-29; the 2026-09-29 rulings allow seam commits to edit tests), what changed, deviations (the drain item was already done; none else), mutation evidence, validation, and the `ast` re-check of the config-import count.

Commit body names every edited test file: `tests/services/test_failure_logging.py`, `tests/services/test_orchestrator_fetch_spotify.py`, `tests/services/test_orchestrator_process_albums.py`, `tests/services/test_release_checks.py`, `tests/test_pipeline_integration.py`, `tests/test_repositories.py`, `tests/services/test_cache.py`, `tests/services/test_enrichment.py` (one docstring), `tests/services/test_orchestrator_helpers.py` (renames, and the import of `matches_release_criteria` moves from the facade to `domain`); no assertion changed.
Subject: `refactor(seams): Make cross-module names public; add release_status` (67 characters).

---
### Task 4: Hand callers scrobbles, not pages (23c)

**Touches:** `scrobblescope/plays.py` (new), `scrobblescope/lastfm.py`, `scrobblescope/heatmap.py`, `scrobblescope/orchestrator/__init__.py`, `tests/test_plays.py` (new), `tests/services/test_lastfm_service.py`, `tests/test_heatmap.py`, `tests/services/test_lastfm_logic.py`, `tests/services/test_orchestrator_fetch_and_process.py` (one test), `tests/test_provider_fixtures.py`, `tests/test_pipeline_integration.py` (one patch string), `tests/test_lastfm_job_results.py` (markers), `tests/test_module_boundaries.py`, `.claude/SESSION_CONTEXT.md`, `docs/architecture/runtime-system.md`, `docs/architecture/top-albums-sequence.md`, `docs/architecture/heatmap-sequence.md`, `docs/agents/FINDINGS.md`, `BATCH23_DEFINITION.md`, `docs/agents/PLAYBOOK.md`.
**After:** Task 3 (and therefore PR #3).

**Files:**
- Create: `scrobblescope/plays.py`, `tests/test_plays.py`
- Modify: the files above

**Interfaces:**
- Consumes: Task 1's `lastfm_edge` suite (unchanged except its five markers); `errors.ProviderError`; `domain.normalize_name`, `domain.normalize_track_name`; `unmatched.partition_albums_by_threshold` (still called from `fetch_top_albums_async`).
- Produces (Task 5 and Batch 23 WP-2 rely on these exact names):
  - `plays.Play(played_at: datetime, artist: str, album: str, track: str)` -- frozen, slotted; `played_at.tzinfo` must be `datetime.UTC` or `ValueError`.
  - `plays.Window(start: datetime, end: datetime)` -- frozen, both bounds UTC, `start <= end`; `Window.year(year) -> Window`; `start_ts() -> int`; `end_ts() -> int`; `contains(played_at) -> bool` (inclusive both ends).
  - `plays.AlbumKey = tuple[str, str]`; `plays.AlbumTally` (TypedDict: `play_count`, `track_counts`, `original_artist`, `original_album`); `plays.AlbumAggregate(albums: dict[AlbumKey, AlbumTally], plays_seen: int)`.
  - `plays.aggregate_albums(plays: Iterable[Play], window: Window) -> AlbumAggregate`; `plays.aggregate_daily_counts(plays, from_date, to_date) -> dict[str, int]`; `plays.zero_fill_daily_counts(counts, from_date, to_date) -> dict[str, int]`.
  - `lastfm.FetchSummary(pages_expected: int, pages_received: int)` with properties `pages_dropped`, `partial`, `data_loss_pct`; `lastfm.ScrobbleFetch(plays: tuple[Play, ...], summary: FetchSummary, dropped_undated: int, dropped_malformed: int)`; `async lastfm.fetch_scrobbles(username, window: Window, progress_cb=None) -> ScrobbleFetch`.
  - `fetch_top_albums_async` keeps its return shape `(eligible, exclusions, fetch_metadata)` until Task 5.

Why: F-B23-2 (Last.fm's payload shape travels into both calculations) and review card B-3. Batch 23 WP-2's Spotify parser must emit the same record so one aggregator serves both sources. The record is named `Play` because WP-2 already says `iter_plays` and a Spotify row is not a scrobble.

Behaviour changes, each pinned by Task 1 and flipped here, each named in the commit body: (1) `total_scrobbles` no longer counts the now-playing entry (owner ruling 2026-09-29); (2) a track object with no `album`, `artist` or `name` key is skipped by the album calculation instead of being counted under the invented name `"..."`; (3) an unreadable timestamp or a non-object entry is dropped and counted instead of failing the job; (4) a failed Last.fm fetch writes no listening stats before it raises. A fifth, harmless change: plays leave the fetch in page-number order (pages used to arrive in `as_completed` order, so which casing of an album became `original_album` could differ between runs). One accepted cost of change (4): a plain Last.fm outage used to end quietly with `Failed to fetch initial page`; it now raises, so it also logs one class-only ERROR line from the handler (`Error processing request for job ...` for an album job, `Unhandled error in heatmap task for job ...` for a heatmap job). Those lines carry a job id and an exception class and no listener data; the extra line is accepted, and the Section 4 entry says so.

- [ ] **Step 1: Write the failing tests for `plays.py`**

Create `tests/test_plays.py`:

```python
"""Tests for scrobblescope.plays: the record and the pure calculations over it.

The daily-count tests were moved here from tests/test_heatmap.py
(``TestAggregateDailyCounts``) when the calculation stopped reading raw Last.fm
pages; the eight converted ones keep their assertions.
"""

from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest

from scrobblescope.domain import normalize_name, normalize_track_name
from scrobblescope.plays import (
    AlbumAggregate,
    Play,
    Window,
    aggregate_albums,
    aggregate_daily_counts,
    zero_fill_daily_counts,
)


def _play(when, artist="Artist", album="Album", track="Song"):
    return Play(played_at=when, artist=artist, album=album, track=track)


def _noon(day):
    return datetime.combine(day, time(12), tzinfo=UTC)


def _at(day, hour, minute=0, second=0):
    return datetime.combine(day, time(hour, minute, second), tzinfo=UTC)


# ---------------------------------------------------------------------------
# Play and Window
# ---------------------------------------------------------------------------


class TestPlay:
    def test_a_play_refuses_a_naive_timestamp(self):
        """A naive datetime would be read as local time by ``.timestamp()``; a
        source that forgot to convert must fail at the border, not three modules
        later. Planted defect: drop the check in ``Play.__post_init__``."""
        with pytest.raises(ValueError):
            _play(datetime(2023, 6, 15, 12))

    def test_a_play_refuses_a_timestamp_in_another_zone(self):
        """Only UTC counts: day, weekday and hour are read straight from the
        timestamp. Planted defect: accept any aware datetime."""
        minus_five = timezone(timedelta(hours=-5))
        with pytest.raises(ValueError):
            _play(datetime(2023, 6, 15, 12, tzinfo=minus_five))

    def test_a_utc_play_keeps_its_fields(self):
        """A play in UTC is accepted and keeps all four fields as given.
        Planted defect: invert the check in ``Play.__post_init__``, so UTC is the
        one zone refused."""
        when = datetime(2023, 6, 15, 12, tzinfo=UTC)
        play = _play(when, "A", "B", "C")
        assert (play.played_at, play.artist, play.album, play.track) == (
            when,
            "A",
            "B",
            "C",
        )


class TestWindow:
    def test_a_year_window_covers_the_calendar_year_in_epoch_seconds(self):
        """2023-01-01T00:00:00Z .. 2023-12-31T23:59:59Z, the literals the Last.fm
        request has always carried. Planted defect: an end bound one second late."""
        window = Window.year(2023)
        assert window.start_ts() == 1672531200
        assert window.end_ts() == 1704067199

    def test_contains_is_inclusive_at_both_ends(self):
        """Planted defect: make either end exclusive."""
        window = Window.year(2023)
        assert window.contains(window.start)
        assert window.contains(window.end)
        assert not window.contains(window.start - timedelta(seconds=1))
        assert not window.contains(window.end + timedelta(seconds=1))

    def test_a_window_refuses_a_naive_bound(self):
        """Planted defect: drop the UTC check on the bounds in
        ``Window.__post_init__``."""
        with pytest.raises(ValueError):
            Window(start=datetime(2023, 1, 1), end=datetime(2023, 1, 2, tzinfo=UTC))

    def test_a_window_refuses_a_reversed_span(self):
        """Planted defect: drop the ``start > end`` check."""
        with pytest.raises(ValueError):
            Window(
                start=datetime(2023, 1, 2, tzinfo=UTC),
                end=datetime(2023, 1, 1, tzinfo=UTC),
            )


# ---------------------------------------------------------------------------
# aggregate_albums
# ---------------------------------------------------------------------------


class TestAggregateAlbums:
    window = Window.year(2023)

    def test_no_plays_give_an_empty_aggregate(self):
        """Planted defect: start the plays-seen counter at 1."""
        assert aggregate_albums([], self.window) == AlbumAggregate({}, 0)

    def test_it_counts_plays_and_distinct_tracks_per_album(self):
        """Planted defect: count every play as a new track."""
        day = date(2023, 6, 15)
        plays = [
            _play(_at(day, 12, n), "Radiohead", "OK Computer", title)
            for n, title in enumerate(["Airbag", "Airbag", "Karma Police"])
        ]
        aggregate = aggregate_albums(plays, self.window)
        album = aggregate.albums[normalize_name("Radiohead", "OK Computer")]
        assert album["play_count"] == 3
        assert album["track_counts"] == {
            normalize_track_name("Airbag"): 2,
            normalize_track_name("Karma Police"): 1,
        }
        assert aggregate.plays_seen == 3

    def test_a_play_outside_the_window_is_seen_but_not_counted(self):
        """Planted defect: skip the window filter."""
        inside = _play(datetime(2023, 6, 15, tzinfo=UTC))
        outside = _play(datetime(2022, 12, 31, 23, 59, 59, tzinfo=UTC))
        aggregate = aggregate_albums([inside, outside], self.window)
        assert aggregate.albums[normalize_name("Artist", "Album")]["play_count"] == 1
        assert aggregate.plays_seen == 2

    @pytest.mark.parametrize(
        "names",
        [("", "Album", "Song"), ("Artist", "", "Song"), ("Artist", "Album", "")],
        ids=["no-artist", "no-album", "no-track"],
    )
    def test_a_play_missing_any_of_the_three_names_is_skipped(self, names):
        """An album needs all three names (the heatmap does not). Planted
        defect: drop the guard."""
        artist, album, track = names
        play = _play(datetime(2023, 6, 15, tzinfo=UTC), artist, album, track)
        aggregate = aggregate_albums([play], self.window)
        assert aggregate.albums == {}
        assert aggregate.plays_seen == 1

    def test_spellings_that_normalize_alike_are_one_album_named_by_the_first(self):
        """Planted defect: let the last spelling replace the first."""
        day = date(2023, 6, 15)
        plays = [
            _play(_at(day, 12, 0), "Mitski", "Be The Cowboy", "A"),
            _play(_at(day, 12, 1), "MITSKI", "be the cowboy (Deluxe Edition)", "B"),
        ]
        aggregate = aggregate_albums(plays, self.window)
        assert len(aggregate.albums) == 1
        album = next(iter(aggregate.albums.values()))
        assert album["play_count"] == 2
        assert (album["original_artist"], album["original_album"]) == (
            "Mitski",
            "Be The Cowboy",
        )

    def test_track_titles_that_normalize_alike_are_one_track(self):
        """Planted defect: key tracks by the raw title."""
        day = date(2023, 6, 15)
        plays = [
            _play(_at(day, 12, 0), track="Karma Police"),
            _play(_at(day, 12, 1), track="karma police"),
        ]
        album = next(iter(aggregate_albums(plays, self.window).albums.values()))
        assert len(album["track_counts"]) == 1

    def test_identical_plays_each_count(self):
        """Two listens at the same second are two listens. Planted defect:
        collapse equal plays (iterate ``set(plays)``)."""
        when = datetime(2023, 6, 15, 12, tzinfo=UTC)
        album = next(
            iter(aggregate_albums([_play(when), _play(when)], self.window).albums.values())
        )
        assert album["play_count"] == 2


# ---------------------------------------------------------------------------
# aggregate_daily_counts and zero_fill_daily_counts
# ---------------------------------------------------------------------------


class TestAggregateDailyCounts:
    def test_basic_counting(self):
        """Plays on known dates produce correct per-day counts."""
        plays = [
            _play(_noon(date(2026, 1, 1))),
            _play(_noon(date(2026, 1, 1))),
            _play(_noon(date(2026, 1, 3))),
        ]
        result = aggregate_daily_counts(plays, date(2026, 1, 1), date(2026, 1, 3))
        assert result["2026-01-01"] == 2
        assert result["2026-01-02"] == 0
        assert result["2026-01-03"] == 1

    def test_fills_365_days(self):
        """A 365-day range produces exactly 365 keys (non-leap year span)."""
        from_date, to_date = date(2025, 3, 8), date(2026, 3, 7)
        result = aggregate_daily_counts([], from_date, to_date)
        assert len(result) == (to_date - from_date).days + 1
        assert all(v == 0 for v in result.values())

    def test_fills_366_days_leap_year(self):
        """A range spanning Feb 29 of a leap year produces 366 keys."""
        result = aggregate_daily_counts([], date(2023, 3, 8), date(2024, 3, 7))
        assert len(result) == 366
        assert "2024-02-29" in result

    def test_boundary_timestamps(self):
        """Plays at exactly from_date's first second and to_date's last are included."""
        from_date, to_date = date(2026, 6, 1), date(2026, 6, 2)
        plays = [_play(_at(from_date, 0)), _play(_at(to_date, 23, 59, 59))]
        result = aggregate_daily_counts(plays, from_date, to_date)
        assert result["2026-06-01"] == 1
        assert result["2026-06-02"] == 1

    def test_out_of_range_excluded(self):
        """Plays outside [from_date, to_date] are excluded. Planted defect:
        remove both range limits (the filter and the zero-fill's own bounds),
        so out-of-range days reach the result."""
        from_date, to_date = date(2026, 5, 10), date(2026, 5, 12)
        plays = [
            _play(_at(date(2026, 5, 9), 23, 59, 59)),
            _play(_noon(date(2026, 5, 11))),
            _play(_at(date(2026, 5, 13), 0, 0, 1)),
        ]
        result = aggregate_daily_counts(plays, from_date, to_date)
        assert result["2026-05-11"] == 1
        assert sum(result.values()) == 1

    def test_no_plays_give_all_zeros(self):
        result = aggregate_daily_counts([], date(2026, 1, 1), date(2026, 1, 7))
        assert len(result) == 7
        assert all(v == 0 for v in result.values())

    def test_plays_from_several_pages_are_merged(self):
        """The calculation takes one flat sequence; page boundaries are gone."""
        plays = [
            _play(_noon(date(2026, 2, 1))),
            _play(_noon(date(2026, 2, 1))),
            _play(_noon(date(2026, 2, 2))),
        ]
        result = aggregate_daily_counts(plays, date(2026, 2, 1), date(2026, 2, 2))
        assert result["2026-02-01"] == 2
        assert result["2026-02-02"] == 1

    def test_midnight_boundary_attribution(self):
        """23:59:59 UTC on day D and 00:00:01 UTC on day D+1 land on their own
        days. Planted defect: bucket by the next day's date."""
        d1, d2 = date(2026, 3, 1), date(2026, 3, 2)
        plays = [_play(_at(d1, 23, 59, 59)), _play(_at(d2, 0, 0, 1))]
        result = aggregate_daily_counts(plays, d1, d2)
        assert result["2026-03-01"] == 1
        assert result["2026-03-02"] == 1

    def test_a_play_with_no_names_still_counts(self):
        """The heatmap needs the date only (an album needs all three names).
        Planted defect: skip a play with an empty album, as the album
        calculation does."""
        play = _play(_noon(date(2026, 4, 1)), artist="", album="", track="")
        result = aggregate_daily_counts([play], date(2026, 4, 1), date(2026, 4, 1))
        assert result["2026-04-01"] == 1


class TestZeroFill:
    def test_it_keeps_counts_and_fills_the_gaps(self):
        """Every date in the range is present, counted or zero, both ends
        included. Planted defect: stop the range one day short."""
        result = zero_fill_daily_counts(
            {"2026-01-02": 5}, date(2026, 1, 1), date(2026, 1, 3)
        )
        assert result == {"2026-01-01": 0, "2026-01-02": 5, "2026-01-03": 0}
```

- [ ] **Step 2: Write the failing tests for `lastfm.fetch_scrobbles`**

In `tests/services/test_lastfm_service.py` extend the import block: add `ProviderError` to the `scrobblescope.errors` import, `FetchSummary` and `fetch_scrobbles` to the `scrobblescope.lastfm` import, and add `from datetime import UTC, date, datetime` and `from scrobblescope.plays import Window` with the file's other imports. Append at the end of the file:

```python
# --- fetch_scrobbles: pages in, plays out (Task 23c) ---------------------------


def _scrobble_page(tracks, number=1, total=1):
    return {
        "recenttracks": {
            "@attr": {"page": str(number), "totalPages": str(total)},
            "track": tracks,
        }
    }


def _raw(artist, album, name, uts):
    return {
        "artist": {"#text": artist},
        "album": {"#text": album},
        "name": name,
        "date": {"uts": str(uts)},
    }


async def _scrobbles(pages, meta=None, window=None, progress_cb=None):
    """Run ``fetch_scrobbles`` over ``pages``; return (result, the fetch mock)."""
    meta = meta or {
        "status": "ok",
        "pages_expected": len(pages),
        "pages_received": len(pages),
    }
    with patch(
        "scrobblescope.lastfm.fetch_all_recent_tracks_async",
        new_callable=AsyncMock,
        return_value=(pages, meta),
    ) as fetch:
        result = await fetch_scrobbles(
            "anyone", window or Window.year(2023), progress_cb=progress_cb
        )
    return result, fetch


@pytest.mark.asyncio
async def test_fetch_scrobbles_hands_back_plays_with_utc_timestamps():
    """
    GIVEN a page with one scrobble at 2023-06-15T12:00:00Z
    WHEN fetch_scrobbles runs
    THEN the play carries that moment with tzinfo exactly UTC, and the three names.

    Planted defect: read the artist from the album's key and the album from the
    artist's.
    """
    page = _scrobble_page([_raw("Mitski", "Laurel Hell", "Heat Lightning", 1686830400)])

    result, _ = await _scrobbles([page])

    (play,) = result.plays
    assert play.played_at == datetime(2023, 6, 15, 12, tzinfo=UTC)
    assert play.played_at.tzinfo is UTC
    assert (play.artist, play.album, play.track) == (
        "Mitski",
        "Laurel Hell",
        "Heat Lightning",
    )


@pytest.mark.asyncio
async def test_a_play_at_2330_utc_keeps_its_utc_day():
    """
    GIVEN a scrobble at 23:30 UTC on 2026-04-10
    WHEN fetch_scrobbles runs
    THEN its day is the UTC day, whatever zone the host is in.

    Planted defect: decode the timestamp with the host's local zone. The play
    then has no tzinfo and its constructor refuses it.
    """
    page = _scrobble_page([_raw("A", "B", "C", 1775863800)])

    result, _ = await _scrobbles([page], window=Window.year(2026))

    assert result.plays[0].played_at.date() == date(2026, 4, 10)
    assert result.plays[0].played_at.tzinfo is UTC


@pytest.mark.asyncio
async def test_the_now_playing_entry_is_dropped_and_counted():
    """
    GIVEN a now-playing entry (no date) beside a dated scrobble
    WHEN fetch_scrobbles runs
    THEN one play is returned and one undated entry is counted.

    Planted defect: turn the undated entry into a play.
    """
    now_playing = {"artist": {"#text": "A"}, "album": {"#text": "B"}, "name": "C"}
    page = _scrobble_page([now_playing, _raw("A", "B", "C", 1686830400)])

    result, _ = await _scrobbles([page])

    assert len(result.plays) == 1
    assert (result.dropped_undated, result.dropped_malformed) == (1, 0)


@pytest.mark.asyncio
async def test_an_unreadable_entry_is_dropped_and_counted_not_fatal(caplog):
    """
    GIVEN entries that are not objects, have a non-numeric timestamp, or one too
    large to be a date, beside a good scrobble
    WHEN fetch_scrobbles runs
    THEN the good one is returned, the three bad ones are counted, and the log
    names their count and nothing of their content.

    Planted defect: let the first unreadable entry raise.
    """
    bad_text = _raw("Zqxv Artist", "Zqxv Album", "Zqxv Track", "abc")
    too_big = _raw("Zqxv Artist", "Zqxv Album", "Zqxv Track", "9" * 20)
    page = _scrobble_page(
        ["Zqxv", bad_text, too_big, _raw("A", "B", "C", 1686830400)]
    )

    with caplog.at_level(logging.DEBUG):
        result, _ = await _scrobbles([page])

    assert len(result.plays) == 1
    assert result.dropped_malformed == 3
    assert "3 entries" in caplog.text
    assert "Zqxv" not in caplog.text


@pytest.mark.asyncio
async def test_a_missing_name_becomes_an_empty_string():
    """
    GIVEN an entry with no album object at all
    WHEN fetch_scrobbles runs
    THEN its play has an empty album: the aggregators decide what an empty name
    means, the border does not invent one.

    Planted defect: default a missing album to "...".
    """
    entry = {"artist": {"#text": "A"}, "name": "C", "date": {"uts": "1686830400"}}

    result, _ = await _scrobbles([_scrobble_page([entry])])

    assert result.plays[0].album == ""


@pytest.mark.asyncio
async def test_plays_leave_in_page_order_whatever_order_the_pages_arrive():
    """
    GIVEN page 2 arrives before page 1
    WHEN fetch_scrobbles runs
    THEN the plays are ordered by page number, so "first seen" does not depend
    on which page the network answered first.

    Planted defect: keep arrival order.
    """
    first = _scrobble_page([_raw("A", "B", "one", 1686830400)], number=1, total=2)
    second = _scrobble_page([_raw("A", "B", "two", 1686830401)], number=2, total=2)

    result, _ = await _scrobbles([second, first])

    assert [play.track for play in result.plays] == ["one", "two"]


@pytest.mark.asyncio
async def test_the_summary_reports_dropped_pages():
    """
    GIVEN a fetch that read 3 of 5 pages
    WHEN fetch_scrobbles runs
    THEN the summary is partial with two pages dropped and 40 percent lost.

    Planted defect: compute the loss percentage against the pages received
    instead of the pages expected.
    """
    meta = {
        "status": "partial",
        "pages_expected": 5,
        "pages_received": 3,
        "pages_dropped": 2,
    }
    pages = [_scrobble_page([], n, 5) for n in (1, 2, 3)]

    result, _ = await _scrobbles(pages, meta)

    assert result.summary == FetchSummary(pages_expected=5, pages_received=3)
    assert result.summary.partial is True
    assert result.summary.pages_dropped == 2
    assert result.summary.data_loss_pct == 40


@pytest.mark.asyncio
async def test_metadata_without_page_counts_is_a_complete_fetch():
    """
    GIVEN metadata that carries only a status
    WHEN fetch_scrobbles runs
    THEN the summary is not partial and computing its loss does not divide by zero.

    Planted defect: divide by pages_expected without a guard.
    """
    result, _ = await _scrobbles([_scrobble_page([])], meta={"status": "ok"})

    assert result.summary.partial is False
    assert result.summary.pages_dropped == 0
    assert result.summary.data_loss_pct == 0


@pytest.mark.asyncio
async def test_an_unusable_first_page_raises_the_typed_unavailable_failure():
    """
    GIVEN the page layer reports that page 1 never answered
    WHEN fetch_scrobbles runs
    THEN it raises the typed Last.fm-unavailable failure, which classifies as
    lastfm_unavailable and names no username.

    Planted defect: return an empty fetch instead of raising.
    """
    meta = {"status": "error", "reason": "lastfm_unavailable"}

    with pytest.raises(ProviderError) as excinfo:
        await _scrobbles([], meta)

    assert classify_exception_to_error_code(excinfo.value) == "lastfm_unavailable"
    assert "anyone" not in str(excinfo.value)


@pytest.mark.asyncio
async def test_fetch_scrobbles_passes_the_window_and_callback_through():
    """
    GIVEN a year window and a progress callback
    WHEN fetch_scrobbles runs
    THEN the page layer is asked for that window's epoch bounds with the very
    same callback.

    Planted defect: drop the progress callback from the page-layer call.
    """
    callback = MagicMock()

    _, fetch = await _scrobbles(
        [_scrobble_page([])], window=Window.year(2024), progress_cb=callback
    )

    fetch.assert_awaited_once_with("anyone", 1704067200, 1735689599, progress_cb=callback)


@pytest.mark.asyncio
async def test_fetch_scrobbles_logs_no_listening_facts(caplog):
    """
    GIVEN pages whose names are distinctive markers, with a dropped entry
    WHEN fetch_scrobbles runs at DEBUG
    THEN no marker reaches any log record.

    Planted defect: log each play it builds (its names) at DEBUG.
    """
    page = _scrobble_page(
        [_raw("Zqxv Artist", "Zqxv Album", "Zqxv Track", 1686830400), "Zqxv"]
    )

    with caplog.at_level(logging.DEBUG):
        await _scrobbles([page])

    assert "Zqxv" not in caplog.text
```

`logging`, `AsyncMock`, `MagicMock`, `patch` and `classify_exception_to_error_code` are already imported by this file.

- [ ] **Step 3: Run both; they fail on missing names**

Run: `"$PY" -m pytest tests/test_plays.py tests/services/test_lastfm_service.py -q -p no:cacheprovider`
Expected: collection errors (`ModuleNotFoundError: scrobblescope.plays`, `ImportError: fetch_scrobbles`).

- [ ] **Step 4: Create `scrobblescope/plays.py`**

```python
"""Normalized listening facts and the pure calculations over them.

A ``Play`` is one listen, however its source reported it: when, and the artist,
album and track names. Last.fm scrobbles become plays inside ``lastfm.py``;
Batch 23's Spotify export parser emits the same record. Everything downstream
(the album calculation, the heatmap) reads plays and never the shape of a
provider's payload (Global Rule 4).

A ``Play`` carries nothing else, so it cannot carry listener identity: no
username, IP address, user agent, country or platform (``BATCH23_DEFINITION.md``
"Data handling"). Rules that belong to one source -- Last.fm's now-playing
entry, the export's 30-second and private-session rules -- are applied by that
source's own module before a ``Play`` exists, never here.

    plays <- domain
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TypedDict

from scrobblescope.domain import normalize_name, normalize_track_name

#: An album's identity: ``domain.normalize_name(artist, album)``.
AlbumKey = tuple[str, str]


@dataclass(frozen=True, slots=True)
class Play:
    """One listen. ``played_at`` is UTC to the second; a name is ``""`` when
    the source gave none."""

    played_at: datetime
    artist: str
    album: str
    track: str

    def __post_init__(self):
        """Refuse any timestamp whose ``tzinfo`` is not exactly ``datetime.UTC``.

        A naive datetime would be read as local time by ``.timestamp()`` and
        attribute a listen to the wrong day on a host that is not UTC; a source
        that forgot to convert fails here, at the border.
        """
        if self.played_at.tzinfo is not UTC:
            raise ValueError("Play.played_at must be a datetime with tzinfo UTC")


@dataclass(frozen=True, slots=True)
class Window:
    """A span of time, inclusive at both ends, both bounds UTC."""

    start: datetime
    end: datetime

    def __post_init__(self):
        """Refuse a bound that is not UTC and a window that ends before it starts."""
        for bound in (self.start, self.end):
            if bound.tzinfo is not UTC:
                raise ValueError("Window bounds must be datetimes with tzinfo UTC")
        if self.start > self.end:
            raise ValueError("Window.start must not be after Window.end")

    @classmethod
    def year(cls, year: int) -> "Window":
        """Return January 1 00:00:00 to December 31 23:59:59 of *year*, UTC."""
        return cls(
            start=datetime(year, 1, 1, tzinfo=UTC),
            end=datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC),
        )

    def start_ts(self) -> int:
        """Return the start as epoch seconds, the form the Last.fm API takes."""
        return int(self.start.timestamp())

    def end_ts(self) -> int:
        """Return the end as epoch seconds, the form the Last.fm API takes."""
        return int(self.end.timestamp())

    def contains(self, played_at: datetime) -> bool:
        """Return whether *played_at* lies in the window, ends included."""
        return self.start <= played_at <= self.end


class AlbumTally(TypedDict):
    """What the album calculation knows about one album.

    A ``TypedDict`` on purpose: it is named and typed, but still a plain dict
    at runtime, so ``partition_albums_by_threshold``, ``_apply_pre_slice``,
    ``_build_results`` and the Deezer fallback read it unchanged.
    """

    play_count: int
    track_counts: dict[str, int]
    original_artist: str
    original_album: str


@dataclass(frozen=True, slots=True)
class AlbumAggregate:
    """Every album found in a window, before any threshold is applied.

    ``plays_seen`` counts the plays offered, including those outside the window
    and those too incomplete to be an album play, so a job's scrobble total
    matches what the source returned.
    """

    albums: dict[AlbumKey, AlbumTally]
    plays_seen: int


def aggregate_albums(plays: Iterable[Play], window: Window) -> AlbumAggregate:
    """Group the plays inside *window* into albums.

    A play with an empty artist, album or track name is not an album play (the
    heatmap, which needs only the date, still counts it). Albums are keyed by
    ``normalize_name``; the first spelling seen names the album, and tracks are
    keyed by ``normalize_track_name`` so spellings that normalize alike are one
    track. Pure: no I/O, no clock.
    """
    albums: dict[AlbumKey, AlbumTally] = {}
    seen = 0
    for play in plays:
        seen += 1
        if not window.contains(play.played_at):
            continue
        if not (play.artist and play.album and play.track):
            continue
        key = normalize_name(play.artist, play.album)
        tally = albums.get(key)
        if tally is None:
            tally = albums[key] = {
                "play_count": 0,
                "track_counts": {},
                "original_artist": play.artist,
                "original_album": play.album,
            }
        tally["play_count"] += 1
        track = normalize_track_name(play.track)
        tally["track_counts"][track] = tally["track_counts"].get(track, 0) + 1
    return AlbumAggregate(albums=albums, plays_seen=seen)


def zero_fill_daily_counts(counts, from_date: date, to_date: date) -> dict[str, int]:
    """Fill every calendar date in ``[from_date, to_date]`` with 0 where missing.

    Args:
        counts: Mapping of ``"YYYY-MM-DD"`` strings to integer counts for dates that had at least one play.
        from_date: Inclusive start date.
        to_date: Inclusive end date.

    Returns:
        A new dict with every ISO date in the range present, each mapped to
        ``counts.get(key, 0)``.
    """
    daily_counts = {}
    current = from_date
    while current <= to_date:
        key = current.isoformat()
        daily_counts[key] = counts.get(key, 0)
        current += timedelta(days=1)
    return daily_counts


def aggregate_daily_counts(
    plays: Iterable[Play], from_date: date, to_date: date
) -> dict[str, int]:
    """Count plays per UTC calendar day over ``[from_date, to_date]``.

    Every date in the range is present; a day with no plays maps to ``0``. A
    play's day is read straight from its UTC timestamp. Plays outside the range
    are ignored. The names on a play are not consulted: the heatmap counts every
    dated listen. Pure: no I/O, no clock.
    """
    counts: dict[str, int] = {}
    for play in plays:
        day = play.played_at.date()
        if from_date <= day <= to_date:
            key = day.isoformat()
            counts[key] = counts.get(key, 0) + 1
    return zero_fill_daily_counts(counts, from_date, to_date)
```

- [ ] **Step 5: Add `fetch_scrobbles` to `lastfm.py`**

Imports: add `from dataclasses import dataclass`, change `from scrobblescope.errors import PrivateProfileError, UserNotFoundError` to also import `ProviderError`, and add `from scrobblescope.plays import Play, Window` after the `scrobblescope.errors` import. Keep the file's existing datetime import and spelling (`from datetime import UTC, datetime` after PR #2). Append after `fetch_all_recent_tracks_async`:

```python
@dataclass(frozen=True, slots=True)
class FetchSummary:
    """How complete a fetch was: the pages Last.fm reported and the pages read."""

    pages_expected: int
    pages_received: int

    @property
    def pages_dropped(self) -> int:
        """Return how many pages never arrived."""
        return max(0, self.pages_expected - self.pages_received)

    @property
    def partial(self) -> bool:
        """Return whether any page was lost."""
        return self.pages_received < self.pages_expected

    @property
    def data_loss_pct(self) -> int:
        """Return the share of pages lost, as a whole percent (0 when none expected)."""
        if self.pages_expected == 0:
            return 0
        return round((self.pages_dropped / self.pages_expected) * 100)


@dataclass(frozen=True, slots=True)
class ScrobbleFetch:
    """The scrobbles of one user in one window, with how complete they are.

    ``dropped_undated`` counts entries with no date (the now-playing entry);
    ``dropped_malformed`` counts entries that could not be read. Neither is
    ever logged by content.
    """

    plays: tuple[Play, ...]
    summary: FetchSummary
    dropped_undated: int
    dropped_malformed: int


def _page_number(page: Any) -> int:
    """Return the page's own number, or 0 when it carries none.

    Pages are sorted by this so the plays leave in page order, not in the order
    the network happened to answer; a stable sort leaves unnumbered pages as
    received.
    """
    try:
        return int(page["recenttracks"]["@attr"]["page"])
    except (KeyError, TypeError, ValueError):
        return 0


def _name_of(entry: dict, key: str) -> str:
    """Return the ``#text`` of an entry's artist or album object, or ``""``."""
    value = entry.get(key)
    text = value.get("#text") if isinstance(value, dict) else None
    return text if isinstance(text, str) else ""


def _plays_from_pages(pages: list) -> tuple[list[Play], int, int]:
    """Turn well-formed Last.fm pages into plays; count the entries that cannot be.

    Returns ``(plays, dropped_undated, dropped_malformed)``. The date comes from
    ``date.uts`` decoded as UTC, never from ``date["#text"]``, which is
    locale-dependent. Nothing but the timestamp and the three names is kept:
    no mbid, image, url or username ever leaves this function.
    """
    plays: list[Play] = []
    undated = 0
    malformed = 0
    for page in sorted(pages, key=_page_number):
        for entry in page.get("recenttracks", {}).get("track", []):
            if not isinstance(entry, dict):
                malformed += 1
                continue
            date_field = entry.get("date")
            uts = date_field.get("uts") if isinstance(date_field, dict) else None
            if not uts:
                undated += 1
                continue
            try:
                played_at = datetime.fromtimestamp(int(uts), tz=UTC)
            except (TypeError, ValueError, OverflowError, OSError):
                malformed += 1
                continue
            name = entry.get("name")
            plays.append(
                Play(
                    played_at=played_at,
                    artist=_name_of(entry, "artist"),
                    album=_name_of(entry, "album"),
                    track=name if isinstance(name, str) else "",
                )
            )
    return plays, undated, malformed


async def fetch_scrobbles(username, window: Window, progress_cb=None) -> ScrobbleFetch:
    """Return the scrobbles of *username* inside *window* as normalized plays.

    Pagination, retries, the page cache and every Last.fm quirk stay behind this
    function; raw pages never leave it. ``progress_cb(pages_done, pages_expected,
    pages_received)`` is passed to the page fan-out untouched.

    Raises the typed failures the page layer raises (``UserNotFoundError``,
    ``PrivateProfileError``) and, when page 1 never answered,
    ``ProviderError("lastfm", "unavailable")``. A total failure is an exception,
    never a status value. Partial data is a value, not an exception: see
    ``ScrobbleFetch.summary``. No message names the user or any page content.
    """
    pages, meta = await fetch_all_recent_tracks_async(
        username, window.start_ts(), window.end_ts(), progress_cb=progress_cb
    )
    if meta.get("status") == "error":
        raise ProviderError("lastfm", "unavailable")
    plays, undated, malformed = _plays_from_pages(pages)
    if malformed:
        logging.warning(f"Last.fm: {malformed} entries could not be read and were skipped")
    summary = FetchSummary(
        pages_expected=meta.get("pages_expected", 0),
        pages_received=meta.get("pages_received", len(pages)),
    )
    return ScrobbleFetch(tuple(plays), summary, undated, malformed)
```

- [ ] **Step 6: The heatmap consumes plays**

In `scrobblescope/heatmap.py`:

1. Module docstring: replace `(\`\`lastfm.fetch_all_recent_tracks_async\`\`)` with `(\`\`lastfm.fetch_scrobbles\`\`)` and the dependency chain with `heatmap <- errors, jobs, lastfm, plays, utils, worker`.
2. Imports: remove `from collections import Counter` and `from scrobblescope.lastfm import fetch_all_recent_tracks_async`; add `from scrobblescope.lastfm import fetch_scrobbles` and `from scrobblescope.plays import Window, aggregate_daily_counts`.
3. Delete `_zero_fill_daily_counts` and `_aggregate_daily_counts` (both moved to `plays.py`).
4. In `_fetch_and_process_heatmap`, replace the window computation, the fetch, the status handling and the aggregation call so that the function from `now = ...` to the `total = ...` line reads:

```python
    now = datetime.now(UTC)
    to_date = now.date()
    # Minus one because both ends are inclusive. Written as arithmetic rather
    # than as a literal 364, which read as a different number from every other
    # copy of the window and could not be checked against them.
    from_date = to_date - timedelta(days=HEATMAP_WINDOW_DAYS - 1)
    window = Window(start=datetime.combine(from_date, dt_time.min, tzinfo=UTC), end=now)

    # Phase 5-80%: fetch Last.fm scrobbles -------------------------------------
    def _heatmap_progress(pages_done, total_pages, pages_received):
        """Report page-fetching progress inside the heatmap's fetch band."""
        jobs.record_stat(job_id, "pages_received", pages_received)
        jobs.record_stat(job_id, "pages_expected", total_pages)
        jobs.report_phase(
            job_id,
            jobs.HEATMAP_LASTFM_FETCH,
            pages_done,
            total_pages,
            "Reading your Last.fm history...",
        )

    jobs.advance(job_id, 5, "Fetching your scrobble history from Last.fm...")

    fetch_start = time.time()
    fetch = await fetch_scrobbles(username, window, progress_cb=_heatmap_progress)
    fetch_elapsed = time.time() - fetch_start
    logging.info(f"Heatmap Last.fm fetch for job {job_id}: {fetch_elapsed:.1f}s")

    # Record fetch stats for observability. A total Last.fm failure never gets
    # here: fetch_scrobbles raises, and heatmap_task's backstop classifies it.
    summary = fetch.summary
    jobs.record_stat(job_id, "pages_expected", summary.pages_expected)
    jobs.record_stat(job_id, "pages_received", summary.pages_received)

    # Partial data handling: some pages failed but we got partial data.
    if summary.partial:
        jobs.record_stat(
            job_id,
            "partial_data_warning",
            f"Note: {summary.pages_dropped} of {summary.pages_expected} Last.fm "
            f"pages failed ({summary.data_loss_pct}% data loss). "
            "Heatmap may be incomplete.",
        )

    # Phase 80-90%: aggregate daily counts ------------------------------------
    jobs.advance(job_id, 80, "Counting your daily scrobbles...")
    daily_counts = aggregate_daily_counts(fetch.plays, from_date, to_date)

    total = sum(daily_counts.values())
```

   (Everything after `total = ...` is unchanged.) In the function's docstring replace "On upstream errors or zero scrobbles the job terminates early with a classified error via ``jobs.fail``." with "A total Last.fm failure raises out of this function and is classified by ``heatmap_task``'s backstop; zero scrobbles in range ends the job with ``no_scrobbles_in_range`` via ``jobs.fail``."
5. In `_report_heatmap_failure`'s docstring delete the last sentence ("The inner, status-based Last.fm path inside ``_fetch_and_process_heatmap`` still publishes its own code.") -- there is no inner path any more; a Last.fm outage reaches this function as a ``ProviderError`` and is classified like any other typed failure.

- [ ] **Step 7: The album pipeline consumes plays**

In `scrobblescope/orchestrator/__init__.py`:

1. Imports: replace `from scrobblescope.lastfm import fetch_all_recent_tracks_async` with `from scrobblescope.lastfm import fetch_scrobbles`; add `from scrobblescope.plays import Window, aggregate_albums` after it; delete `from scrobblescope.domain import normalize_name, normalize_track_name`; then delete by hand the imports nothing uses now -- `from collections import defaultdict`, the `from datetime import ...` line and `from typing import Any` -- and confirm with `"$RUFF" check --select F scrobblescope/orchestrator/__init__.py` (ruff reports an unused import in an `__init__.py` but does not remove it).
2. Replace the whole `fetch_top_albums_async` function with:

```python
async def fetch_top_albums_async(
    username, year, min_plays=10, min_tracks=3, progress_cb=None
):
    """Fetch and partition top albums by the configured listening thresholds.

    Returns an ``(eligible_albums, threshold_exclusions, fetch_metadata)``
    tuple. Threshold exclusions retain report facts but never enter Spotify
    enrichment. Last.fm is read as plays (``lastfm.fetch_scrobbles``) and
    grouped by ``plays.aggregate_albums``; a total Last.fm failure raises.

    The returned ``fetch_metadata`` dict includes a ``stats`` key with
    aggregation counters (total_scrobbles, pages_fetched, unique_albums,
    albums_passing_filter, albums_below_threshold) so the caller can record
    them as job stats. Task 23d replaces this tuple with a typed selection.

    Args:
        progress_cb: Optional ``Callable[[int, int, int], None]`` forwarded to
            ``fetch_scrobbles`` for per-page progress.
    """
    logging.debug(f"Start fetch_top_albums_async(year={year})")
    window = Window.year(year)
    fetch = await fetch_scrobbles(username, window, progress_cb=progress_cb)
    aggregate = aggregate_albums(fetch.plays, window)

    filtered, threshold_exclusions = partition_albums_by_threshold(
        aggregate.albums, min_plays, min_tracks
    )
    total_below_threshold = len(threshold_exclusions)
    threshold_exclusions = _cap_threshold_exclusions(threshold_exclusions)

    summary = fetch.summary
    fetch_metadata: dict = {
        "status": "partial" if summary.partial else "ok",
        "pages_expected": summary.pages_expected,
        "pages_received": summary.pages_received,
        "stats": {
            "total_scrobbles": aggregate.plays_seen,
            "pages_fetched": summary.pages_received,
            "unique_albums": len(aggregate.albums),
            "albums_passing_filter": len(filtered),
            "albums_below_threshold": total_below_threshold,
        },
    }
    if summary.partial:
        fetch_metadata["pages_dropped"] = summary.pages_dropped
        fetch_metadata["partial_data_warning"] = (
            f"Note: {summary.pages_dropped} of {summary.pages_expected} Last.fm "
            f"pages failed to load ({summary.data_loss_pct}% data loss). "
            "Results may be incomplete."
        )
    return filtered, threshold_exclusions, fetch_metadata
```

3. In `_fetch_job_albums` delete the block

```python
    # Upstream failure: Last.fm was unreachable
    if fetch_metadata.get("status") == "error":
        jobs.fail(
            job_id,
            fetch_metadata.get("reason", "lastfm_unavailable"),
            username=username,
        )
        return None
```

   and change its docstring's first line to "Fetch Last.fm albums and finish an empty job in place." A total Last.fm failure now raises out of `fetch_top_albums_async` into `_fetch_and_process`'s handler, which classifies it.
4. In `__all__` replace `"fetch_all_recent_tracks_async",` with `"fetch_scrobbles",` (before `"fetch_spotify_access_token"`).

- [ ] **Step 8: Edit the existing tests**

Every edit below is named in the commit body.

1. `tests/services/test_lastfm_logic.py` (9 patch strings, 1 target): `sed -i 's/scrobblescope\.orchestrator\.fetch_all_recent_tracks_async/scrobblescope.lastfm.fetch_all_recent_tracks_async/' tests/services/test_lastfm_logic.py`, then in `test_fetch_top_albums_uses_utc_year_window_on_non_utc_host` change `patch("scrobblescope.orchestrator.datetime", new=utc_minus_five_datetime)` to `patch("scrobblescope.plays.datetime", new=utc_minus_five_datetime)`. Its `assert_awaited_once_with("testuser", 1704067200, 1735689599, progress_cb=None)` is unchanged.
2. `tests/test_pipeline_integration.py`: change `patch(o + "fetch_all_recent_tracks_async", ...)` to `patch("scrobblescope.lastfm.fetch_all_recent_tracks_async", ...)` (keep its arguments).
3. `tests/test_provider_fixtures.py`: replace `test_lastfm_fixture_flows_through_aggregate_daily_counts` with

```python
@pytest.mark.asyncio
async def test_lastfm_fixture_flows_through_scrobbles_into_daily_counts():
    """Runs the fixture through the real normalizer and the heatmap's real
    aggregator: `date.uts` is what a play's timestamp comes from, so a fixture
    that drops or renames it fails here, not just in a hand-written field
    check.

    Planted defect: read the date from ``date["#text"]`` (a locale-dependent
    string the fixture carries) instead of ``date["uts"]``."""
    from scrobblescope.lastfm import fetch_scrobbles
    from scrobblescope.plays import Window, aggregate_daily_counts

    page = _load("lastfm_recenttracks_page.json")
    meta = {"status": "ok", "pages_expected": 1, "pages_received": 1}

    with patch(
        "scrobblescope.lastfm.fetch_all_recent_tracks_async",
        new_callable=AsyncMock,
        return_value=([page], meta),
    ):
        fetch = await fetch_scrobbles("RJ", Window.year(2008))

    counts = aggregate_daily_counts(fetch.plays, date(2008, 6, 9), date(2008, 6, 9))

    assert counts == {"2008-06-09": 1}
```

   and in `test_lastfm_fixture_flows_through_fetch_top_albums` change the patch target `"scrobblescope.orchestrator.fetch_all_recent_tracks_async"` to `"scrobblescope.lastfm.fetch_all_recent_tracks_async"`.
4. `tests/services/test_orchestrator_fetch_and_process.py`, `test_fetch_and_process_discards_exclusions_on_lastfm_error`: delete the `threshold_item` dict and replace the `return_value=(...)` argument of the `fetch_top_albums_async` patch with `side_effect=ProviderError("lastfm", "unavailable")`. The assertions are unchanged (a raised outage publishes no unmatched report). `ProviderError` is already imported in that file.
5. `tests/test_heatmap.py`:
   - Module docstring: replace "``_aggregate_daily_counts``: pure function with mock page data, ..." bullet with "``plays.aggregate_daily_counts`` is tested in ``tests/test_plays.py``."
   - Imports: remove `_aggregate_daily_counts` from the `scrobblescope.heatmap` import; extend `from scrobblescope.errors import UserNotFoundError` to `ProviderError, UserNotFoundError`; add `from scrobblescope.lastfm import FetchSummary, ScrobbleFetch` and `from scrobblescope.plays import Play`.
   - Replace the helpers `_make_track` and `_wrap_tracks` with:

```python
def _play(day):
    """A play at noon UTC on ``day`` (a ``datetime.date``)."""
    return Play(
        played_at=datetime.combine(day, dt_time(12, 0), tzinfo=UTC),
        artist="Artist",
        album="Album",
        track="Song",
    )


def _fetch(plays, expected=1, received=1):
    """What ``fetch_scrobbles`` returns for ``plays`` read from ``received`` of
    ``expected`` pages."""
    return ScrobbleFetch(tuple(plays), FetchSummary(expected, received), 0, 0)
```

   (use the file's datetime spelling for UTC after PR #2: `UTC`, imported from `datetime`).
   - Delete `class TestAggregateDailyCounts` and the section banner above it: its ten tests live in `tests/test_plays.py` (eight converted there beside one new test, `test_a_play_with_no_names_still_counts`; `test_now_playing_skipped` became `test_the_now_playing_entry_is_dropped_and_counted`, and `test_utc_decode_invariant_against_local_tz_drift` became `test_a_play_at_2330_utc_keeps_its_utc_day`, both in `tests/services/test_lastfm_service.py`).
   - In `TestFetchAndProcessHeatmap` and `TestHeatmapPhaseProgress` change each patch of `"scrobblescope.heatmap.fetch_all_recent_tracks_async"` to `"scrobblescope.heatmap.fetch_scrobbles"` and its data as follows:

| Test | Old data | New data |
|---|---|---|
| `test_partial_data_stores_warning_and_continues` | `page = _wrap_tracks([_make_track(track_date)])`, `meta = {partial, 10, 8, 2}`, `return_value=([page], meta)` | `return_value=_fetch([_play(track_date)], expected=10, received=8)`; delete `page` and `meta` |
| `test_partial_data_with_zero_scrobbles_fires_error` | `meta = {partial, 5, 2, 3}`, `return_value=([], meta)` | `return_value=_fetch([], expected=5, received=2)` |
| `test_zero_scrobbles_fires_no_scrobbles_error` | `meta = {ok, 1, 1}`, `return_value=([], meta)` | `return_value=_fetch([])` |
| `test_happy_path_stores_correct_result_dict` | three `_make_track` in a page, `meta` | `return_value=_fetch([_play(yesterday), _play(yesterday), _play(today)])` |
| `test_success_is_readable_through_repository_at_100_percent` | `page`, `metadata`, `return_value=([page], metadata)` | `return_value=_fetch([_play(today)])` |
| `test_progress_callback_sends_correct_percentages` | `_fetch_with_progress` returns `[page], meta` | it returns `_fetch([_play(today)])` |
| `test_heatmap_lastfm_phase_and_cleared_at_completion` | `fake_fetch(username, from_ts, to_ts, progress_cb=None)` returns `[page], meta` with 102 pages expected, 23 received | `fake_fetch(username, window, progress_cb=None)` returns `_fetch([_play(today)], expected=102, received=23)` |

   - Replace `test_upstream_error_sets_job_error` with a test that the failure now propagates to the backstop, and add the backstop's answer:

```python
    @pytest.mark.asyncio
    async def test_a_total_lastfm_failure_propagates_to_the_backstop(self):
        """A total Last.fm failure is an exception now: the pipeline neither
        swallows it nor publishes a terminal state itself.

        Planted defect: catch the provider failure in the pipeline and publish
        lastfm_unavailable from there."""
        with (
            patch("scrobblescope.heatmap.cleanup_expired_cache"),
            patch("scrobblescope.jobs.expire_stale"),
            patch("scrobblescope.jobs.start"),
            patch("scrobblescope.jobs.advance"),
            patch("scrobblescope.jobs.record_stat"),
            patch(
                "scrobblescope.heatmap.fetch_scrobbles",
                new_callable=AsyncMock,
                side_effect=ProviderError("lastfm", "unavailable"),
            ),
            patch("scrobblescope.jobs.fail") as mock_set_error,
            patch("scrobblescope.jobs.succeed") as mock_set_results,
        ):
            with pytest.raises(ProviderError):
                await _fetch_and_process_heatmap("job-1", "testuser")
            mock_set_error.assert_not_called()
            mock_set_results.assert_not_called()
```

   and in `TestHeatmapTask`, after `test_user_not_found_crash_publishes_user_not_found`:

```python
    def test_lastfm_outage_crash_publishes_lastfm_unavailable(self):
        """A Last.fm outage escaping the pipeline is classified by type as
        lastfm_unavailable: retryable, blamed on Last.fm.

        Planted defect: classify every escaped exception as internal_error.
        The thread entry point takes the job id alone (PR #3): the username is
        read from the job record."""
        job_id = jobs.create({"username": "user", "mode": "heatmap"})
        with (
            patch("scrobblescope.heatmap.release_job_slot"),
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
                side_effect=ProviderError("lastfm", "unavailable"),
            ),
        ):
            heatmap_task(job_id)

        progress = jobs.progress(job_id)
        assert progress["error_code"] == "lastfm_unavailable"
        assert progress["error_source"] == "lastfm"
        assert progress["retryable"] is True
```

   - Check: `"$PY" -m pytest tests/test_heatmap.py -q -p no:cacheprovider` passes, and `git grep -n "_make_track\|_wrap_tracks\|_aggregate_daily_counts" -- tests` is empty.
6. `tests/test_lastfm_job_results.py`: delete the five `@pytest.mark.xfail(strict=True, ...)` decorators (`test_the_scrobble_total_counts_completed_scrobbles_only`, `test_an_entry_with_no_album_field_is_not_an_album_play`, `test_a_failed_lastfm_job_records_no_listening_stats`, and the two `test_one_unreadable_timestamp_does_not_fail_the_*`). No assertion changes.

Then: `git grep -n "orchestrator\.\(datetime\|timezone\|normalize_name\|normalize_track_name\|defaultdict\|fetch_all_recent_tracks_async\)" -- tests scrobblescope` is empty, and `"$RUFF" check scrobblescope tests && "$RUFF" format scrobblescope tests` is clean.

- [ ] **Step 9: Add the page-layer rule to the boundary guard**

Append to `tests/test_module_boundaries.py`:

```python
PAGE_LAYER = {"fetch_recent_tracks_page_async", "fetch_all_recent_tracks_async"}


def test_nothing_outside_lastfm_reads_the_page_layer():
    """
    GIVEN every module under scrobblescope/ except lastfm.py
    WHEN its imports and attribute reads are walked
    THEN none names the Last.fm page functions: callers get plays from
    ``lastfm.fetch_scrobbles`` and raw pages never leave the module.

    Planted defect: add ``from scrobblescope.lastfm import
    fetch_all_recent_tracks_async`` to ``heatmap.py``.
    """
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        module = _module_name(path)
        if module == "scrobblescope.lastfm":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module == (
                "scrobblescope.lastfm"
            ):
                offenders += [
                    f"{module}: imports {item.name}"
                    for item in node.names
                    if item.name in PAGE_LAYER
                ]
            if isinstance(node, ast.Attribute) and node.attr in PAGE_LAYER:
                offenders.append(f"{module}: reads .{node.attr}")
    assert offenders == []
```

- [ ] **Step 10: Run the suites**

Run: `"$PY" -m pytest tests/test_plays.py tests/services/test_lastfm_service.py tests/test_lastfm_job_results.py tests/test_heatmap.py tests/services/test_lastfm_logic.py tests/test_module_boundaries.py tests/test_log_privacy.py -q -p no:cacheprovider`
Expected: all pass, no xfail left. `tests/test_lastfm_job_results.py` reports `23 passed`: the Task 1 suite is the parity proof, and apart from the five removed markers it is byte-for-byte what Task 1 committed (`git diff HEAD -- tests/test_lastfm_job_results.py` shows only those deletions).
Run: `"$PY" -m pytest -q -p no:cacheprovider`
Expected: every test passes.

- [ ] **Step 11: Mutation evidence**

| # | File and plant | Test that must fail |
|---|---|---|
| 1 | `plays.py`: in `Play.__post_init__` change `is not UTC` to `is UTC` (UTC becomes the zone refused) | `TestPlay::test_a_utc_play_keeps_its_fields`, and the two refusal tests (a naive or foreign-zone play is then accepted) |
| 2 | `plays.py`: in `Play.__post_init__` change `is not UTC` to `is None` | `TestPlay::test_a_play_refuses_a_timestamp_in_another_zone` (the naive case still raises) |
| 3 | `plays.py`: delete the `for bound in (self.start, self.end):` check in `Window.__post_init__` | `TestWindow::test_a_window_refuses_a_naive_bound` (the comparison then raises `TypeError`, not `ValueError`) |
| 4 | `plays.py`: delete the `if self.start > self.end:` check | `TestWindow::test_a_window_refuses_a_reversed_span` |
| 5 | `plays.py`: `end_ts` returns `int(self.end.timestamp()) + 1` | `TestWindow::test_a_year_window_covers_the_calendar_year_in_epoch_seconds` and the UTC-window test in `test_lastfm_logic.py` |
| 6 | `plays.py`: `contains` uses `< self.end` | `TestWindow::test_contains_is_inclusive_at_both_ends` |
| 7 | `plays.py`: in `aggregate_albums` start `seen = 0` as `seen = 1` | `test_no_plays_give_an_empty_aggregate` (it expects `plays_seen == 0`) |
| 8 | `plays.py`: in `aggregate_albums` key tracks by `f"{normalize_track_name(play.track)}#{seen}"` | `test_it_counts_plays_and_distinct_tracks_per_album` (three keys, not two) |
| 9 | `plays.py`: delete the `window.contains` skip in `aggregate_albums` | `test_a_play_outside_the_window_is_seen_but_not_counted` and Task 1's `test_scrobbles_outside_the_year_are_not_counted` |
| 10 | `plays.py`: delete the `if not (play.artist and play.album and play.track)` skip | the three `test_a_play_missing_any_of_the_three_names_is_skipped` cases |
| 11 | `plays.py`: after `tally = albums.get(key)` add `if tally is not None: tally["original_artist"], tally["original_album"] = play.artist, play.album` | `test_spellings_that_normalize_alike_are_one_album_named_by_the_first` and Task 1's `test_the_first_casing_seen_names_the_album` |
| 12 | `plays.py`: `track = normalize_track_name(play.track)` becomes `track = play.track` | `test_track_titles_that_normalize_alike_are_one_track` ("Karma Police" and "karma police" are then two) |
| 13 | `plays.py`: `for play in plays:` in `aggregate_albums` becomes `for play in set(plays):` | `test_identical_plays_each_count` (two equal frozen plays collapse to one) |
| 14 | `plays.py`: in `aggregate_daily_counts` change `if from_date <= day <= to_date:` to `if True:` AND the final return to `return {**zero_fill_daily_counts(counts, from_date, to_date), **counts}` (either limit alone is masked by the other, so both go) | `TestAggregateDailyCounts::test_out_of_range_excluded` |
| 15 | `plays.py`: in `aggregate_daily_counts` add `if not play.album: continue` after `day = play.played_at.date()` | `TestAggregateDailyCounts::test_a_play_with_no_names_still_counts` |
| 16 | `plays.py`: in `zero_fill_daily_counts` change `while current <= to_date:` to `while current < to_date:` | `TestZeroFill::test_it_keeps_counts_and_fills_the_gaps` (the last day is missing), and `test_boundary_timestamps` |
| 17 | `lastfm.py`: in `_plays_from_pages` remove the `continue` after `undated += 1` (the entry then also counts as malformed) | `test_the_now_playing_entry_is_dropped_and_counted` (it expects `(1, 0)`) |
| 18 | `lastfm.py`: `datetime.fromtimestamp(int(uts))` with no `tz` | `test_a_play_at_2330_utc_keeps_its_utc_day` and Task 1's pipeline tests (`Play` refuses the naive value) |
| 19 | `lastfm.py`: iterate `pages` instead of `sorted(pages, key=_page_number)` | `test_plays_leave_in_page_order_whatever_order_the_pages_arrive` |
| 20 | `lastfm.py`: `fetch_scrobbles` does not raise on error metadata | `test_an_unusable_first_page_raises_the_typed_unavailable_failure` and Task 1's two outage tests |
| 21 | `lastfm.py`: `data_loss_pct` without the `== 0` guard | `test_metadata_without_page_counts_is_a_complete_fetch` (0 / 0) |
| 22 | `lastfm.py`: default a missing album to `"..."` in `_name_of` (`return text if isinstance(text, str) else "..."`) | `test_a_missing_name_becomes_an_empty_string`, Task 1's `test_an_entry_with_no_album_field_is_not_an_album_play` |
| 23 | `lastfm.py`: in `_plays_from_pages` build `Play(artist=_name_of(entry, "album"), album=_name_of(entry, "artist"), ...)` | `test_fetch_scrobbles_hands_back_plays_with_utc_timestamps` |
| 24 | `lastfm.py`: in `_plays_from_pages` narrow `except (TypeError, ValueError, OverflowError, OSError):` to `except (TypeError,):` | `test_an_unreadable_entry_is_dropped_and_counted_not_fatal` (the `"abc"` timestamp raises `ValueError` out of the function) |
| 25 | `lastfm.py`: delete the `if not isinstance(entry, dict):` guard | `test_an_unreadable_entry_is_dropped_and_counted_not_fatal` (the bare string `"Zqxv"` has no `.get`) |
| 26 | `lastfm.py`: `data_loss_pct` divides `self.pages_dropped` by `self.pages_received` | `test_the_summary_reports_dropped_pages` (2 / 3 gives 67, not 40) |
| 27 | `lastfm.py`: in `fetch_scrobbles` call `fetch_all_recent_tracks_async(username, window.start_ts(), window.end_ts())` without `progress_cb=progress_cb` | `test_fetch_scrobbles_passes_the_window_and_callback_through` |
| 28 | `lastfm.py`: in `_plays_from_pages` after `plays.append(...)` add ``logging.debug(f"Last.fm play {plays[-1]}")`` | `test_fetch_scrobbles_logs_no_listening_facts` (the valid entry's names carry the marker) |
| 29 | `lastfm.py`: in `_plays_from_pages` read `date_field.get("#text")` instead of `date_field.get("uts")` | `test_lastfm_fixture_flows_through_scrobbles_into_daily_counts` (the fixture's `"9 Jun 2008, 17:16"` is not a number, so the count is 0, not 1) |
| 30 | `heatmap.py`: wrap the `fetch_scrobbles` call in `try: ... except ProviderError: jobs.fail(job_id, "lastfm_unavailable"); return` | `test_a_total_lastfm_failure_propagates_to_the_backstop` (no `ProviderError` escapes) |
| 31 | `heatmap.py`: in `_report_heatmap_failure` replace the classifier call with `error_code = "internal_error"` | `test_lastfm_outage_crash_publishes_lastfm_unavailable` |
| 32 | `heatmap.py`: add `from scrobblescope.lastfm import fetch_all_recent_tracks_async` | `test_nothing_outside_lastfm_reads_the_page_layer` |

Apply one at a time, run the named test, confirm it fails, restore with `git checkout -- <file>`. Rows 1-16 run in `tests/test_plays.py`, rows 17-29 in `tests/services/test_lastfm_service.py` (row 29 in `tests/test_provider_fixtures.py`), rows 30-31 in `tests/test_heatmap.py`, row 32 in `tests/test_module_boundaries.py`. Where a row names a test from Task 1, run `tests/test_lastfm_job_results.py` too.

- [ ] **Step 12: Measure the memory the plays add, and stop above the budget (hosting ceiling)**

Plays are built while `utils.REQUEST_CACHE` still holds every raw page for an hour, so the plays are pure addition. The budget is **20 MB of peak added memory, for the 80,000-scrobble probe below, per job.** Why 20: the production machine has 512 MB on one worker, `config.MAX_ACTIVE_JOBS` is 5, and five concurrent jobs of an account this large would add 100 MB, about a fifth of the machine. That is the most this refactor may spend. 80,000 scrobbles in a year (about 220 a day) is an extreme listener, so the figure for most jobs is a small fraction of it. The strings are not copied (a `Play` points at the same decoded strings the cached page holds), so the cost is the `Play` and `datetime` objects and the tuple, and there is no cheap in-scope trim.

Write this script OUTSIDE the repository (the scratchpad directory) and run it with `PYTHONPATH` set to the worktree:

```python
import asyncio
import tracemalloc
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from scrobblescope.lastfm import fetch_scrobbles
from scrobblescope.plays import Window

PAGES, PER_PAGE = 400, 200  # 80,000 scrobbles: an extreme listener's year
BASE = int(datetime(2023, 1, 1, tzinfo=UTC).timestamp())


def build():
    pages = []
    for p in range(PAGES):
        tracks = [
            {
                "artist": {"#text": f"Artist {n % 300}", "mbid": "x" * 36},
                "album": {"#text": f"Album {n % 900}", "mbid": "x" * 36},
                "name": f"Track {n}",
                "mbid": "x" * 36,
                "url": "https://www.last.fm/music/" + "x" * 60,
                "image": [{"#text": "https://img.example/" + "x" * 40, "size": "s"}] * 4,
                "streamable": "0",
                "date": {"uts": str(BASE + n), "#text": "01 Jan 2023, 00:00"},
            }
            for n in range(p * PER_PAGE, (p + 1) * PER_PAGE)
        ]
        attr = {"page": str(p + 1), "totalPages": str(PAGES)}
        pages.append({"recenttracks": {"@attr": attr, "track": tracks}})
    return pages


tracemalloc.start()
pages = build()
held, _ = tracemalloc.get_traced_memory()
tracemalloc.reset_peak()
meta = {"status": "ok", "pages_expected": PAGES, "pages_received": PAGES}
with patch(
    "scrobblescope.lastfm.fetch_all_recent_tracks_async",
    new=AsyncMock(return_value=(pages, meta)),
):
    fetch = asyncio.run(fetch_scrobbles("probe", Window.year(2023)))
current, peak = tracemalloc.get_traced_memory()
print(
    f"raw pages held {held / 1e6:.1f} MB; plays added {(current - held) / 1e6:.1f} MB; "
    f"peak added {(peak - held) / 1e6:.1f} MB"
)
```

Run: `PYTHONPATH=C:/ssw/lfs "$PY" <scratchpad>/memory_probe.py`
Expected: three numbers. A dry run of this script against the post-change code on a copy of 5dde407 printed `raw pages held 104.9 MB; plays added 9.6 MB; peak added 10.4 MB`; treat that as the order of magnitude to expect (about half the budget), not as the number to record. Record the numbers it prints on your tree in the Section 4 entry.

Stop rule:
1. "peak added" at most 20 MB: record the three numbers and go on.
2. "peak added" above 20 MB: **stop. Do not commit Task 4.** Return the probe's output to the controller and report that the budget is exceeded. Do not trim the record, add a cap, or change `set_cached_response` to get under it: caching normalized pages instead of raw ones is a behaviour change to the request cache, and it is the controller's decision whether to take it into this PR, plan it as its own task, or raise the budget. Record the number as a finding either way.

- [ ] **Step 13: Docs follow the code**

`.claude/SESSION_CONTEXT.md` Section 3: replace the `lastfm.py` line with `  lastfm.py                 # check_user_exists, check_profile_is_public, fetch_scrobbles (pages in, plays out; pagination, retries and the page cache stay inside)`; add after the `domain.py` line `  plays.py                  # Play (the record both sources emit), Window, aggregate_albums, aggregate_daily_counts, zero_fill_daily_counts`; replace the `heatmap.py` line's `, _aggregate_daily_counts` with nothing (`# heatmap_task, _fetch_and_process_heatmap`). Section 4: add `plays.py         <- domain` after `domain.py        <- (leaf)`; `lastfm.py        <- config, errors, plays, utils`; `heatmap.py       <- errors, jobs, lastfm, plays, utils, worker`; `orchestrator/__init__.py  <- ...` gains `plays` and loses `domain` (it no longer imports it). Derive the lists instead of trusting this text: (the snippet prints the package's own name, `orchestrator`, for its submodule imports; ignore that entry)

```bash
"$PY" -I - <<'PYEOF'
import ast, pathlib
for name in ("lastfm", "heatmap", "plays", "orchestrator/__init__"):
    tree = ast.parse(pathlib.Path(f"scrobblescope/{name}.py").read_text(encoding="utf-8"))
    mods = sorted({a.name if n.module == "scrobblescope" else n.module.split(".")[1]
                   for n in ast.walk(tree)
                   if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("scrobblescope")
                   for a in n.names})
    print(name, mods)
PYEOF
```

Also in Section 5 (the `background_task` flow) change "-> Fetch Last.fm scrobbles (paginated, async)" / "-> Group into albums, filter by thresholds" to "-> lastfm.fetch_scrobbles (paginated, async; pages become plays)" / "-> plays.aggregate_albums, then filter by thresholds".

`docs/architecture/runtime-system.md`: add the node `Plays[plays.py<br/>normalized plays, album and daily aggregates]` to the Runtime subgraph; edges `Album --> Plays`, `Heatmap --> Plays`, `LastFMClient --> Plays`, `Plays --> Domain`; add `Plays` to the `class ... runtime` list. Render the block with the Mermaid validator.

`docs/architecture/top-albums-sequence.md`:
- `Orch->>Orch: Group, normalize, and partition by threshold (inside fetch_top_albums_async)` becomes `Orch->>Orch: Turn pages into plays (lastfm.fetch_scrobbles), group them into albums (plays.aggregate_albums) and partition by threshold (inside fetch_top_albums_async)`.
- the `alt Terminal Last.fm failure` branch (`Orch->>Jobs: fail(lastfm_unavailable)` and its Note) becomes `Note over Orch,Jobs: fetch_scrobbles raises ProviderError(lastfm unavailable) before any stat is written; _fetch_and_process classifies it and calls jobs.fail(lastfm_unavailable), which also stores an empty result list`.
- in the prose after the diagram: "Grouping and threshold filtering happen inside `fetch_top_albums_async`, so they run before every downstream branch. The Last.fm failure terminal and the empty-result terminal simply discard the grouped set." becomes "Grouping (`plays.aggregate_albums`) and threshold filtering happen inside `fetch_top_albums_async`, so they run before every downstream branch. A Last.fm failure raises before any grouping; the empty-result terminal simply discards the grouped set."

`docs/architecture/heatmap-sequence.md`:
- `Heatmap->>LastFM: Fetch last 365 days of recent tracks` gains ` (lastfm.fetch_scrobbles)`; `LastFM-->>Heatmap: Raw scrobble page` becomes `LastFM-->>Heatmap: Page of scrobbles, turned into plays inside lastfm.py`.
- the lines `Heatmap->>Jobs: record_stat(pages_expected and pages_received)` and `alt Terminal Last.fm failure` / `Heatmap->>Jobs: fail(lastfm_unavailable)` / `else Pages available` become `alt Terminal Last.fm failure`, `Note over Heatmap,Jobs: fetch_scrobbles raises ProviderError(lastfm unavailable); the unhandled-exception path below publishes lastfm_unavailable`, `else Plays available`, then `Heatmap->>Jobs: record_stat(pages_expected and pages_received)` as the first line of that branch (re-indent it).
- `Heatmap->>Heatmap: Decode UTC timestamps, filter boundaries, and fill empty days` becomes `Heatmap->>Heatmap: plays.aggregate_daily_counts: the UTC day of each play, boundaries filtered, empty days filled`.
- the paragraph from "The inner, status-based Last.fm path's terminal error code" to "(F-SWE-5)." becomes: "A total Last.fm failure is an exception, not a status: `lastfm.fetch_scrobbles` raises a typed provider failure, and the one backstop -- the `opt Unhandled exception anywhere above` block -- classifies it by type with `errors.classify_exception_to_error_code`, the classifier the album pipeline also uses, and publishes that code (`lastfm_unavailable` for an outage). A fault the classifier does not recognize is ours, so it publishes `internal_error` instead (F-SWE-5)."
- Render both sequence diagrams with the Mermaid validator before committing.

`docs/agents/FINDINGS.md`, F-B23-2: replace its `Status: open (P2). A parity refactor for a batch after Batch 23. Source:` sentence start with `Status: resolved <commit date> by refactor(lastfm): Hand callers scrobbles, not pages -- lastfm.fetch_scrobbles returns plays.Play records and both calculations read them; the two differences listed above are pinned in tests/test_lastfm_job_results.py and tests/test_plays.py, and the Spotify-export rules stay out of plays.py. Source:` (keep the rest of the line). Only the status changes: the entry's problem text, which still names `heatmap._aggregate_daily_counts`, stays as the historical statement of the defect.

`BATCH23_DEFINITION.md` WP-2: replace the three bullets beginning `- [ ] \`iter_plays\` yields tz-aware UTC plays`, `- [ ] \`aggregate_albums\` produces an unpartitioned album mapping` and `- [ ] \`aggregate_daily_counts_from_plays\` anchors its window` with exactly:

```
- [ ] `iter_plays` yields `plays.Play`, the record the Last.fm path already
  emits (`scrobblescope/plays.py`, Batch 23 WP-0 Task 23): a frozen
  `(played_at, artist, album, track)` whose `played_at` is a datetime with
  `tzinfo` exactly `datetime.UTC` (the constructor refuses anything else) and
  whose three names are strings, empty when the export gave none. Nothing else
  crosses the border: no IP address, user agent, country, username or
  platform. `iter_plays` applies the play rule, skips podcasts and audiobooks,
  keeps skip counters, and never copies a private field; the 30-second and
  private-session rules live here, never in `plays.py`.
- [ ] The parser adds no aggregator. `plays.aggregate_albums(plays, window)`
  (with `plays.Window.year(year)` for the album job) produces the
  unpartitioned album mapping keyed by `normalize_name`, with `play_count`,
  `track_counts`, `original_artist` and `original_album`, plus `plays_seen`;
  it is the one aggregator both sources use. WP-3 owns threshold partitioning
  and its post-partition counters. Source-specific row and skip counters stay
  distinct from accepted play counts.
- [ ] The heatmap's daily counts come from `plays.aggregate_daily_counts`.
  WP-2 chooses the window, anchored at `min(today, last play)`; the shared
  `plays.zero_fill_daily_counts` fills the empty days.
```

and in WP-3's acceptance change nothing yet (Task 5 does). WP-6's sentence "Both aggregators keep one original track name per normalized key" is left for the statistics PR (#6), which amends WP-6.

Sweep: `git grep -n -e "_aggregate_daily_counts" -e "_zero_fill_daily_counts" -e "aggregate_daily_counts_from_plays" -e "fetch_all_recent_tracks_async" -- . ':!docs/history' ':!docs/logarchive' ':!docs/superpowers/plans' ':!tests' ':!scrobblescope/lastfm.py'`
Expected hits: `BATCH23_DEFINITION.md` (the checked, dated Part A line for `_zero_fill_daily_counts`; and the WP-3 acceptance line that Task 5 rewrites), and `docs/agents/FINDINGS.md` F-B23-2's problem text (two lines naming `heatmap._aggregate_daily_counts`: a resolved finding's body is left as the historical statement). Anything else is a stale statement: fix it.

- [ ] **Step 14: Section 4 entry, gates, commit**

Entry heading: `### <commit date> - Callers get scrobbles, not Last.fm pages`. Body: scope; owner intent (2026-09-29 rulings: "tests move to the new interfaces"; `total_scrobbles` counts completed scrobbles only); what changed; the four behaviour changes and the ordering change by name; the accepted extra ERROR line on a plain Last.fm outage; deviations (none); the three memory numbers from Step 12 against the 20 MB budget; mutation evidence; validation.

Commit body: names the four behaviour changes, then every edited test: `tests/services/test_lastfm_logic.py` (9 patch strings; the UTC test's `datetime` patch target), `tests/test_heatmap.py` (`TestAggregateDailyCounts` moved to `tests/test_plays.py`; 7 pipeline tests re-pointed to `fetch_scrobbles`; `test_upstream_error_sets_job_error` replaced), `tests/test_provider_fixtures.py` (2), `tests/test_pipeline_integration.py` (1 patch string), `tests/services/test_orchestrator_fetch_and_process.py::test_fetch_and_process_discards_exclusions_on_lastfm_error`, `tests/test_lastfm_job_results.py` (5 xfail markers removed), `tests/test_module_boundaries.py` (one rule added).
Subject: `refactor(lastfm): Hand callers scrobbles, not pages` (51 characters).

---
### Task 5: Publish one typed album selection (23d)

**Touches:** `scrobblescope/plays.py`, `scrobblescope/orchestrator/__init__.py`, `tests/helpers.py`, `tests/test_plays.py`, `tests/services/test_finish_album_job.py` (new), `tests/services/test_lastfm_logic.py`, `tests/services/test_orchestrator_fetch_and_process.py`, `tests/services/test_orchestrator_helpers.py` (one test), `tests/test_provider_fixtures.py`, `.claude/SESSION_CONTEXT.md`, `docs/architecture/top-albums-sequence.md`, `docs/architecture/runtime-system.md`, `docs/agents/FINDINGS.md`, `BATCH23_DEFINITION.md`, `docs/agents/PLAYBOOK.md`.
**After:** Task 4.

**Files:**
- Create: `tests/services/test_finish_album_job.py`
- Modify: the files above

**Interfaces:**
- Consumes: Task 4's `Play`, `Window`, `AlbumAggregate`, `AlbumKey`, `AlbumTally`, `aggregate_albums`, `lastfm.FetchSummary`, `lastfm.fetch_scrobbles`; PR #3's `album_request.AlbumRequest` (already imported by `orchestrator/__init__.py` for `background_task`).
- Produces (Batch 23 WP-3's `export_album_task` imports exactly these and nothing private):
  - `plays.AlbumSelection(eligible: dict[AlbumKey, AlbumTally], exclusions: dict[AlbumKey, dict], total_below_threshold: int, plays_seen: int, unique_albums: int)` with `stats() -> dict` returning `total_scrobbles`, `unique_albums`, `albums_passing_filter`, `albums_below_threshold`.
  - `plays.select_albums(aggregate: AlbumAggregate, min_plays: int, min_tracks: int, exclusion_cap: int) -> AlbumSelection` -- the one threshold partition and the exclusion cap (ties broken by normalized key).
  - `async orchestrator.finish_album_job(job_id, selection, album, *, overall_start_time) -> list` -- the one publish step. `album` is PR #3's `album_request.AlbumRequest` (its `username` is `None` for an export; `select_albums` has already applied its minimums). It records the four stats and one unmatched record per exclusion, ends with one `jobs.succeed(job_id, [], "No albums found for the specified criteria.")` and no correction-worker hand-off when nothing is eligible, and otherwise runs `_process_filtered_albums` with the request's year, sort mode, release scope, decade, release year, limit and `include_unmatched`. See "Dependence on PR #3" for why the request object and not seven keywords.
  - `orchestrator.fetch_top_albums_async(username, year, min_plays=10, min_tracks=3, progress_cb=None) -> tuple[AlbumSelection, FetchSummary]` -- never `None`, never a status dict.
  - `tests.helpers.lastfm_albums(eligible=None, exclusions=None, *, pages_expected=1, pages_received=1, plays_seen=0, total_below_threshold=None)` -> `(AlbumSelection, FetchSummary)`, for tests that patch `fetch_top_albums_async`.

Why: review card B-3 and F-B23-1's threshold half. `_fetch_job_albums` returns `None` for "terminal state already written" and `_process_filtered_albums` returns `[]` for both "job errored" and "empty"; the export job would copy those blocks. One selection type and one publish step give both sources the same ending, and Batch 23 WP-6's per-album fields are added in `aggregate_albums` once.

Deleted: `_fetch_job_albums` (the `None` sentinel), `_record_lastfm_stats`, `_cap_threshold_exclusions` and the interim metadata dict of Task 4. Not changed: `_process_filtered_albums`, `_build_results` (F-B23-1's release-scope half stays open) and the two `return []` after a Spotify failure.

- [ ] **Step 1: Add the shared test helper**

Append to `tests/helpers.py`:

```python
def lastfm_albums(
    eligible=None,
    exclusions=None,
    *,
    pages_expected=1,
    pages_received=1,
    plays_seen=0,
    total_below_threshold=None,
):
    """What ``fetch_top_albums_async`` returns: ``(AlbumSelection, FetchSummary)``.

    For tests that patch ``scrobblescope.orchestrator.fetch_top_albums_async``.
    ``unique_albums`` is derived (eligible plus excluded); the count of albums
    below threshold is ``len(exclusions)`` unless a cap made it larger.
    """
    from scrobblescope.lastfm import FetchSummary
    from scrobblescope.plays import AlbumSelection

    eligible = eligible or {}
    exclusions = exclusions or {}
    selection = AlbumSelection(
        eligible=eligible,
        exclusions=exclusions,
        total_below_threshold=(
            len(exclusions) if total_below_threshold is None else total_below_threshold
        ),
        plays_seen=plays_seen,
        unique_albums=len(eligible) + len(exclusions),
    )
    return selection, FetchSummary(pages_expected, pages_received)
```

- [ ] **Step 2: Write the failing tests for `select_albums`**

Append to `tests/test_plays.py` (add `select_albums` to the import from `scrobblescope.plays`):

```python
# ---------------------------------------------------------------------------
# select_albums and AlbumSelection
# ---------------------------------------------------------------------------


def _aggregate(albums, plays_seen=0):
    """An AlbumAggregate holding ``albums`` given as {(artist, album): (plays, tracks)}."""
    built = {}
    for (artist, album), (plays, tracks) in albums.items():
        built[normalize_name(artist, album)] = {
            "play_count": plays,
            "track_counts": {f"t{n}": 1 for n in range(tracks)},
            "original_artist": artist,
            "original_album": album,
        }
    return AlbumAggregate(albums=built, plays_seen=plays_seen)


class TestSelectAlbums:
    def test_it_splits_by_both_minimums_and_counts_each_side(self):
        """Planted defect: make a minimum exclusive."""
        aggregate = _aggregate(
            {
                ("A", "Passes"): (10, 3),
                ("B", "Few Plays"): (9, 3),
                ("C", "Few Tracks"): (12, 2),
            },
            plays_seen=31,
        )

        selection = select_albums(aggregate, 10, 3, exclusion_cap=500)

        assert set(selection.eligible) == {normalize_name("A", "Passes")}
        assert set(selection.exclusions) == {
            normalize_name("B", "Few Plays"),
            normalize_name("C", "Few Tracks"),
        }
        assert selection.total_below_threshold == 2
        assert selection.unique_albums == 3
        assert selection.plays_seen == 31

    def test_stats_are_the_four_numbers_a_job_records(self):
        """Planted defect: report the capped exclusion count as the total."""
        albums = {(f"Artist{n:04d}", f"Album{n:04d}"): (1, 1) for n in range(600)}
        albums[("Big", "Hit")] = (50, 5)
        selection = select_albums(_aggregate(albums, 650), 10, 3, exclusion_cap=500)

        assert selection.stats() == {
            "total_scrobbles": 650,
            "unique_albums": 601,
            "albums_passing_filter": 1,
            "albums_below_threshold": 600,
        }
        assert len(selection.exclusions) == 500

    def test_the_cap_keeps_the_most_played_exclusions(self):
        """Planted defect: keep the first 500 inserted instead of the top 500."""
        albums = {(f"Low{n:03d}", f"Low{n:03d}"): (1, 1) for n in range(500)}
        albums.update({(f"High{n}", f"High{n}"): (9, 1) for n in range(5)})

        selection = select_albums(_aggregate(albums), 10, 3, exclusion_cap=500)

        assert {a["artist"] for a in selection.exclusions.values()} >= {
            f"High{n}" for n in range(5)
        }

    def test_the_cap_does_not_depend_on_input_order(self):
        """Every album ties on one play, so only the key can break the tie.
        Planted defect: sort by play count alone (a stable sort then keeps
        whichever tied albums were inserted first)."""
        albums = {(f"Artist{n:04d}", f"Album{n:04d}"): (1, 1) for n in range(600)}
        forward = select_albums(_aggregate(albums), 10, 3, exclusion_cap=500)
        backward = select_albums(
            _aggregate(dict(reversed(list(albums.items())))), 10, 3, exclusion_cap=500
        )

        assert len(forward.exclusions) == 500
        assert set(forward.exclusions) == set(backward.exclusions)

```

`test_it_splits_by_both_minimums_and_counts_each_side` already shows that a selection under the cap keeps every exclusion (both are in `selection.exclusions`), so no separate under-the-cap test is written, and no type-check test: a test that only asserts `isinstance` fails for no defect a behavioural test would not also catch.

- [ ] **Step 3: Write the failing tests for `finish_album_job`**

Create `tests/services/test_finish_album_job.py`:

```python
"""The one publish step both album sources end in (Task 23d).

Whatever produced an ``AlbumSelection`` -- a Last.fm fetch today, a Spotify
export in Batch 23 -- ``finish_album_job`` records its stats and its
exclusions, ends the job at once when nothing is eligible, and otherwise
enriches the eligible albums. These tests call it with a selection and no
Last.fm at all, which is what the export job will do.
"""

import dataclasses
from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope import jobs
from scrobblescope.album_request import AlbumRequest
from scrobblescope.orchestrator import finish_album_job
from tests.helpers import TEST_JOB_PARAMS, lastfm_albums

ELIGIBLE = {
    ("radiohead", "ok computer"): {
        "play_count": 50,
        "track_counts": {"airbag": 10},
        "original_artist": "Radiohead",
        "original_album": "OK Computer",
    }
}
EXCLUDED = {
    ("quiet artist", "quiet album"): {
        "artist": "Quiet Artist",
        "album": "Quiet Album",
        "play_count": 3,
        "track_count": 1,
        "reason_code": "below_threshold",
        "shortfall": "7 plays and 2 tracks short",
    }
}
# An export job's request: no Last.fm username (PR #3's AlbumRequest allows None).
ALBUM = AlbumRequest(
    username=None,
    year=2025,
    sort_mode="playcount",
    include_unmatched=False,
    release_scope="all",
    decade=None,
    release_year=None,
    min_plays=10,
    min_tracks=3,
    limit_results="all",
)


async def _finish(selection, album=ALBUM):
    """Run the publish step with enrichment and the correction worker mocked."""
    job_id = jobs.create(TEST_JOB_PARAMS)
    process = AsyncMock(return_value=[{"artist": "Radiohead", "album": "OK Computer"}])
    with (
        patch("scrobblescope.orchestrator.process_albums", process),
        patch("scrobblescope.orchestrator.enqueue_release_check") as enqueue,
    ):
        results = await finish_album_job(
            job_id, selection, album, overall_start_time=0.0
        )
    return job_id, results, process, enqueue


@pytest.mark.asyncio
async def test_a_selection_with_albums_is_published_and_enriched():
    """
    GIVEN a selection with one eligible album and one exclusion
    WHEN the publish step runs
    THEN the four stats and the exclusion are on the job, the eligible album
    reaches enrichment, and the finished job is handed to the correction worker.

    Planted defect: skip recording the selection's stats.
    """
    selection, _ = lastfm_albums(ELIGIBLE, EXCLUDED, plays_seen=53)

    job_id, results, process, enqueue = await _finish(selection)

    stats = jobs.progress(job_id)["stats"]
    assert stats["total_scrobbles"] == 53
    assert stats["albums_passing_filter"] == 1
    assert stats["albums_below_threshold"] == 1
    assert stats["unique_albums"] == 2
    assert jobs.unmatched(job_id) == {"quiet artist|quiet album": EXCLUDED[("quiet artist", "quiet album")]}
    process.assert_awaited_once()
    assert process.await_args.args[1] == ELIGIBLE
    assert results == [{"artist": "Radiohead", "album": "OK Computer"}]
    enqueue.assert_called_once_with(job_id)


@pytest.mark.asyncio
async def test_a_selection_with_nothing_eligible_ends_the_job_once():
    """
    GIVEN a selection whose every album is below a minimum
    WHEN the publish step runs
    THEN the stats and exclusions are recorded, the job ends exactly once at
    100% with the empty-result message and no error, and neither enrichment nor
    the correction worker is reached.

    Planted defects: leave the job running when nothing is eligible; or end it
    twice.
    """
    selection, _ = lastfm_albums(None, EXCLUDED, plays_seen=3)

    with patch("scrobblescope.jobs.succeed", wraps=jobs.succeed) as succeed:
        job_id, results, process, enqueue = await _finish(selection)

    succeed.assert_called_once_with(
        job_id, [], "No albums found for the specified criteria."
    )
    context = jobs.context(job_id)
    assert results == []
    assert context["progress"]["progress"] == 100
    assert context["progress"]["error"] is False
    assert context["progress"]["message"] == "No albums found for the specified criteria."
    assert context["results"] == []
    assert context["progress"]["stats"]["albums_below_threshold"] == 1
    assert len(context["unmatched"]) == 1
    process.assert_not_awaited()
    enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_stats_and_exclusions_are_readable_by_the_time_the_job_ends():
    """
    GIVEN a selection with nothing eligible
    WHEN the job ends
    THEN a page that sees 100% already finds the stats and the exclusions.

    Planted defect: record the exclusions after ending the job.
    """
    selection, _ = lastfm_albums(None, EXCLUDED, plays_seen=3)
    job_id = jobs.create(TEST_JOB_PARAMS)
    seen_at_the_end = {}
    real_succeed = jobs.succeed

    def succeed_and_look(jid, results, message):
        seen_at_the_end["stats"] = jobs.progress(jid)["stats"]
        seen_at_the_end["unmatched"] = jobs.unmatched(jid)
        return real_succeed(jid, results, message)

    with patch("scrobblescope.jobs.succeed", side_effect=succeed_and_look):
        await finish_album_job(job_id, selection, ALBUM, overall_start_time=0.0)

    assert seen_at_the_end["stats"]["albums_below_threshold"] == 1
    assert len(seen_at_the_end["unmatched"]) == 1


@pytest.mark.asyncio
async def test_the_shared_step_writes_no_lastfm_only_stats():
    """
    GIVEN a selection that did not come from Last.fm
    WHEN the publish step runs
    THEN the job carries no page counts or page-loss notice: an export has no pages.

    Planted defect: write ``pages_fetched`` from the shared step.
    """
    selection, _ = lastfm_albums(ELIGIBLE, plays_seen=50)

    job_id, _, _, _ = await _finish(selection)

    stats = jobs.progress(job_id)["stats"]
    assert "pages_fetched" not in stats
    assert "partial_data_warning" not in stats
    assert "pages_dropped" not in stats


@pytest.mark.asyncio
async def test_the_albums_choice_reaches_the_enrichment_tail():
    """
    GIVEN a request that asks for unmatched albums to be listed (include_unmatched)
    WHEN the publish step runs
    THEN the tail that merges them is told so.

    Planted defect: drop the argument on the way to ``_process_filtered_albums``.
    """
    selection, _ = lastfm_albums(ELIGIBLE, plays_seen=50)
    job_id = jobs.create(TEST_JOB_PARAMS)
    tail = AsyncMock(return_value=[])

    with patch("scrobblescope.orchestrator._process_filtered_albums", tail):
        await finish_album_job(
            job_id,
            selection,
            dataclasses.replace(ALBUM, include_unmatched=True),
            overall_start_time=0.0,
        )

    assert tail.await_args.kwargs["include_unmatched"] is True
```

- [ ] **Step 4: Run both; they fail on missing names**

Run: `"$PY" -m pytest tests/test_plays.py tests/services/test_finish_album_job.py -q -p no:cacheprovider`
Expected: collection errors (`ImportError: cannot import name 'select_albums'` / `'finish_album_job'`).

- [ ] **Step 5: Add `AlbumSelection` and `select_albums` to `plays.py`**

Change the module docstring's last line to `    plays <- domain, unmatched`, add `from scrobblescope.unmatched import partition_albums_by_threshold` after the `domain` import, and append:

```python
@dataclass(frozen=True, slots=True)
class AlbumSelection:
    """The albums a window's listening leaves after the thresholds.

    ``eligible`` goes on to enrichment. ``exclusions`` holds the report facts of
    albums below a minimum, already capped; ``total_below_threshold`` is their
    count before the cap. ``plays_seen`` and ``unique_albums`` come from the
    aggregate. Immutable and job-free, so a test can build one without a job.
    """

    eligible: dict[AlbumKey, AlbumTally]
    exclusions: dict[AlbumKey, dict]
    total_below_threshold: int
    plays_seen: int
    unique_albums: int

    def stats(self) -> dict[str, int]:
        """Return the four aggregation stats a job records, under their wire names."""
        return {
            "total_scrobbles": self.plays_seen,
            "unique_albums": self.unique_albums,
            "albums_passing_filter": len(self.eligible),
            "albums_below_threshold": self.total_below_threshold,
        }


def select_albums(
    aggregate: AlbumAggregate, min_plays: int, min_tracks: int, exclusion_cap: int
) -> AlbumSelection:
    """Apply the listening minimums to *aggregate* and cap the exclusion report.

    The partition is ``unmatched.partition_albums_by_threshold`` (each excluded
    album appears once even when it fails both minimums). When more albums are
    excluded than *exclusion_cap*, the most played are kept, and ties are broken
    by normalized key so the retained set does not depend on the aggregate's
    insertion order -- a property of the fetch path, not of this decision.
    Pure: no I/O and no job.
    """
    eligible, excluded = partition_albums_by_threshold(
        aggregate.albums, min_plays, min_tracks
    )
    total_below_threshold = len(excluded)
    if total_below_threshold > exclusion_cap:
        kept = sorted(
            excluded,
            key=lambda key: (-int(excluded[key].get("play_count", 0)), key),
        )[:exclusion_cap]
        excluded = {key: excluded[key] for key in kept}
    return AlbumSelection(
        eligible=eligible,
        exclusions=excluded,
        total_below_threshold=total_below_threshold,
        plays_seen=aggregate.plays_seen,
        unique_albums=len(aggregate.albums),
    )
```

- [ ] **Step 6: Rewrite the orchestrator around the selection**

In `scrobblescope/orchestrator/__init__.py`:

1. Imports: change `from scrobblescope.plays import Window, aggregate_albums` to `from scrobblescope.plays import Window, aggregate_albums, select_albums`; delete `from scrobblescope.unmatched import partition_albums_by_threshold`. Run `"$RUFF" check --select F scrobblescope/orchestrator/__init__.py` afterwards and delete by hand anything it reports (it does not fix an `__init__.py`).
2. Delete `_cap_threshold_exclusions`, `_record_lastfm_stats` and `_fetch_job_albums` entirely.
3. Replace `fetch_top_albums_async` with:

```python
async def fetch_top_albums_async(
    username, year, min_plays=10, min_tracks=3, progress_cb=None
):
    """Read *username*'s scrobbles for *year* and select the albums that pass.

    Returns ``(selection, summary)``: an ``AlbumSelection`` (eligible albums,
    the capped threshold exclusions and the four aggregation counts) and the
    ``FetchSummary`` of the Last.fm read. A total Last.fm failure raises; it is
    never a return value. Threshold exclusions keep their report facts but never
    enter Spotify enrichment.

    Args:
        progress_cb: Optional ``Callable[[int, int, int], None]`` forwarded to
            ``fetch_scrobbles`` for per-page progress.
    """
    logging.debug(f"Start fetch_top_albums_async(year={year})")
    window = Window.year(year)
    fetch = await fetch_scrobbles(username, window, progress_cb=progress_cb)
    selection = select_albums(
        aggregate_albums(fetch.plays, window), min_plays, min_tracks, _MAX_ALBUM_CAP
    )
    return selection, fetch.summary
```

4. Add after `_apply_post_slice`:

```python
def _record_fetch_stats(job_id, summary):
    """Write the Last.fm-only job stats: pages fetched, and the page-loss notice.

    They stay out of ``finish_album_job`` because an export has no pages.
    """
    jobs.record_stat(job_id, "pages_fetched", summary.pages_received)
    if summary.partial:
        jobs.record_stat(
            job_id,
            "partial_data_warning",
            f"Note: {summary.pages_dropped} of {summary.pages_expected} Last.fm "
            f"pages failed to load ({summary.data_loss_pct}% data loss). "
            "Results may be incomplete.",
        )
        jobs.record_partial_source(job_id, "lastfm")
        jobs.record_stat(job_id, "pages_dropped", summary.pages_dropped)


def _publish_selection(job_id, selection):
    """Record a selection's four stats and one unmatched entry per exclusion."""
    for key, value in selection.stats().items():
        jobs.record_stat(job_id, key, value)
    for key, item in selection.exclusions.items():
        jobs.record_unmatched(job_id, "|".join(key), item)


async def finish_album_job(job_id, selection, album, *, overall_start_time):
    """Publish an album selection to its job and carry the job to its end.

    The step every album source shares once it holds an ``AlbumSelection``: a
    Last.fm job calls it after ``fetch_top_albums_async``; Batch 23's export job
    calls it after ``plays.select_albums``. It records the selection's stats and
    one unmatched entry per exclusion, in that order, then either ends the job
    on the spot -- nothing is eligible, so ``jobs.succeed`` with an empty result
    and the "no albums" message, and no hand-off to the correction worker -- or
    runs ``_process_filtered_albums`` on the eligible albums.

    ``album`` is the job's validated ``AlbumRequest``: it supplies the year,
    sort mode, release scope, decade, release year, result limit and
    ``include_unmatched`` the enrichment tail needs. Its ``username`` is
    ``None`` for an export, and its minimums were applied by ``select_albums``
    before this call, so they are not read here.

    ``overall_start_time`` is the job's start, so "Total time elapsed" measures
    the whole job. Returns the results list, ``[]`` when the job ended empty or
    failed.
    """
    _publish_selection(job_id, selection)
    if not selection.eligible:
        jobs.succeed(job_id, [], "No albums found for the specified criteria.")
        return []
    jobs.advance(job_id, 20, "Processing your albums...")
    return await _process_filtered_albums(
        job_id,
        selection.eligible,
        album.year,
        album.sort_mode,
        album.release_scope,
        album.decade,
        album.release_year,
        album.limit_results,
        overall_start_time,
        include_unmatched=album.include_unmatched,
    )
```

5. In `_process_filtered_albums`'s docstring replace "and Batch 23's export task will be the second caller, invoking it after its own aggregation so both paths share the same "Done" progress and release-check hand-off instead of duplicating them." with "and is called through ``finish_album_job``, which Batch 23's export task also calls, so both paths share the same "Done" progress and release-check hand-off."
6. Replace the body of `_fetch_and_process`'s `try:` (everything from `overall_start_time = time.time()` to the `return await _process_filtered_albums(...)` call) with:

```python
        overall_start_time = time.time()
        cleanup_expired_cache()
        jobs.expire_stale()

        jobs.start(job_id, "Initializing...")
        jobs.advance(job_id, 5, "Fetching your data from Last.fm...")

        def _lastfm_progress(pages_done, total_pages, _pages_received):
            """Report page-fetching progress inside the album fetch band."""
            jobs.report_phase(
                job_id,
                jobs.ALBUM_LASTFM_FETCH,
                pages_done,
                total_pages,
                "Reading your Last.fm history...",
            )

        step_start_time = time.time()
        selection, summary = await fetch_top_albums_async(
            username,
            year,
            min_plays=min_plays,
            min_tracks=min_tracks,
            progress_cb=_lastfm_progress,
        )
        logging.info(
            f"Time elapsed (Last.fm data fetch): {time.time() - step_start_time:.1f}s"
        )
        _record_fetch_stats(job_id, summary)

        album = AlbumRequest(
            username=username,
            year=year,
            sort_mode=sort_mode,
            include_unmatched=include_unmatched,
            release_scope=release_scope,
            decade=decade,
            release_year=release_year,
            min_plays=min_plays,
            min_tracks=min_tracks,
            limit_results=limit_results,
        )
        return await finish_album_job(
            job_id, selection, album, overall_start_time=overall_start_time
        )
```

   Keep the `except Exception as exc:` handler as it is. `_fetch_and_process` still receives its parameters positionally (PR #3 leaves its signature alone); the `AlbumRequest` is rebuilt here from them, and `AlbumRequest` is already imported by this module for `background_task`.
7. `__all__`: delete `"_fetch_job_albums"` and `"_record_lastfm_stats"`; add `"finish_album_job"` (after `"fetch_top_albums_async"`).
8. Run `"$RUFF" check --select I,F --fix scrobblescope && "$RUFF" format scrobblescope`, then `"$RUFF" check --select F scrobblescope` must report nothing.

- [ ] **Step 7: Edit the existing tests**

1. `tests/services/test_lastfm_logic.py` -- the function now returns `(selection, summary)`:

| Test | Old line | New lines |
|---|---|---|
| `..._min_plays_filter`, `..._min_tracks_filter` (they read `excluded`) | `result, excluded, _ = await fetch_top_albums_async(...)` | `selection, _ = await fetch_top_albums_async(...)` then `result, excluded = selection.eligible, selection.exclusions` |
| `test_fetch_top_albums_aggregates_play_counts` (it never reads `excluded`), `..._skips_out_of_bounds_timestamps`, `..._skips_now_playing_track`, `..._non_latin_tracks_counted_distinctly` | `result, excluded, _ = ...` or `result, _, _ = await fetch_top_albums_async(...)` | `selection, _ = await fetch_top_albums_async(...)` then `result = selection.eligible` |
| `test_fetch_top_albums_returns_stats_in_metadata` | `_, exclusions, metadata = await ...` and `stats = metadata["stats"]` | `selection, summary = await ...`, `stats = selection.stats()`, `exclusions = selection.exclusions`, and one added line `assert summary.pages_received == 1` (the page it was given); its docstring says `selection.stats()` where it said `fetch_metadata["stats"]`; rename it `test_fetch_top_albums_returns_stats_in_the_selection` |
| `test_threshold_exclusion_cap_is_independent_of_input_order` | `_, excluded, _ = await fetch_top_albums_async("testuser", 2023)` | `selection, _ = await fetch_top_albums_async("testuser", 2023)` then `return selection.exclusions` |

   The UTC-window test (`await fetch_top_albums_async("testuser", 2024)`, no unpacking) is unchanged. No asserted value changes.
2. `tests/test_provider_fixtures.py::test_lastfm_fixture_flows_through_fetch_top_albums`: `eligible, _, _ = await fetch_top_albums_async(...)` becomes `selection, _ = await fetch_top_albums_async(...)` followed by `eligible = selection.eligible`.
3. `tests/services/test_orchestrator_fetch_and_process.py`: add `lastfm_albums` to `from tests.helpers import TEST_JOB_PARAMS`. The patches of `fetch_top_albums_async` that raise (`side_effect=RuntimeError/ZeroDivisionError/ProviderError/KeyError`, and `test_fetch_and_process_discards_exclusions_on_lastfm_error`) are unchanged. Change these twelve:

| Where | Old | New |
|---|---|---|
| eight tests with `return_value=(filtered, {}, {"status": "ok"})` (cache-hit, hands-the-finished-job, `..._does_not_queue_correction_checks_on_an_error`, the Spotify-error test and its neighbours: find them with `git grep -n 'return_value=(filtered, {}, {"status": "ok"})' tests/services/test_orchestrator_fetch_and_process.py`) | `return_value=(filtered, {}, {"status": "ok"})` | `return_value=lastfm_albums(filtered)` |
| the exclusions-only test (`threshold_item` for "Lizzy McAlpine / Older") | `return_value=({}, {("lizzy mcalpine", "older"): threshold_item}, {"status": "ok"})` (three lines) | `return_value=lastfm_albums(exclusions={("lizzy mcalpine", "older"): threshold_item})` |
| `test_fetch_and_process_lastfm_phase_callback`, `fake_fetch` | `return {}, {}, {"status": "ok"}` | `return lastfm_albums()` |
| `test_fetch_and_process_passes_progress_cb_to_lastfm`, `_invoke_cb` | `return {}, {}, {"status": "ok"}` | `return lastfm_albums()` |
| the include-unmatched test (`_INCLUDE_FILTERED`) | `return_value=(dict(_INCLUDE_FILTERED), {}, {"status": "ok"})` | `return_value=lastfm_albums(dict(_INCLUDE_FILTERED))` |

   Check: `git grep -n '{"status"' -- tests/services/test_orchestrator_fetch_and_process.py` is empty and `"$PY" -m pytest tests/services/test_orchestrator_fetch_and_process.py -q -p no:cacheprovider` passes without any assertion edited.
4. `tests/services/test_orchestrator_helpers.py::test_lastfm_page_loss_is_recorded_as_a_kind_beside_its_sentence` (it called the deleted `_record_lastfm_stats`) is replaced by:

```python
def test_lastfm_page_loss_is_recorded_as_a_kind_beside_its_sentence():
    """
    GIVEN a Last.fm fetch that dropped a page of four
    WHEN its fetch stats are recorded on the job
    THEN the job holds the sentence, the number of pages dropped and the kind
         ("lastfm"), so the Results page never has to read the sentence to know
         what degraded
    """
    from scrobblescope.lastfm import FetchSummary
    from scrobblescope.orchestrator import _record_fetch_stats

    job_id = jobs.create(TEST_JOB_PARAMS)
    _record_fetch_stats(job_id, FetchSummary(pages_expected=4, pages_received=3))

    stats = jobs.progress(job_id)["stats"]
    assert stats["partial_data_sources"] == ["lastfm"]
    assert stats["pages_dropped"] == 1
    assert stats["pages_fetched"] == 3
    assert stats["partial_data_warning"].startswith(
        "Note: 1 of 4 Last.fm pages failed to load (25% data loss)."
    )


def test_a_complete_lastfm_fetch_records_pages_and_no_notice():
    """A fetch that read every page records the count and no page-loss notice.

    Planted defect: write the page-loss notice even when no page was dropped."""
    from scrobblescope.lastfm import FetchSummary
    from scrobblescope.orchestrator import _record_fetch_stats

    job_id = jobs.create(TEST_JOB_PARAMS)
    _record_fetch_stats(job_id, FetchSummary(pages_expected=2, pages_received=2))

    stats = jobs.progress(job_id)["stats"]
    assert stats["pages_fetched"] == 2
    assert "partial_data_warning" not in stats
    assert "partial_data_sources" not in stats
```

- [ ] **Step 8: Run the suites**

Run: `"$RUFF" check scrobblescope tests && "$RUFF" format scrobblescope tests`
Run: `"$PY" -m pytest tests/test_plays.py tests/services/test_finish_album_job.py tests/services/test_lastfm_logic.py tests/services/test_orchestrator_fetch_and_process.py tests/services/test_orchestrator_helpers.py tests/test_provider_fixtures.py tests/test_lastfm_job_results.py tests/test_pipeline_integration.py -q -p no:cacheprovider`
Expected: all pass; `tests/test_lastfm_job_results.py` still `23 passed` and unchanged since Task 4 (`git diff HEAD -- tests/test_lastfm_job_results.py` is empty): the parity suite proves the tail rewrite.
Run: `"$PY" -m pytest -q -p no:cacheprovider`
Expected: every test passes.
Sweep: `git grep -n -e _fetch_job_albums -e _record_lastfm_stats -e _cap_threshold_exclusions -- scrobblescope tests` is empty.

- [ ] **Step 9: Mutation evidence**

| # | File and plant | Test that must fail |
|---|---|---|
| 1 | `plays.py`: in `select_albums` sort by `-int(excluded[key].get("play_count", 0))` alone (drop the `key` tie-break) | `test_the_cap_does_not_depend_on_input_order` and `test_threshold_exclusion_cap_is_independent_of_input_order` |
| 2 | `plays.py`: `select_albums` slices `list(excluded)[:exclusion_cap]` (insertion order) | `test_the_cap_keeps_the_most_played_exclusions` (the five 9-play albums come last and fall off) |
| 3 | `plays.py`: `stats()` reports `len(self.exclusions)` for `albums_below_threshold` | `test_stats_are_the_four_numbers_a_job_records` (500, not 600) |
| 4 | `scrobblescope/unmatched.py`, `partition_albums_by_threshold`: `if play_count < min_plays:` becomes `<=` | `test_it_splits_by_both_minimums_and_counts_each_side` (the 10-play album is then excluded) |
| 5 | `orchestrator`: in `finish_album_job` move `_publish_selection(job_id, selection)` to after the empty-eligible `jobs.succeed` (inside that branch) | `test_stats_and_exclusions_are_readable_by_the_time_the_job_ends` |
| 6 | `orchestrator`: delete the `jobs.succeed(job_id, [], ...)` / `return []` pair in `finish_album_job` | `test_a_selection_with_nothing_eligible_ends_the_job_once` and Task 1's `test_when_every_album_is_below_a_minimum_the_job_ends_with_the_report` |
| 7 | `orchestrator`: in `finish_album_job` call `jobs.succeed(job_id, [], ...)` twice before `return []` | `test_a_selection_with_nothing_eligible_ends_the_job_once` (`assert_called_once_with`) |
| 8 | `orchestrator`: omit `include_unmatched=album.include_unmatched` in `finish_album_job`'s call | `test_the_albums_choice_reaches_the_enrichment_tail` |
| 9 | `orchestrator`: `_publish_selection` also writes `pages_fetched` | `test_the_shared_step_writes_no_lastfm_only_stats` |
| 10 | `orchestrator`: delete the `for key, value in selection.stats().items():` loop in `_publish_selection` | `test_a_selection_with_albums_is_published_and_enriched` (no `total_scrobbles`) and `test_stats_and_exclusions_are_readable_by_the_time_the_job_ends` |
| 11 | `orchestrator`: delete `jobs.record_partial_source(job_id, "lastfm")` in `_record_fetch_stats` | `test_lastfm_page_loss_is_recorded_as_a_kind_beside_its_sentence` and Task 1's partial test |
| 12 | `orchestrator`: in `_record_fetch_stats` change `if summary.partial:` to `if True:` | `test_a_complete_lastfm_fetch_records_pages_and_no_notice` (a "0 of 2" notice appears) |
| 13 | `orchestrator`: `_fetch_and_process` skips `_record_fetch_stats` | Task 1's `test_a_dropped_page_makes_the_album_job_partial_and_says_so` |

Apply one at a time, run the named test, confirm it fails, restore with `git checkout -- <file>`. Rows 1-4 run in `tests/test_plays.py` (and `tests/services/test_lastfm_logic.py` for the cap-order test), rows 5-10 in `tests/services/test_finish_album_job.py`, rows 11-12 in `tests/services/test_orchestrator_helpers.py`, row 13 in `tests/test_lastfm_job_results.py`.

- [ ] **Step 10: Docs follow the code**

`.claude/SESSION_CONTEXT.md` Section 3: the `plays.py` line becomes `  plays.py                  # Play (the record both sources emit), Window, aggregate_albums, aggregate_daily_counts, zero_fill_daily_counts, AlbumSelection, select_albums`; the `orchestrator/__init__.py` line becomes `# facade + pipeline glue: process_albums, _fetch_and_process, background_task, fetch_top_albums_async, finish_album_job (the one publish step)`. Section 4: `plays.py         <- domain, unmatched`; re-derive the `orchestrator/__init__.py` import list with the `ast` snippet from Task 4 Step 13 (it no longer imports `unmatched`).

`docs/architecture/runtime-system.md`: add the edge `Plays --> Unmatched`; re-render with the Mermaid validator.

`docs/architecture/top-albums-sequence.md`:
- the line Task 4 wrote, `Orch->>Orch: Turn pages into plays (lastfm.fetch_scrobbles), group them into albums (plays.aggregate_albums) and partition by threshold (inside fetch_top_albums_async)`, becomes `Orch->>Orch: Turn pages into plays (lastfm.fetch_scrobbles), group them into albums (plays.aggregate_albums) and select by threshold (plays.select_albums, inside fetch_top_albums_async)`.
- `Orch->>Jobs: Aggregation stats, and partial_data_warning plus record_partial_source(lastfm) when pages were dropped (failed, or malformed after every retry)` becomes `Orch->>Jobs: pages_fetched, and partial_data_warning plus record_partial_source(lastfm) when pages were dropped (failed, or malformed after every retry); Last.fm only`.
- `Orch->>Jobs: Persist one below_threshold exclusion per album, with its counts and failed thresholds` becomes `Orch->>Jobs: finish_album_job: record the four aggregation stats, then one below_threshold exclusion per album, with its counts and failed thresholds`.
- after the paragraph that begins "Grouping (`plays.aggregate_albums`) and threshold filtering", add: "The publish step after aggregation is `finish_album_job`: it takes an `AlbumSelection` from any source, records its stats and exclusions, ends the job at once when nothing is eligible and otherwise runs enrichment. A Spotify export will call it with its own selection; the Last.fm-only stats (`pages_fetched` and the page-loss notice) are written by `_fetch_and_process` before it."
- Render the diagram with the Mermaid validator.

`docs/agents/FINDINGS.md`, F-B23-1: before the `Source:` of its Status paragraph insert `The threshold half landed in Task 23d (plays.select_albums returns the exclusions without a job and finish_album_job publishes them); the release-scope half in _build_results is still open.`

`BATCH23_DEFINITION.md`: WP-3's first bullet (`- [ ] \`export_album_task\` parses in \`asyncio.to_thread\`, closes the buffer, then runs the existing threshold partition, stats, unmatched records and \`_process_filtered_albums\`, mapping \`ExportError\` to a classified code through \`jobs.fail\`.`) becomes exactly:

```
- [ ] `export_album_task` parses in `asyncio.to_thread`, closes the buffer,
  then calls `plays.aggregate_albums`, `plays.select_albums` (the one
  threshold partition and exclusion cap) and `orchestrator.finish_album_job`
  with the request's `album_request.AlbumRequest` (built by
  `parse_album_request(..., require_username=False)`, so its `username` is
  `None`) -- the one publish step: stats, unmatched records, the "no album
  passes" ending, then enrichment -- mapping `ExportError` to a classified
  code through `jobs.fail`.
```

WP-3's acceptance start (`- **Acceptance:** \`process_albums\` receives the aggregate;` / `\`fetch_all_recent_tracks_async\` is never called, proven by patching it to` / `raise;`) becomes `- **Acceptance:** \`process_albums\` receives the selection's eligible albums;` / `\`lastfm.fetch_scrobbles\` is never called, proven by patching it to` / `raise;`. WP-2's acceptance sentence "The aggregator's output feeds `partition_albums_by_threshold` unchanged." becomes "The aggregator's output feeds `plays.select_albums` unchanged."

The unexecuted Spotify-export plan (`docs/superpowers/plans/2026-09-13-batch23-spotify-export-import.md`) is a dated plan and is not annotated: it stays as written, and WP-2's and WP-3's executors read the amended `BATCH23_DEFINITION.md`.

Sweep: `git grep -n -e _fetch_job_albums -e _record_lastfm_stats -e _cap_threshold_exclusions -e "fetch_all_recent_tracks_async" -- . ':!docs/history' ':!docs/logarchive' ':!docs/superpowers/plans' ':!tests' ':!scrobblescope/lastfm.py'`
Expected hits: only `BATCH23_DEFINITION.md`'s checked, dated Part A line naming `_cap_threshold_exclusions` (a point-in-time record). Anything else is stale.

- [ ] **Step 11: Section 4 entry, gates, commit**

Entry heading: `### <commit date> - One album selection and one publish step`. Body: scope; owner intent (review card B-3, "one typed album aggregate built from normalized plays, the same for a Last.fm job and an export job, and one publish step after aggregation... No sentinel returns from the aggregation", Task 23 brief); what changed, including that `finish_album_job` takes PR #3's `AlbumRequest`; the WP-3 and WP-2-acceptance amendments to `BATCH23_DEFINITION.md` and why they are this PR's (the tranche spec's documentation rule); deviations (none; the interim metadata dict of Task 4 is gone); mutation evidence; validation.

Commit body names every edited test: `tests/services/test_lastfm_logic.py` (8 tests unpack `(selection, summary)`; the stats test is renamed), `tests/services/test_orchestrator_fetch_and_process.py` (12 patch return values), `tests/services/test_orchestrator_helpers.py::test_lastfm_page_loss_is_recorded_as_a_kind_beside_its_sentence` (replaced, with one sibling added), `tests/test_provider_fixtures.py::test_lastfm_fixture_flows_through_fetch_top_albums`, plus the new `tests/services/test_finish_album_job.py` and additions to `tests/test_plays.py`.
Subject: `refactor(orchestrator): Publish one typed album selection` (57 characters).

---

## Self-Review

**1. Spec coverage** (spec "PR #4" row and the master plan's P4 "Must cover"):

| Requirement | Where |
|---|---|
| 23a parity tests, first | Task 1 |
| 23b public names across modules | Task 3 |
| 23c scrobbles not pages | Task 4 |
| 23d one typed album selection and one publish step | Task 5 |
| Usernames leave every log line (F-B23-40): `heatmap.py` fetch timing, `lastfm.py` private-profile line, `heatmap._report_heatmap_failure`, job id where a line needs correlation | Task 2 (the three named lines, five more username lines found in the same sweep, and the request-cache hit line; the three route lines of the sweep left with PR #3) |
| `BATCH23_DEFINITION.md` WP-2 amendment naming the record shape | Task 4 Step 13 (exact text); the WP-3 text and WP-2's acceptance sentence that Tasks 4-5 make untrue, Task 5 Step 10 (in scope by the tranche spec's documentation rule) |
| Each task has `Touches:` and `After:`; one atomic commit with its own untagged Section 4 entry (heading and subject, measured) | every task |
| Docs follow the code: `docs/architecture/*.md`, SESSION_CONTEXT Sections 3-4 | Tasks 3, 4, 5 |
| Parity tests precede the refactor; mutation evidence for new tests | Tasks 1-5 |
| Which 23b-d steps depend on PR #3 and how they adapt | "Dependence on PR #3" |
| Assumptions checked and which held | "Assumptions checked" |
| Hosting cost ceiling | Global Constraints; Task 4 Step 12 (20 MB budget, stop rule) |
| Whole-PR review before push | Global Constraints |

**2. Placeholder scan:** the only deferred values are things that exist only when the work is done: the commit date in each Section 4 heading, N (the measured test count) and the three memory numbers. No "TBD", "similar to", or step without its code.

**3. Type consistency:** `Play`, `Window`, `AlbumAggregate(albums, plays_seen)`, `AlbumSelection(eligible, exclusions, total_below_threshold, plays_seen, unique_albums)`, `FetchSummary(pages_expected, pages_received)`, `ScrobbleFetch(plays, summary, dropped_undated, dropped_malformed)` are used with the same field names in `plays.py`, `lastfm.py`, `heatmap.py`, `orchestrator`, `tests/helpers.py::lastfm_albums` and every test. `select_albums` is `(aggregate, min_plays, min_tracks, exclusion_cap)` in Task 5's definition, tests and `fetch_top_albums_async`. `finish_album_job(job_id, selection, album, *, overall_start_time)` reads `_process_filtered_albums`'s parameters (`include_unmatched` included) from the `AlbumRequest`, whose ten field names are PR #3's. Task 1's `lastfm_edge` patches `scrobblescope.lastfm.*` names that exist before and after Task 4.

**Hand-offs to other PRs.** PR #5 (metadata encoding) builds on the public cache names of Task 3 and touches none of `plays.py`. PR #6 (statistics) builds on `plays.Play` and `plays.aggregate_albums`/`aggregate_daily_counts`, both of which gain WP-6's fields (first listen, one original track name per key) in one place; it also amends `BATCH23_DEFINITION.md` WP-6, whose sentence "Both aggregators keep one original track name per normalized key" is left untouched here.

## Owner questions

None. The first draft's three questions were decided by the controller (see Revision 1): the memory budget is a measured stop rule (Task 4 Step 12), the WP-3 amendment is in scope by the tranche spec's documentation rule, and dated plans stay as history.

## Revision 1 (2026-10-20)

Each finding of `plan-review.md` (Needs fixes: 4 Important, 7 Minor), and what changed.

| Finding | Change |
|---|---|
| I1. The cache key still carries the username; the privacy tests could not see it | Task 2 adds `utils.get_cached_response`'s hit line as a ninth change (`logging.debug("Cache hit for %s", url)`), with `utils.py` and the `RedactingFormatter` docstring in `api_logging.py` in Touches (Step 4). New `test_a_cache_hit_logs_no_listener` leaves `get_cached_response` real, seeds `REQUEST_CACHE` with a `LISTENER` params dict, asserts a "Cache hit" record exists and the listener is absent; planted defect: restore `{key}`; mutation row 9. Every count is corrected: eleven lines in five files at 5dde407, plus the twelfth carrier; after PR #3 nine lines in four files (Task 2 intro, assumptions row, Section 4 entry, FINDINGS text, self-review). |
| I2. Task 2 written for 5dde407 although it runs after #3 | Task 2 rewritten on #3's approved plan: the three lines #3 removes (registration-year warning, two heatmap pre-check lines) and their two tests, the `tests/test_routes.py` edit and Step 4 are gone; Touches no longer names `routes/*_flow.py`; the preamble states that Tasks 2-5 assume #3 has merged. |
| I3. Adaptation table incomplete or wrong | "Dependence on PR #3" rewritten as a list of what #3 changes plus a per-task call-site table: Task 1 `_run_heatmap_task` -> `heatmap_task(job_id)` (the `_run_album_job` edit was a no-op and is dropped); Task 2 `heatmap_task(job_id)` and `background_task(job_id)` from records that carry `LISTENER` (each test asserts `jobs.params(job_id)["username"] == LISTENER` first, so it cannot pass vacuously); Task 4 `heatmap_task(job_id)` on a heatmap record. Task 5's contingency is decided: `finish_album_job(job_id, selection, album, *, overall_start_time)` takes #3's ten-field `AlbumRequest` (`username` is `None` for an export); `_fetch_and_process` builds one from its positional parameters; the WP-3 text follows (Step 10). |
| I4. About a dozen new tests without a planted defect or mutation row | Every new Task 4 and Task 5 test now names a defect, and every defect has a row I traced against the test's own data. Task 4: the table grows from 13 to 32 rows (e.g. `test_a_utc_play_keeps_its_fields`, the split Window tests, `test_no_plays_give_an_empty_aggregate`, `test_identical_plays_each_count`, `fetch_scrobbles` hands-back, summary, pass-through and no-listening-facts tests, the unreadable-entry test, the two new heatmap tests, the fixture test). Task 5: the table grows from 10 to 13 rows (stats published, complete-fetch test). Deleted as asserting nothing a stronger test does not: `test_it_accepts_a_counter` (the Counter path is dead), `test_a_selection_under_the_cap_keeps_every_exclusion` and `test_a_selection_is_an_albumselection`. |
| M1. Count slips | Task 4: eight `TestAggregateDailyCounts` tests converted (the ninth in the new class is new); the class docstring says the eight keep their assertions. Task 5 commit body: 8 tests unpack `(selection, summary)`. |
| M2. Near-duplicates of existing failure-logging tests | Task 2 drops its own handler test and the two pre-check tests; `_assert_type_only_at_error` in `tests/services/test_failure_logging.py` gains an optional `listener` and three existing tests pass it (named in the commit body); the new file keeps only what is new (heatmap run, album run, the two thread-entry backstops, the page-layer pair, the cache hit). |
| M3. Test names that promise more than they assert | `test_a_selection_with_nothing_eligible_ends_the_job_once` now asserts `jobs.succeed` is called once with the empty-result message (mutation row 7 calls it twice); the type-check test is deleted. |
| M4. Misattributed quote | Task 2 Why and its entry cite the tranche spec's own wording, "Last.fm usernames leave the logs (F-B23-40)". |
| M5. Task 4 sweep names too few expected hits | Step 13 says F-B23-2's problem text (which names `heatmap._aggregate_daily_counts`) stays as the historical statement, and lists those lines as expected hits. |
| M6. Log noise on an outage accepted without saying so | Task 4's behaviour-change paragraph and entry body state the extra class-only ERROR line on a plain Last.fm outage and accept it. |
| M7. Parity gap for G3 | Task 1's `test_scrobbles_outside_the_year_are_not_counted` also asserts `total_scrobbles == 24` (out-of-window entries are counted); mutation row 19 (19 rows now). |
| Q1. Memory ceiling | Not the owner's. Task 4 Step 12 now has a stated budget (20 MB peak added per 80,000-scrobble job, from 512 MB, five job slots) and a stop rule: above it, Task 4 does not commit and the number goes to the controller. The cache-the-normalized-pages option stays a separate decision. |
| Q2. WP-3 text in scope | Not the owner's. Global Constraints cites the spec's rule ("the same PR amends `BATCH23_DEFINITION.md`") and says which text: WP-2 (Task 4 Step 13), and in Task 5 Step 10 WP-3's first bullet, the start of WP-3's acceptance and WP-2's acceptance sentence about `partition_albums_by_threshold`. WP-6 stays for PR #6. |
| Q3. Annotating the export plan | Not the owner's. Dated plans stay as history; the conditional paragraph in Task 5 Step 10 is replaced by a sentence saying the plan is not annotated. |
