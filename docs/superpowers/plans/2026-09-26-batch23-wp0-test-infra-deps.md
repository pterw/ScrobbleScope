# Batch 23 WP-0 test-infrastructure and dependencies plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear the third and last cluster of `BATCH23_DEFINITION.md` WP-0 Part C --
F-LOAD-2, F-MAS-1 and F-B21-3's remainder -- so Batch 23 WP-0 can close with no open
test-infrastructure or dependency defect. This is item 3 of "After this plan" in
`docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`.

**Out of scope.** The release-check worker log lines the same section once assigned here
moved to the control-plane plan's Task 13 on 2026-09-24 as F-B23-6; that finding is
`RESOLVED` (`docs/history/findings/FINDINGS_ARCHIVE.md`, "provider calls leave no trace in
the log"). Nothing in this plan touches provider-call logging.

**Architecture:** Four independent tasks. Tasks 1-3 touch disjoint files and carry no
`After:`, so their code phases may run in parallel. Task 4 edits the CI workflow that
Task 3's dependency move feeds, so it waits for Task 3 to land.

1. **F-LOAD-2** -- a real-thread integration test through the album pipeline's actual
   entry point, mocking only the provider network boundaries.
2. **F-MAS-1** -- fixtures transcribed from Last.fm's and Spotify's published API
   references, plus shape tests catching the app's own assumptions drifting from them; a
   weaker guarantee than a contract test, since it cannot catch the providers drifting.
3. **F-B21-3's remainder** -- move `virtualenv`, `distlib`, `filelock` and `platformdirs`
   from `requirements.txt` to `requirements-dev.txt`, still pinned; a live `pip-audit`
   recount recorded in the finding's resolution.
4. **The CI audit's blind spot** -- `requirements-dev.txt` is never in `pip-audit`'s
   inputs, so a vulnerable dev-only pin would never be flagged; add it to the one
   workflow step that runs the audit.

**Tech Stack:** Python 3.13 stdlib (`threading`, `unittest.mock`), pytest,
`pytest-asyncio`, Flask test client, `pip-audit`. No new dependency.

## Global Constraints

Every task's requirements include this section.

- **Qualified interpreter only.** This is a linked worktree; the venv lives in the
  primary checkout. Use `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"`
  and its sibling `pytest.exe` / `pre-commit.exe` / `pip-audit.exe` in the same
  `Scripts/` directory. Never bare `pip`, never a second venv. Quote every path.
- **No new dependency, no version change** without the owner's approval
  (`AGENTS.md` "Environment Setup"). Task 3 moves four existing pins between files; it
  changes no version.
- **Bookkeeping is a landing concern, not a task concern.** No task's `Touches:` includes
  `docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, `docs/agents/FINDINGS.md`,
  `docs/history/findings/FINDINGS_ARCHIVE.md`, the log archive, this plan's own
  checkboxes, or the `[test_count]` pin in `config/docsync.toml`. Once a task's own files
  are correct and its tests pass, a landing: (1) writes the untagged
  `docs/agents/PLAYBOOK.md` Section 4 entry, directly after
  `<!-- DOCSYNC:CURRENT-BATCH-END -->`, opening "Side task, no batch tag: ... part of
  Batch 23 WP-0" (owner ruling, 2026-09-23); (2) runs the full suite (below) to read N;
  (3) resolves the task's finding in `docs/agents/FINDINGS.md`, replacing its `Status:`
  line with the canonical form
  `` - [x] **Status:** resolved`` / `` **Completed:** <date>`` / `<reason, per task>`;
  (4) runs `python scripts/doc_state_sync.py --fix --test-count N`, which rotates the
  resolved record into `FINDINGS_ARCHIVE.md`, refreshes `.claude/SESSION_CONTEXT.md`, and
  pins N in `config/docsync.toml` -- never hand-edit any of those four count sites;
  (5) stages every changed path by name (never `git add -A` / `git add .`), then
  `pre-commit run --all-files`, re-staging anything a hook rewrites; (6) runs
  `python scripts/doc_state_sync.py --check`, which must exit 0 (the root
  `BATCH23_DEFINITION.md` warning is the one expected exception); (7) commits
  (`AGENTS.md` "Commit Rules": Conventional Commits, imperative mood, no trailing period,
  subject <=72 chars, body explains why; no `Co-authored-by` or attribution line; never
  `--no-verify`, fix and restage instead), one commit per task, never mixing two tasks'
  work. (`frontend_gate.py` would also run for a task touching `static/`, `templates/` or
  `scripts/dev/_frontend_gate_*` -- no task here does.)
- **Measure the count.**
  `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider`
  Quote it in the Section 4 entry as `` `pytest -q` -- **N passed** ``; the untracked
  mutation-runner tests are excluded, since they are not repository state.
- **A change to a check is accepted only on a live probe**: red on a planted defect,
  green on its near miss, both run locally before the workflow file is trusted. Task 4
  says exactly how.
- **Untracked files belong to other agents.** Never stage, edit or delete them: the
  mutation runner, its scope file and tests, `progress_copy.md`, the review HTML files,
  `plan.md`, the audit documents, and anything under `.superpowers/`.
- **ASCII only** in every file: `--`, not an em dash.
- **The pre-commit `worktree-alignment` hook prints an advisory `WT005` line and still
  passes.** Do not act on it.

---

### Task 1: A real thread runs the album pipeline end to end (F-LOAD-2)

**Touches:**
- Create: `tests/test_pipeline_integration.py`

**After:** none. **Interfaces:** none produced or consumed; self-contained.

**Why the album pipeline, not the heatmap one.** The finding's roadmap line names
`/results_loading -> /progress -> /results_complete`, the album flow
(`scrobblescope/routes/album_flow.py`), entered via
`scrobblescope.orchestrator.background_task(job_id, username, year, sort_mode,
release_scope, decade=None, release_year=None, min_plays=10, min_tracks=3,
limit_results="all")` and started only through `worker.start_job_thread` -- a call every
existing test patches away (`tests/test_routes.py`), so none exercises the real
`threading.Thread`, per-thread event loop (`worker.new_thread_event_loop`), or
`jobs_lock`-guarded job store under concurrent access from a polling client. That is what
"no integration tests in CI" means here.

**What stays mocked (genuine network boundaries, not business logic):**
`scrobblescope.routes.check_user_exists` / `.check_profile_is_public` (the Last.fm
preflight); `scrobblescope.orchestrator.fetch_all_recent_tracks_async` (Last.fm's
scrobble pages); `.fetch_spotify_access_token`, `.search_for_spotify_album_id`,
`.fetch_spotify_album_details_batch`, `.create_optimized_session` (the Spotify calls,
mocked exactly as `tests/services/test_orchestrator_process_albums.py`
`test_process_albums_persists_a_spotify_row_through_the_contract` already does);
`._get_db_connection` (`AsyncMock` returning a bare connection), `._batch_lookup_metadata`
(returns `{}`) and `._batch_persist_metadata` (no Postgres in the test environment); and
`.enqueue_release_check` -- the happy path calls this unconditionally, and unpatched it
would start a real MusicBrainz worker thread and live lookup whenever
`MUSICBRAINZ_ENABLED`/`MUSICBRAINZ_CONTACT` happen to be set in this environment.

**Not mocked:** `worker.start_job_thread`, `worker.acquire_job_slot`,
`orchestrator.background_task`, `._fetch_and_process`, `.fetch_top_albums_async`,
`.process_albums`, and every `repositories.py` job-store function -- exactly the code
F-LOAD-2 says nothing exercises.

- [x] **Step 1: Write the test.** One scrobble, one album, no cover art needed on the
  Spotify side (a details payload with only `release_date` is enough, since Task 4 of
  the reconcile plan already proved a sparse payload degrades cleanly).

```python
import time
from unittest.mock import AsyncMock, MagicMock, patch

from scrobblescope.repositories import get_job_progress


def test_album_pipeline_runs_on_a_real_thread_end_to_end(client):
    """
    GIVEN a real POST to /results_loading, with only network calls mocked
    WHEN the test polls the real /progress endpoint, as a browser does
    THEN the job reaches its terminal state through the real thread, event
    loop and job-store lock, and actually reaches the Spotify phase (F-LOAD-2).
    """
    # 2025-06-15T12:00:00Z: inside fetch_top_albums_async's year=2025 window
    # (orchestrator/__init__.py:118-119); an out-of-window uts is silently
    # dropped at :144-149 before albums is ever built.
    lastfm_page = {
        "recenttracks": {
            "track": [
                {
                    "artist": {"#text": "Fleetwood Mac"},
                    "album": {"#text": "Rumours"},
                    "name": "Dreams",
                    "date": {"uts": "1749988800"},
                }
            ],
            "@attr": {"page": "1", "totalPages": "1"},
        }
    }

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)
    o = "scrobblescope.orchestrator."

    with (
        patch("scrobblescope.routes.check_user_exists", return_value={"registered_year": 2000}),
        patch("scrobblescope.routes.check_profile_is_public", return_value=True),
        patch(o + "fetch_all_recent_tracks_async", new_callable=AsyncMock,
              return_value=([lastfm_page], {"status": "ok", "pages_expected": 1, "pages_received": 1})),
        patch(o + "fetch_spotify_access_token", new_callable=AsyncMock, return_value="tok"),
        patch(o + "create_optimized_session", return_value=mock_session_ctx),
        patch(o + "search_for_spotify_album_id", new_callable=AsyncMock, return_value="sp1") as mock_search,
        patch(o + "fetch_spotify_album_details_batch", new_callable=AsyncMock,
              return_value={"sp1": {"release_date": "1977-02-04"}}) as mock_details,
        patch(o + "_get_db_connection", new_callable=AsyncMock, return_value=AsyncMock()),
        patch(o + "_batch_lookup_metadata", new_callable=AsyncMock, return_value={}),
        patch(o + "_batch_persist_metadata", new_callable=AsyncMock),
        # Closes the unconditional MusicBrainz call (orchestrator/__init__.py:619)
        # by mock, not by accident of MUSICBRAINZ_ENABLED/_CONTACT in this env.
        patch(o + "enqueue_release_check"),
    ):
        resp = client.post(
            "/results_loading",
            # min_plays/min_tracks=1: thresholds are inclusive minimums, and one
            # scrobble gives play_count=1 and one unique track -- the route's
            # defaults (10, 3) would exclude it before Spotify is reached.
            data={"username": "flounder14", "year": "2025", "min_plays": "1", "min_tracks": "1"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        job_id = resp.headers["Location"].rsplit("job_id=", 1)[-1]

        deadline = time.time() + 10
        progress = get_job_progress(job_id)
        while progress is not None and progress.get("progress", 0) < 100 and not progress.get("error"):
            assert time.time() < deadline, "background thread did not finish in time"
            time.sleep(0.05)
            progress = get_job_progress(job_id)

    assert progress is not None
    assert progress.get("error") is not True, progress
    assert progress["progress"] == 100
    # The point of this test: the album survived filtering and actually
    # reached the Spotify phase, not just a job that completed emptily.
    mock_search.assert_awaited_once()
    mock_details.assert_awaited_once()
```

  If `results_loading`'s actual redirect shape differs from the sketch (check
  `album_flow.py`'s `redirect(url_for(...))` call), read `job_id` from wherever it really
  is -- do not change what the test proves, only how it reads the id.

- [x] **Step 2: Run it to verify it fails for the right reason first.** Temporarily
  revert one mock (e.g. `check_user_exists`) and confirm the test fails on a real network
  call, not by accident; restore it. Then temporarily drop the `min_plays`/`min_tracks`
  override and confirm it fails on `mock_search.assert_awaited_once()`, proving the
  threshold override is load-bearing too; restore it.

- [x] **Step 3: Run it for real.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_pipeline_integration.py -q`
Expected: 1 passed. If it hangs, the semaphore in `tests/conftest.py`'s `fresh_job_slots`
fixture already resets `MAX_ACTIVE_JOBS` per test, so a hang means a mock is missing, not
a leaked slot from an earlier test -- add whichever provider call the traceback names.

- [x] **Step 4: Run the full suite once**, to confirm the new thread does not race any
  other test's shared state (`JOBS`, `REQUEST_CACHE`):

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider`
Expected: all pass, count N noted for the landing.

**Resolves:** F-LOAD-2. Landing's reason sentence: "`tests/test_pipeline_integration.py`
drives `/results_loading` through the real `worker.start_job_thread`, `background_task`
and job store, mocking only the Last.fm, Spotify and MusicBrainz network boundaries, and
asserting the Spotify phase was actually reached."

---

### Task 2: Fixtures transcribed from the providers' own docs, plus shape tests (F-MAS-1, Q7 = a)

**Touches:**
- Create: `tests/fixtures/spotify_get_album.json`
- Create: `tests/fixtures/lastfm_recenttracks_page.json`
- Create: `tests/test_provider_fixtures.py`

**After:** none. **Interfaces:** none produced or consumed; self-contained. A later plan
may point other tests at these fixtures, but nothing here requires that.

**What "transcribed from published docs" means.** Each fixture is typed in by hand from
the provider's own reference page, not captured live and not built to match what the
app's existing mocks already assume. `spotify_get_album.json`: Spotify Web API "Get an
Album" object (developer.spotify.com/documentation/web-api/reference/get-an-album),
trimmed to what `scrobblescope.spotify.album_metadata_from_details` reads --
`release_date`, `images` (list of `{url, height, width}`), `external_urls.spotify`,
`tracks.items` (`name`, `duration_ms`) -- plus one sibling field the app ignores (e.g.
`album_type`), so the shape test proves the app reads a subset, not an exact match.
`lastfm_recenttracks_page.json`: Last.fm's `user.getRecentTracks` response
(www.last.fm/api/show/user.getRecentTracks), trimmed to one `track` entry carrying
`artist.#text`, `album.#text`, `name` and `date.uts`, plus the `@attr` paging block.

**Why this is a weaker guarantee, stated once for the record.** A shape test here catches
the app's *own* code reading a field the docs don't promise, or missing one they do. It
cannot catch Spotify or Last.fm silently changing their real response -- that needs a
recording library or a live contract test, which Q7's answer explicitly declines for now.

- [ ] **Step 1: Write the two fixture files** as plain JSON, following the field lists
  above. Keep each under 40 lines; this is a documentation artifact, not a full payload.

- [ ] **Step 2: Write the shape tests.**

```python
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIXTURES / name).read_text())


def test_spotify_fixture_has_every_field_the_app_reads():
    """A field the app reads but the doc-transcribed fixture lacks would
    already fail here (F-MAS-1)."""
    from scrobblescope.spotify import album_metadata_from_details

    album = _load("spotify_get_album.json")
    meta = album_metadata_from_details("sp1", album)

    assert meta.release_date == album["release_date"]
    assert meta.url == album["external_urls"]["spotify"]
    assert meta.image_url == album["images"][0]["url"]
    assert meta.track_durations  # at least one track survived translation


def test_lastfm_fixture_has_every_field_the_app_reads():
    """The recenttracks fixture carries every field callers key off of."""
    page = _load("lastfm_recenttracks_page.json")
    track = page["recenttracks"]["track"][0]

    assert track["artist"]["#text"]
    assert track["album"]["#text"]
    assert track["name"]
    assert track["date"]["uts"].isdigit()


def test_existing_spotify_mocks_do_not_drift_from_the_transcribed_shape():
    """An existing mock's keys must be a subset of the doc-transcribed
    fixture's -- the regression guard Q7 asks for."""
    fixture_keys = set(_load("spotify_get_album.json"))
    sample_mock_payload = {
        "release_date": "2025-01-01",
        "images": [{"url": "https://img.example.com/a.jpg"}],
        "external_urls": {"spotify": "https://open.spotify.com/album/sp1"},
        "tracks": {"items": [{"name": "Track One", "duration_ms": 240000}]},
    }
    assert set(sample_mock_payload) <= fixture_keys
```

  The third test's `sample_mock_payload` is a stand-in the task author copies from the
  actual literal used in `tests/services/test_orchestrator_process_albums.py`
  `test_process_albums_persists_a_spotify_row_through_the_contract` (Task 5 of the
  reconcile plan) -- read that literal and use its real keys, so the assertion is
  checking the suite's own mock, not a copy invented for this test.

- [ ] **Step 3: Run the new tests.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_provider_fixtures.py -q`
Expected: 4 passed.

- [ ] **Step 4: Run the full suite once**, count N for the landing.

**Resolves:** F-MAS-1. Landing's reason sentence: "`tests/fixtures/` holds Spotify and
Last.fm response shapes transcribed from each provider's published reference;
`tests/test_provider_fixtures.py` pins the app's own field reads against them and checks
one existing mock for drift -- a weaker guarantee than a live contract test, recorded as
such (Q7 answer a)."

---

### Task 3: Move four dev-only pins out of the production install (F-B21-3 remainder, Q6 = a)

**Touches:**
- Modify: `requirements.txt` (remove four lines)
- Modify: `requirements-dev.txt` (add the same four lines, same pins)

**After:** none. **Interfaces:** none. `requirements-dev.txt` already opens with
`-r requirements.txt`, so every package removed from the production file stays installed
in a dev environment.

`virtualenv==20.36.1`, `distlib==0.3.9`, `filelock==3.20.3` and `platformdirs==4.3.6` are
`virtualenv`'s own dependency closure -- packaging/environment tooling, imported nowhere
in `scrobblescope/` (confirm with the Step 1 grep). They are the remainder of F-B21-3:
its other two problems (`pypdf`/`pdf2image`/`pillow`/`ipinfo`/`cachetools` removed, and
`requests`/`urllib3` upgraded past their advisories) are already fixed on `main`
(`0f5b2468`, `c1620a9d`) and are not touched again here.

- [ ] **Step 1: Confirm nothing imports them.**

```bash
git grep -n -e "^import virtualenv" -e "^import distlib" -e "^import filelock" -e "^import platformdirs" -e "from virtualenv" -e "from distlib" -e "from filelock" -e "from platformdirs" -- '*.py'
```

Expected: no hits. If any exist, stop and report NEEDS_CONTEXT -- the finding's premise
(dev tooling, not a runtime import) would be wrong for that package.

- [ ] **Step 2: Move the four lines.** Delete `distlib==0.3.9`, `filelock==3.20.3`,
  `platformdirs==4.3.6` and `virtualenv==20.36.1` from `requirements.txt`, keeping the
  remaining lines' alphabetical order intact. Add the same four pins to
  `requirements-dev.txt`, in alphabetical position among its existing seven package lines
  (`pip-audit`, `ruff`, `pre-commit`, `playwright`, `pytest`, `pytest-asyncio`,
  `pytest-cov`, below its `-r requirements.txt` line).

- [ ] **Step 3: Reinstall and confirm nothing production-facing broke.**

```bash
"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pip.exe" install -r requirements-dev.txt
```

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider`
Expected: all pass -- these four were already installed as transitive tooling
dependencies, so moving their pin file changes nothing importable.

- [ ] **Step 4: Record a live `pip-audit` recount**, both before and after, so the
  finding's resolution states a real number rather than repeating the 2026-08-21 one:

```bash
"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pip-audit.exe" -r requirements.txt
"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pip-audit.exe" -r requirements.txt -r requirements-dev.txt
```

Note both counts (vulnerabilities found, packages affected) in the Section 4 entry and in
the finding's resolution reason -- this is the "live pip-audit recount" the scope asks
for; do not carry forward the stale 115/12 figure.

**Resolves:** F-B21-3 in full (not just its remainder -- the prior commits closed the
other two parts). Landing's reason sentence: "the unused PDF-adjacent packages were
already removed and `requests`/`urllib3` already upgraded past their advisories
(`0f5b2468`, `c1620a9d`); the remaining unused-tooling pins (`virtualenv`, `distlib`,
`filelock`, `platformdirs`) are now moved to `requirements-dev.txt`, still pinned; a live
`pip-audit` recount on <date> found <N> vulnerabilities in <M> packages against
`requirements.txt` alone, <N2> against both files together" (landing fills in Step 4's
four numbers).

---

### Task 4: Audit the dev requirements too (CI input gap)

**Touches:**
- Modify: `.github/workflows/test.yml` (the "Security audit (pip-audit)" step's `inputs:`)

**After:** Task 3 -- sequencing only (its live probe reads more clearly once
`requirements-dev.txt` holds Task 3's real pins); no code dependency. **Interfaces:** none.

Today's step (`.github/workflows/test.yml:130-134`) passes `inputs: requirements.txt`
only, so a vulnerable pin anywhere in `requirements-dev.txt` -- including the four Task 3
just added -- is never flagged by CI, `continue-on-error` or not.

- [ ] **Step 1: Confirm the pinned action's syntax for multiple input files.** Check
  `pypa/gh-action-pip-audit@v1.1.0`'s `action.yml` (fetch the tag, or read the runner's
  cached copy from a prior CI run) for whether `inputs:` takes a newline- or
  space-separated list, and use whichever it documents.

- [ ] **Step 2: Edit the step.**

```yaml
      - name: Security audit (pip-audit)
        uses: pypa/gh-action-pip-audit@v1.1.0
        with:
          inputs: requirements.txt requirements-dev.txt
        continue-on-error: true
```

  (Replace the `inputs:` value with the newline-separated form from Step 1 if that is
  what v1.1.0 documents instead.)

- [ ] **Step 3: Live probe, red on a planted defect.** In a scratch copy of
  `requirements-dev.txt` (never committed), pin one existing dev package to a version
  `pip-audit` currently reports as vulnerable (find a real, current CVE/GHSA id by
  running `pip-audit -r <scratch file>` first -- the advisory feed changes over time, so
  do not hardcode a package/version pair into this plan). Run:

```bash
"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pip-audit.exe" -r requirements.txt -r <scratch file>
```

  Expected: the planted advisory is reported. The workflow step itself is not run
  locally; this local invocation with the same two inputs is the proof that the change
  under test -- auditing the dev file at all -- works.

- [ ] **Step 4: Live probe, green on the near miss.** Revert the scratch file to the
  real, pinned `requirements-dev.txt` and rerun the same command. Expected: that
  package's advisory no longer appears.

- [ ] **Step 5: Run the full suite once**, count N for the landing (unchanged from
  Task 3's, since this task changes no Python).

**Resolves:** no finding by itself -- it closes the scope item "add requirements-dev.txt
to the CI audit's inputs", which is not filed under its own F-* id. The landing's Section
4 entry states the live-probe result from Steps 3-4 (which advisory was planted, and that
it disappeared on the near miss) in place of a resolution reason.

---

## Open questions

None.
