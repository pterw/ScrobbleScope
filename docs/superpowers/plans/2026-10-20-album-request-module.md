# Album request module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One module turns the album form into a validated request or a typed refusal, one Last.fm pre-check answer (with a short timeout of its own) serves the album, heatmap and validate routes, and one admission path starts every job with its parameters on the job record.

**Architecture:** Seven tasks on `refactor/album-request-module`, each its own atomic commit. Task 1 pins today's route behaviour; Tasks 2-4 add the pure request module, the pre-check and the admission module with their own tests; Tasks 5-6 move the album route and then the heatmap and validate routes onto them; Task 7 makes the job kind an explicit record field and amends `BATCH23_DEFINITION.md` WP-4. The design is review card B-1 (`docs/history/reports/architecture-review-20260930-0040.html`) and the Task 26 brief; the tranche rulings are `docs/superpowers/specs/2026-10-20-pre-batch23-tranche-design.md` (PR #3 in its table) and the order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` (P3).

**Tech Stack:** Python 3.13, Flask (blueprint `main`), asyncio threads (`utils.run_async_in_thread`, `worker`), pytest, ruff, pre-commit, docsync (`scripts/doc_state_sync.py`), Mermaid.

## Global Constraints

- Every commit is atomic and carries its own untagged PLAYBOOK Section 4 entry, placed directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` line (AGENTS.md "Side-Task Handling").
- Commit procedure, every commit, in this order (AGENTS.md "Commit Rules"): write the Section 4 entry; `pytest -q` and measure N; `doc_state_sync.py --fix --test-count N` (bare `--fix` when N is unchanged); stage by name, never `git add -A` or `git add .`; `pre-commit run --all-files` and re-stage anything a hook rewrote; `doc_state_sync.py --check` exits 0; commit.
- Commit subject `<type>(<scope>): <Capitalised imperative>`, at most 72 characters; body explains why. No `Co-authored-by` trailer.
- From the linked worktree `C:/ssw/arm`, every Python command uses the primary checkout's interpreter. In the commands below `PY` stands for `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"` (and `pre-commit.exe`, `ruff.exe` sit beside it).
- Markdown is ASCII only (`--`, never an em dash). Cite code by name, not line number.
- New tests assert intended behaviour, not the code as written, and each comes with mutation evidence: the planted defect named and the test shown failing. Restore a committed file with `git checkout -- <path>`; for a file not yet committed, `git add` it first so `git checkout -- <path>` restores it.
- Refactor requires parity tests (AGENTS.md): Task 1 precedes every change to existing behaviour. A test is added only if no existing test already asserts the same thing (AGENTS.md anti-pattern 1); the existing tests Task 1 relies on are named there.
- Existing Last.fm tests stay unmodified except where a task names them (`BATCH23_DEFINITION.md` Intended outcome, owner ruling 2026-09-29). A commit that edits an existing test names every edited test in its body.
- `BATCH23_DEFINITION.md` is amended in the same PR when a seam changes what a work package may assume: this PR amends WP-4 (Task 7), with the exact text given there.
- Each seam PR updates its own architecture diagrams and SESSION_CONTEXT Sections 3-4 in the commit that changes them. Do not change any "Last verified" date: the documentation PR (#8) owns them.
- Hosting cost ceiling (spec): nothing in this PR keeps the production database awake, adds a machine or adds a service. It adds no database traffic and no dependency.
- Browser gates run one at a time on the owner's machine. Only Task 7 runs the frontend gate.
- `WT003 refactor/album-request-module` and `WT010` are expected advisories from the `worktree-alignment` hook; the hook still passes.
- Do not push. The controller pushes and opens the PR.
- Mermaid blocks edited here are validated with the `validate_and_render_mermaid_diagram` MCP call before commit; a sequence-diagram message must not contain `;`.
- The Last.fm username is listener data: no new log line this PR writes may contain it (it goes in the job id's place or nowhere).

## Assumptions checked against `C:/ssw/kb` (5dde407)

| Assumption (source) | Held? | What the code shows |
|---|---|---|
| Task 26 brief: builds "on Task 22's job module" | Held | `scrobblescope/jobs.py` has `create`, `context`, `JobStore`, `MemoryJobStore`, `use_store`. |
| Brief: ten job parameters re-passed positionally | Held | `results_loading` builds ten params, then `start_job_thread(background_task, args=(11 values))`; `background_task` re-passes them to `_fetch_and_process`. Eleven with `include_unmatched` (PR #1) counted; the brief's "ten" counted without `mode`. |
| Brief: one `try` swallows a pre-check outage and starts the job | Held, in new form | After PR #256 the order is exists, then privacy, then registration hint, still in one `try ... except Exception` that logs "Registration year check failed ... proceeding" and falls through to `acquire_job_slot`. The heatmap route answers 503 retryable. |
| Brief: sets are defined in `domain.release_window`, the sort modes and the limit options; "do not invent new sets" | **Did not hold** | `release_window` owns the scope-to-years rule but not the set of valid scopes (an unknown scope returns `None`, meaning every year). Sort modes and limit options have no Python owner: they exist only as `<option>`/radio values in `templates/index.html` (decades are a hard-coded Jinja list there). `_apply_post_slice` merely `int()`s the limit. The new module becomes the one Python owner, copied from the form, with a test that fails if the two drift. |
| Brief: typed refusals reuse Task 18's failure types | **Did not hold as written** | `errors.py` holds job-failure codes (`ERROR_CODES`) and provider exceptions, not form refusals. A form refusal is a field and a sentence, so `Refusal(field, message)` is new; the outage wording reuses the heatmap route's existing sentence. |
| Brief: bounds for year, release_year, min_plays, min_tracks exist to validate against | Partly | Only in the template: year `min=2002`, release year `min=1900`, `min_plays` 1-50, `min_tracks` 1-10. The server checks only the year range today. |
| Brief: `params.get("mode", "album")` defaults delete | Held | Three defaults: `album_flow._extract_job_params`, `routes._get_validated_job_context`, `api.release_checks`. `_latest_heatmap_job` has no default. Many tests and six frontend-gate seeds create album jobs without `mode`; Task 7 fixes them. |
| Brief: docs `runtime-system.md` request flow | **Did not hold** | `runtime-system.md` has no request flow (it is package-level). The album request flow lives in `docs/architecture/top-albums-sequence.md` and SESSION_CONTEXT Section 5; the heatmap one in `heatmap-sequence.md`. |
| Brief: "README form behaviour if stated" | Held (nothing to do) | `README.md` states no form behaviour for these fields. |
| Master: one pre-check shared by album and heatmap | Extended | `/validate_user` (`routes/api.py`) repeats the same two checks, so it joins. Three copies become one. |
| Master: "30-second total" bounds a slow Last.fm | Held, and worse | `create_optimized_session` sets `total=30`, and `check_user_exists` and `check_profile_is_public` each open their own session, so one request can hold a gunicorn thread (`--workers 1 --threads 4`) for up to 60 seconds. `run_async_in_thread` has no timeout parameter. |
| Spec: F-B23-40 lists the usernames in three log lines | Gap found | The heatmap route also logs the username in `_validate_heatmap_user` ("User existence check failed for {username}", "Profile privacy check failed for {username}"). The shared pre-check (Task 3) drops them; PR #4's list should not count them. |
| (new) The loading page's Retry re-posts the album form | Handled elsewhere | PR #256 (fix F3) fixes `include_unmatched` and adds a contract test that every form field `routes/album_flow.results_loading` reads is posted back by `retryCurrentSearch`. This plan moves the parsing; Task 2 exposes the field set as `album_request.FORM_FIELDS` and Task 5 Step 4, item 4 keeps that contract test covering it. |
| (new) Existing tests lean on the old fail-open | **Did not hold** | `tests/test_pipeline_integration.py::test_album_pipeline_runs_on_a_real_thread_end_to_end` mocks `check_user_exists` as `{"registered_year": 2000}` with no `exists` key; today the `KeyError` is swallowed by the route's broad `except`. Task 5 changes that mock. `background_task(` has six test call sites, not five (the sixth is multi-line, in `test_background_task_stores_unmatched_rows_when_the_flag_is_on`); Task 4 lists all. |

Earlier review cards: 2026-09-21 #2 (pipeline parameters) and 2026-09-21b #2 (admission as one transaction) were OPEN; this PR closes the album and heatmap halves of both (the export route is the third caller, WP-4). B-12's server half (job kind as a record field) lands in Task 7; its client half (CSRF, retry shapes) stays open.

---

## File Structure

| File | Responsibility |
|---|---|
| `scrobblescope/album_request.py` (new) | Pure, Flask-free. `AlbumRequest` (the ten parameters, defaults declared once), `Refusal(field, message)`, `parse_album_request`, `registration_refusal`, and the sets and bounds the form offers. Imports only `jobs` (for the `mode` constant). |
| `scrobblescope/routes/precheck.py` (new) | `check_lastfm_user(username) -> UserCheck`: exists first, then public; one answer (`Verdict.PUBLIC/MISSING/PRIVATE/UNAVAILABLE`) plus the registration year. Logs class only, never the username. |
| `scrobblescope/routes/admission.py` (new) | `admit(params, target, *, label)`: expire stale jobs, take a slot, create the job, start the thread with the job id only; returns the job id or a `Refused` member. |
| `scrobblescope/jobs.py` | Gains `MODE_ALBUM`, `MODE_HEATMAP` and `params(job_id)`. |
| `scrobblescope/utils.py`, `scrobblescope/config.py` | `run_async_in_thread(coro, timeout=None)`; `LASTFM_PRECHECK_TIMEOUT_SECONDS`. |
| `scrobblescope/orchestrator/__init__.py`, `scrobblescope/heatmap.py` | `background_task(job_id)` and `heatmap_task(job_id)` read their parameters from the job record. |
| `scrobblescope/routes/__init__.py`, `album_flow.py`, `heatmap_flow.py`, `api.py` | Facade passes the timeout; routes call the three modules above and keep only their own HTTP responses. |

The route files keep reading cross-cutting dependencies through the live `routes` module reference (`_routes`), so the existing patches at `scrobblescope.routes.run_async_in_thread`, `_check_user_exists`, `_check_profile_is_public`, `acquire_job_slot`, `start_job_thread`, `_current_year` and `MAX_ACTIVE_JOBS` keep working.

Task order and parallelism (landings are serial in this order, always): the code of Tasks 1, 2 and 3 is disjoint, so their code phases may overlap, but all three edit `docs/agents/PLAYBOOK.md` (a new Section 4 entry at the same anchor), Tasks 2 and 3 both edit `.claude/SESSION_CONTEXT.md`, and each task's measured test count N includes the tests of the tasks landed before it. They therefore land one at a time in the order 1, 2, 3, each rebased on the last. Task 4 is After Task 3 (it edits the `routes/__init__.py` tail import and the SESSION_CONTEXT lines Task 3 changes) and uses Task 2; Task 5 is After 2, 3 and 4; Task 6 After 5; Task 7 After 6. Task 3 edits `tests/test_utils.py`, which the later lastfm-scrobbles PR (#4, task 23a) also edits (one test there): whoever lands second rebases.

---

### Task 1: Pin the album, heatmap and validate flows before refactor

**Touches:** `tests/test_request_flow_parity.py` (new), `docs/agents/PLAYBOOK.md`
**After:** none

**Files:**
- Create: `tests/test_request_flow_parity.py`
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry)

**Interfaces:**
- Consumes: the `client`, `fresh_job_store` fixtures (`tests/conftest.py`), `VALID_FORM_DATA` (`tests/helpers.py`).
- Produces: a suite that passes on today's code and must pass unchanged after every later task. It deliberately does not pin today's fail-open pre-check (the defect Task 5 removes) nor the positional thread arguments (Task 4 replaces them); it asserts what reaches the pipeline instead.

Why: AGENTS.md "Refactor requires parity tests". `tests/test_routes.py` already covers the private/missing-user order, registration year, include-unmatched coercion, thread-failure cleanup and the 303 redirect, so none of that is repeated. These tests cover what is not asserted anywhere: which form fields land in the job record per scope, that the values reach the pipeline in the right slots, the year boundaries, that a full house creates no job, and the bodies of the outage answers.

Overlap, stated (AGENTS.md anti-pattern 1): `test_results_loading_missing_username`, `test_results_loading_year_out_of_bounds`, `test_results_loading_year_gate_uses_the_utc_year` and `test_validate_user_not_found` already assert the same refusal sentences and the same not-found body. The rows of `test_an_unusable_name_or_year_is_refused_before_any_lookup` and `test_validate_user_asks_about_privacy_only_for_an_existing_user` are kept only for their delta: Last.fm is never asked, no job or thread exists, and (for the year) the 2002 and 2025 boundaries; they are not a second copy of the sentence checks.

- [ ] **Step 1: Write the tests**

Create `tests/test_request_flow_parity.py`:

```python
"""Parity tests for the album, heatmap and validate_user request flows.

Written before the request module, the pre-check and the admission module
replace the code behind these routes (AGENTS.md "Refactor requires parity
tests"). Each test states a listener-visible behaviour that must survive the
refactor. Nothing here pins the fail-open pre-check or the positional thread
arguments: those are what the refactor removes.
"""

from unittest.mock import AsyncMock, patch

import pytest

from scrobblescope import jobs
from tests.helpers import VALID_FORM_DATA

PUBLIC_USER = {"exists": True, "registered_year": None}

#: The ten parameters a job record holds for an album run.
RECORD_KEYS = (
    "username",
    "year",
    "sort_mode",
    "include_unmatched",
    "release_scope",
    "decade",
    "release_year",
    "min_plays",
    "min_tracks",
    "limit_results",
)


def _run_inline(target, args=()):
    """Stand in for start_job_thread: run the thread's target on this thread."""
    target(*args)


def _post_album(client, form):
    """POST /results_loading for a public user with the worker thread stubbed."""
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data={**VALID_FORM_DATA, **form})
    return response, mock_start


@pytest.mark.parametrize(
    "form, expected",
    [
        pytest.param(
            {"release_scope": "custom", "decade": "1990s", "release_year": "1982"},
            {"release_scope": "custom", "decade": None, "release_year": 1982},
            id="custom-keeps-the-year-and-drops-the-decade",
        ),
        pytest.param(
            {"release_scope": "decade", "decade": "1990s", "release_year": "1982"},
            {"release_scope": "decade", "decade": "1990s", "release_year": None},
            id="decade-keeps-the-decade-and-drops-the-year",
        ),
        pytest.param(
            {"release_scope": "previous", "decade": "1990s", "release_year": "1982"},
            {"release_scope": "previous", "decade": None, "release_year": None},
            id="previous-drops-both",
        ),
    ],
)
def test_the_job_record_keeps_only_the_release_fields_its_scope_uses(
    client, fresh_job_store, form, expected
):
    """
    GIVEN a form posted with both a decade and a release year
    WHEN the album job is created
    THEN the record holds every other field as posted, and only the release
    field the chosen scope reads, so a stale hidden input cannot narrow a run.
    """
    base = {
        "year": "2023",
        "sort_by": "playtime",
        "min_plays": "7",
        "min_tracks": "4",
        "limit_results": "25",
    }

    response, _ = _post_album(client, {**base, **form})

    assert response.status_code == 303
    (job_id,) = fresh_job_store.ids()
    params = jobs.context(job_id)["params"]
    assert {key: params[key] for key in RECORD_KEYS} == {
        "username": "flounder14",
        "year": 2023,
        "sort_mode": "playtime",
        "include_unmatched": False,
        "min_plays": 7,
        "min_tracks": 4,
        "limit_results": "25",
        **expected,
    }


def test_the_forms_values_reach_the_album_pipeline_in_order(client, fresh_job_store):
    """
    GIVEN a form with a distinct value in every slot
    WHEN the job's thread runs (inline here)
    THEN the pipeline is awaited once with each value in its own slot.

    Mutation: swap min_plays and min_tracks in background_task's call to
    _fetch_and_process and this fails.
    """
    form = {
        **VALID_FORM_DATA,
        "year": "2023",
        "sort_by": "playcount",
        "release_scope": "custom",
        "release_year": "1982",
        "min_plays": "7",
        "min_tracks": "4",
        "limit_results": "25",
        "include_unmatched": "1",
    }
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch("scrobblescope.routes.start_job_thread", side_effect=_run_inline),
        patch(
            "scrobblescope.orchestrator._fetch_and_process", new_callable=AsyncMock
        ) as pipeline,
        patch("scrobblescope.orchestrator.release_job_slot"),
    ):
        response = client.post("/results_loading", data=form)

    assert response.status_code == 303
    (job_id,) = fresh_job_store.ids()
    pipeline.assert_awaited_once_with(
        job_id,
        "flounder14",
        2023,
        "playcount",
        "custom",
        None,
        1982,
        7,
        4,
        "25",
        include_unmatched=True,
    )


def test_the_heatmap_username_is_trimmed_and_reaches_its_pipeline(
    client, fresh_job_store
):
    """
    GIVEN a heatmap start whose username has surrounding spaces
    WHEN the job's thread runs (inline here)
    THEN the record and the pipeline both hold the trimmed name, and the
    record says the job is a heatmap.

    Mutation: stop stripping the username in heatmap_loading and this fails.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch("scrobblescope.routes.start_job_thread", side_effect=_run_inline),
        patch(
            "scrobblescope.heatmap._fetch_and_process_heatmap",
            new_callable=AsyncMock,
        ) as pipeline,
        patch("scrobblescope.heatmap.release_job_slot"),
    ):
        response = client.post("/heatmap_loading", data={"username": "  flounder14  "})

    assert response.status_code == 202
    job_id = response.get_json()["job_id"]
    assert jobs.context(job_id)["params"] == {
        "username": "flounder14",
        "mode": "heatmap",
    }
    pipeline.assert_awaited_once_with(job_id, "flounder14")


@pytest.mark.parametrize(
    "form, message",
    [
        ({"username": ""}, "Username and year are required."),
        ({"year": ""}, "Username and year are required."),
        ({"year": "20x5"}, "Year must be a valid number."),
        ({"year": "2001"}, "Year must be between 2002 and 2025."),
        ({"year": "2026"}, "Year must be between 2002 and 2025."),
    ],
)
def test_an_unusable_name_or_year_is_refused_before_any_lookup(
    client, fresh_job_store, form, message
):
    """
    GIVEN a form with no name, no year, a non-numeric year or a year outside
    2002 to the current year
    WHEN POST /results_loading is submitted
    THEN the form comes back with the reason, Last.fm is not asked, and no job
    or thread is started.
    """
    with (
        patch("scrobblescope.routes._current_year", return_value=2025),
        patch("scrobblescope.routes._check_user_exists") as lookup,
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data={**VALID_FORM_DATA, **form})

    assert response.status_code == 200
    assert message in response.get_data(as_text=True)
    lookup.assert_not_called()
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


@pytest.mark.parametrize("year", ["2002", "2025"])
def test_the_first_and_last_listening_years_are_accepted(client, year):
    """The year range is inclusive at both ends.

    Mutation: change `year < 2002` to `year <= 2002` in results_loading and
    the 2002 row fails.
    """
    with patch("scrobblescope.routes._current_year", return_value=2025):
        response, _ = _post_album(client, {"year": year})

    assert response.status_code == 303


def test_a_full_house_refuses_before_a_job_exists(client, fresh_job_store):
    """
    GIVEN every job slot is busy
    WHEN an album search and a heatmap start are submitted
    THEN both are refused and neither leaves a job behind.

    Mutation: create the job before acquiring the slot in either route and the
    store is no longer empty.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
    ):
        album = client.post("/results_loading", data=VALID_FORM_DATA)
        heatmap = client.post("/heatmap_loading", data={"username": "flounder14"})

    assert album.status_code == 200
    assert b"Too many requests in progress" in album.data
    assert heatmap.status_code == 429
    assert heatmap.get_json()["retryable"] is True
    assert fresh_job_store.ids() == []


def test_a_heatmap_privacy_check_outage_is_a_retryable_503(client, fresh_job_store):
    """
    GIVEN the user exists but Last.fm cannot answer the privacy check
    WHEN POST /heatmap_loading is submitted
    THEN the answer is the retryable 503 body and nothing starts.

    Mutation: change the message or `retryable` in that answer and this fails.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch(
            "scrobblescope.routes._check_profile_is_public",
            side_effect=RuntimeError("down"),
        ),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/heatmap_loading", data={"username": "flounder14"})

    assert response.status_code == 503
    assert response.get_json() == {
        "error": True,
        "message": "Validation service unavailable. Try again.",
        "retryable": True,
    }
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


def test_validate_user_outage_is_a_retryable_503(client):
    """GET /validate_user answers 503 with the shared unavailable sentence."""
    with patch(
        "scrobblescope.routes._check_user_exists", side_effect=RuntimeError("down")
    ):
        response = client.get("/validate_user", query_string={"username": "someone"})

    assert response.status_code == 503
    assert response.get_json() == {
        "valid": False,
        "message": "Validation service unavailable. Try again.",
    }


def test_validate_user_asks_about_privacy_only_for_an_existing_user(client):
    """
    GIVEN Last.fm does not know the name
    WHEN GET /validate_user runs
    THEN the answer is "not found" and the privacy check is never made.

    Mutation: ask for privacy before existence and the mock is called.
    """
    with (
        patch(
            "scrobblescope.routes._check_user_exists",
            return_value={"exists": False, "registered_year": None},
        ),
        patch("scrobblescope.routes._check_profile_is_public") as privacy,
    ):
        response = client.get("/validate_user", query_string={"username": "ghost"})

    assert response.status_code == 200
    assert response.get_json() == {
        "valid": False,
        "message": "Username not found on Last.fm.",
    }
    privacy.assert_not_called()
```

- [ ] **Step 2: Run them; they pass on the current tree**

Run: `PY -m pytest tests/test_request_flow_parity.py -q -p no:cacheprovider`
Expected: `16 passed`.

- [ ] **Step 3: Mutation evidence**

Apply each defect to the committed source, run the named test, record the failure, then `git checkout -- <path>`:

| Planted defect | File | Test that must fail |
|---|---|---|
| keep the posted decade whatever the scope (`decade = request.form.get("decade")`) | `scrobblescope/routes/album_flow.py` | `test_the_job_record_keeps_only_the_release_fields_its_scope_uses` (custom and previous rows) |
| swap `min_plays` and `min_tracks` in the `_fetch_and_process(...)` call | `scrobblescope/orchestrator/__init__.py` (`background_task`) | `test_the_forms_values_reach_the_album_pipeline_in_order` |
| remove `username = username.strip()` | `scrobblescope/routes/heatmap_flow.py` | `test_the_heatmap_username_is_trimmed_and_reaches_its_pipeline` |
| `year < 2002` becomes `year <= 2002` | `scrobblescope/routes/album_flow.py` | `test_the_first_and_last_listening_years_are_accepted[2002]` |
| call `jobs.create` before `acquire_job_slot` in `_dispatch_heatmap_job` | `scrobblescope/routes/heatmap_flow.py` | `test_a_full_house_refuses_before_a_job_exists` |
| change the heatmap privacy-outage `retryable` to `False` | `scrobblescope/routes/heatmap_flow.py` | `test_a_heatmap_privacy_check_outage_is_a_retryable_503` |
| call `_check_profile_is_public` before `_check_user_exists` | `scrobblescope/routes/api.py` | `test_validate_user_asks_about_privacy_only_for_an_existing_user` |

After restoring, re-run Step 2: all pass.

- [ ] **Step 4: Section 4 entry, gates, commit**

Entry heading: `### YYYY-MM-DD - The request flows are pinned before they are refactored` (today's date). Body: scope (tests only), why (AGENTS.md "Refactor requires parity tests" before PR #3's module changes), what is pinned and what deliberately is not (the fail-open pre-check; positional thread arguments), the mutation table results, Validation `pytest -q` N.
Commit: `test(routes): Pin the album, heatmap and validate flows before refactor`.

---

### Task 2: The album request module

**Touches:** `scrobblescope/album_request.py` (new), `scrobblescope/jobs.py`, `tests/test_album_request.py` (new), `.claude/SESSION_CONTEXT.md`, `docs/architecture/runtime-system.md`, `docs/agents/PLAYBOOK.md`
**Lands:** serially after Task 1 (both edit PLAYBOOK Section 4); code phase may overlap Task 1.
**After:** none

**Files:**
- Create: `scrobblescope/album_request.py`
- Create: `tests/test_album_request.py`
- Modify: `scrobblescope/jobs.py` (two constants)
- Modify: `.claude/SESSION_CONTEXT.md` (Section 3 and Section 4)
- Modify: `docs/architecture/runtime-system.md` (node and edge for the new module)
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces (later tasks rely on these exact names):
  - `jobs.MODE_ALBUM == "album"`, `jobs.MODE_HEATMAP == "heatmap"`.
  - `Refusal(field: str, message: str)` frozen dataclass.
  - `AlbumRequest(username, year, sort_mode="playcount", include_unmatched=False, release_scope="same", decade=None, release_year=None, min_plays=10, min_tracks=3, limit_results="all")` frozen dataclass with `to_params() -> dict` (the ten keys plus `"mode": "album"`) and `AlbumRequest.from_params(params) -> AlbumRequest` (raises `TypeError` when `username` or `year` is missing).
  - `parse_album_request(form, *, current_year, require_username=True) -> AlbumRequest | Refusal`.
  - `registration_refusal(year, registered_year) -> Refusal | None`.
  - Constants `SORT_MODES`, `RELEASE_SCOPES`, `DECADES`, `LIMIT_OPTIONS`, `MIN_LISTENING_YEAR`, `MIN_RELEASE_YEAR`, `MIN_PLAYS_BOUNDS`, `MIN_TRACKS_BOUNDS`, `MAX_USERNAME_LENGTH`.
  - `FORM_FIELDS`: the tuple of form field names the parser reads (`username`, `year`, `sort_by`, `include_unmatched`, `release_scope`, `decade`, `release_year`, `min_plays`, `min_tracks`, `limit_results`). It is the single list the loading page's Retry contract test reads (Task 5 Step 4, item 4); a test here proves it matches what the parser actually reads.

Why: the form has no Python owner. A bad `decade` makes every album fail the release filter and the listener sees "no albums"; a `custom` scope without a year silently accepts every year. The module is the one place that says what a valid album request is, and the export route (WP-4) can call it. Messages for the refusals that exist today are kept word for word.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_album_request.py`:

```python
"""The album request module: a submitted form becomes a request or a refusal."""

import re
from pathlib import Path

import pytest

from scrobblescope import album_request as module
from scrobblescope import jobs
from scrobblescope.album_request import (
    AlbumRequest,
    Refusal,
    parse_album_request,
    registration_refusal,
)
from tests.helpers import VALID_FORM_DATA

CURRENT_YEAR = 2025
INDEX_HTML = (
    Path(__file__).resolve().parents[1] / "templates" / "index.html"
).read_text(encoding="utf-8")


def _form(**overrides):
    """VALID_FORM_DATA with *overrides* applied; a None value removes the field."""
    form = {**VALID_FORM_DATA, **overrides}
    return {key: value for key, value in form.items() if value is not None}


def _parse(**overrides):
    return parse_album_request(_form(**overrides), current_year=CURRENT_YEAR)


def test_a_complete_form_becomes_one_request():
    request = _parse(
        year="2023",
        sort_by="playtime",
        release_scope="decade",
        decade="1990s",
        release_year="1982",
        min_plays="7",
        min_tracks="4",
        limit_results="25",
    )

    assert request == AlbumRequest(
        username="flounder14",
        year=2023,
        sort_mode="playtime",
        include_unmatched=False,
        release_scope="decade",
        decade="1990s",
        release_year=None,
        min_plays=7,
        min_tracks=4,
        limit_results="25",
    )


def test_a_form_with_only_a_name_and_a_year_takes_the_form_defaults():
    """The defaults are the ones the form shows: play count, same year, 10, 3, all."""
    request = parse_album_request(
        {"username": "flounder14", "year": "2025"}, current_year=CURRENT_YEAR
    )

    assert request == AlbumRequest("flounder14", 2025)
    assert (
        request.sort_mode,
        request.release_scope,
        request.min_plays,
        request.min_tracks,
        request.limit_results,
        request.include_unmatched,
    ) == ("playcount", "same", 10, 3, "all", False)


def test_a_blank_optional_field_is_a_missing_one():
    blank = _parse(sort_by="", release_scope="", limit_results="", min_plays=" ")
    absent = _parse(
        sort_by=None, release_scope=None, limit_results=None, min_plays=None
    )

    assert blank == absent
    assert not isinstance(blank, Refusal)


@pytest.mark.parametrize(
    "overrides, field, message",
    [
        ({"username": None}, "username", "Username and year are required."),
        ({"username": "   "}, "username", "Username and year are required."),
        ({"year": None}, "year", "Username and year are required."),
        ({"username": "x" * 65}, "username", "Username is too long."),
        ({"year": "20x5"}, "year", "Year must be a valid number."),
        ({"year": "2001"}, "year", "Year must be between 2002 and 2025."),
        ({"year": "2026"}, "year", "Year must be between 2002 and 2025."),
        (
            {"release_scope": "forever"},
            "release_scope",
            "Choose a release filter from the list.",
        ),
        (
            {"release_scope": "decade", "decade": "2030s"},
            "decade",
            "Choose a decade from the list.",
        ),
        (
            {"release_scope": "decade", "decade": None},
            "decade",
            "Choose a decade from the list.",
        ),
        (
            {"release_scope": "custom", "release_year": None},
            "release_year",
            "Enter a release year.",
        ),
        (
            {"release_scope": "custom", "release_year": "19x0"},
            "release_year",
            "Release year must be a valid number.",
        ),
        (
            {"release_scope": "custom", "release_year": "1899"},
            "release_year",
            "Release year must be between 1900 and 2025.",
        ),
        (
            {"release_scope": "custom", "release_year": "2026"},
            "release_year",
            "Release year must be between 1900 and 2025.",
        ),
        (
            {"sort_by": "loudness"},
            "sort_by",
            "Choose Play count or Play time to rank by.",
        ),
        (
            {"limit_results": "7"},
            "limit_results",
            "Choose how many albums to show from the list.",
        ),
        (
            {"min_plays": "0"},
            "min_plays",
            "Minimum plays must be a whole number from 1 to 50.",
        ),
        (
            {"min_plays": "51"},
            "min_plays",
            "Minimum plays must be a whole number from 1 to 50.",
        ),
        (
            {"min_plays": "many"},
            "min_plays",
            "Minimum plays must be a whole number from 1 to 50.",
        ),
        (
            {"min_tracks": "0"},
            "min_tracks",
            "Minimum unique tracks must be a whole number from 1 to 10.",
        ),
        (
            {"min_tracks": "11"},
            "min_tracks",
            "Minimum unique tracks must be a whole number from 1 to 10.",
        ),
    ],
)
def test_an_unusable_field_is_refused_with_its_name_and_a_sentence(
    overrides, field, message
):
    assert _parse(**overrides) == Refusal(field, message)


@pytest.mark.parametrize(
    "overrides, attribute, expected",
    [
        ({"year": "2002"}, "year", 2002),
        ({"year": "2025"}, "year", 2025),
        ({"release_scope": "custom", "release_year": "1900"}, "release_year", 1900),
        ({"release_scope": "custom", "release_year": "2025"}, "release_year", 2025),
        ({"min_plays": "1"}, "min_plays", 1),
        ({"min_plays": "50"}, "min_plays", 50),
        ({"min_tracks": "1"}, "min_tracks", 1),
        ({"min_tracks": "10"}, "min_tracks", 10),
        ({"username": "x" * 64}, "username", "x" * 64),
        ({"username": "  flounder14  "}, "username", "flounder14"),
    ],
)
def test_the_edges_of_each_range_are_accepted(overrides, attribute, expected):
    assert getattr(_parse(**overrides), attribute) == expected


@pytest.mark.parametrize("limit", ["all", "10", "25", "50", "100"])
def test_every_limit_the_form_offers_is_accepted(limit):
    assert _parse(limit_results=limit).limit_results == limit


@pytest.mark.parametrize("sort_by", ["playcount", "playtime"])
def test_both_ranking_choices_are_accepted(sort_by):
    assert _parse(sort_by=sort_by).sort_mode == sort_by


@pytest.mark.parametrize(
    "scope, decade, release_year",
    [
        ("same", None, None),
        ("previous", None, None),
        ("all", None, None),
        ("decade", "1990s", None),
        ("custom", None, 1982),
    ],
)
def test_only_the_release_field_of_the_chosen_scope_survives(
    scope, decade, release_year
):
    request = _parse(release_scope=scope, decade="1990s", release_year="1982")

    assert (request.decade, request.release_year) == (decade, release_year)


@pytest.mark.parametrize(
    "include, sort_by, expected",
    [
        ("1", "playtime", (True, "playcount")),
        ("1", "playcount", (True, "playcount")),
        (None, "playtime", (False, "playtime")),
        ("0", "playtime", (False, "playtime")),
        ("true", "playcount", (False, "playcount")),
    ],
)
def test_an_include_run_is_always_a_play_count_run(include, sort_by, expected):
    """An unmatched album has no play time, so "All albums" cannot rank by it.

    Only the exact value "1" turns the choice on, as the form's radio sends it.
    """
    request = _parse(include_unmatched=include, sort_by=sort_by)

    assert (request.include_unmatched, request.sort_mode) == expected


def test_an_upload_form_has_no_username_to_require():
    """The export route (WP-4) has no Last.fm name and must not invent one."""
    request = parse_album_request(
        {"year": "2025"}, current_year=CURRENT_YEAR, require_username=False
    )

    assert request == AlbumRequest(None, 2025)
    assert parse_album_request(
        {}, current_year=CURRENT_YEAR, require_username=False
    ) == Refusal("year", "Year is required.")


@pytest.mark.parametrize(
    "year, registered_year, refused",
    [(2015, 2016, True), (2016, 2016, False), (2020, 2016, False)],
)
def test_a_year_before_the_account_existed_is_refused(year, registered_year, refused):
    refusal = registration_refusal(year, registered_year)

    assert (refusal is not None) is refused
    if refused:
        assert refusal == Refusal(
            "year",
            "Year 2015 is before your Last.fm registration year (2016). "
            "Please choose 2016 or later.",
        )


@pytest.mark.parametrize("unknown", [None, 0])
def test_an_unknown_registration_year_is_no_reason_to_refuse(unknown):
    """The registration year is a hint: without it the search proceeds."""
    assert registration_refusal(2003, unknown) is None


def test_a_request_survives_being_stored_on_the_job_record():
    request = _parse(
        release_scope="custom", release_year="1982", include_unmatched="1"
    )

    params = request.to_params()

    assert params["mode"] == jobs.MODE_ALBUM == "album"
    assert set(params) == {
        "username",
        "year",
        "sort_mode",
        "include_unmatched",
        "release_scope",
        "decade",
        "release_year",
        "min_plays",
        "min_tracks",
        "limit_results",
        "mode",
    }
    assert AlbumRequest.from_params(params) == request


def test_a_job_record_without_a_name_or_year_is_not_a_request():
    with pytest.raises(TypeError):
        AlbumRequest.from_params({"year": 2025, "mode": "album"})


class _SpyForm(dict):
    """A form that records every key the parser asks for."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read = set()

    def get(self, key, default=None):
        self.read.add(key)
        return super().get(key, default)


def test_form_fields_lists_exactly_the_fields_the_parser_reads():
    """The Retry contract test trusts FORM_FIELDS, so it must be the real list.

    Mutation: make the parser read a new field (say `form.get("source")`), or
    delete "decade" from FORM_FIELDS, and this fails.
    """
    read = set()
    for scope in module.RELEASE_SCOPES:
        form = _SpyForm(_form(release_scope=scope, decade="1990s", release_year="1982"))
        parse_album_request(form, current_year=CURRENT_YEAR)
        read |= form.read

    assert read == set(module.FORM_FIELDS)


def test_every_scope_the_server_accepts_has_a_release_window_rule():
    """A scope added here but not to domain.release_window would filter nothing.

    Mutation: add "fortnight" to RELEASE_SCOPES and this fails.
    """
    from scrobblescope.domain import release_window

    for scope in module.RELEASE_SCOPES:
        window = release_window(scope, 2023, decade="1990s", release_year=1982)
        assert (window is None) is (scope == "all"), scope


def _select_values(select_id):
    block = re.search(rf'<select id="{select_id}".*?</select>', INDEX_HTML, re.S)
    return set(re.findall(r'<option value="([^"]+)"', block.group(0)))


def _input_numbers(field_id, *attributes):
    tag = re.search(rf'<input[^>]*id="{field_id}"[^>]*>', INDEX_HTML, re.S).group(0)
    return tuple(int(re.search(rf'{a}="(\d+)"', tag).group(1)) for a in attributes)


def test_the_server_accepts_exactly_what_the_form_offers():
    """A choice the form shows must be accepted; one it does not show, refused.

    Mutation: drop "100" from LIMIT_OPTIONS, or add a decade the form lacks,
    and this fails.
    """
    assert _select_values("release_scope") == set(module.RELEASE_SCOPES)
    assert _select_values("limit_results") == set(module.LIMIT_OPTIONS)
    assert set(re.findall(r'name="sort_by" value="(\w+)"', INDEX_HTML)) == set(
        module.SORT_MODES
    )
    loop = re.search(r"for decade in \[([^\]]+)\]", INDEX_HTML).group(1)
    assert tuple(re.findall(r"'(\d{4}s)'", loop)) == module.DECADES


def test_the_server_ranges_are_the_ranges_the_form_enforces():
    assert _input_numbers("year", "min") == (module.MIN_LISTENING_YEAR,)
    assert _input_numbers("release_year", "min") == (module.MIN_RELEASE_YEAR,)
    assert _input_numbers("min_plays", "min", "max") == module.MIN_PLAYS_BOUNDS
    assert _input_numbers("min_tracks", "min", "max") == module.MIN_TRACKS_BOUNDS
```

- [ ] **Step 2: Run to verify it fails**

Run: `PY -m pytest tests/test_album_request.py -q -p no:cacheprovider`
Expected: collection error `ImportError: cannot import name 'album_request' from 'scrobblescope'`.

- [ ] **Step 3: Add the job-kind constants**

In `scrobblescope/jobs.py`, directly above `_ERROR_FIELDS = (...)`, add:

```python
#: The job kinds. A job record's ``params["mode"]`` holds one of them, written
#: when the job is created; the pages and APIs that serve one kind refuse the
#: other. Callers compare against these, never against a string literal.
MODE_ALBUM = "album"
MODE_HEATMAP = "heatmap"
```

- [ ] **Step 4: Write the module**

Create `scrobblescope/album_request.py`:

```python
"""The album request: one form, one validated record or one refusal.

The album form's fields used to be read, converted and checked inline in
``routes/album_flow.results_loading``, and only the year was ever validated:
a bad ``decade`` made every album fail the release filter, so the listener saw
"no albums" instead of a mistake. This module is the one owner of what a valid
album request is. ``parse_album_request`` is pure (no Flask, no I/O): a form
mapping and the current year go in, an ``AlbumRequest`` or a ``Refusal`` naming
the field and the sentence comes out. The Spotify export route (Batch 23 WP-4)
calls the same function with ``require_username=False``.

The sets and bounds below are the ones ``templates/index.html`` offers.
``tests/test_album_request.py`` reads the template and fails if the two drift.

    album_request <- jobs
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields

from scrobblescope import jobs

MIN_LISTENING_YEAR = 2002
MIN_RELEASE_YEAR = 1900
#: The limit ``/validate_user`` already enforces. The form's input allows 100
#: characters, but a Last.fm name is far shorter, so 64 refuses nothing real.
MAX_USERNAME_LENGTH = 64
MIN_PLAYS_BOUNDS = (1, 50)
MIN_TRACKS_BOUNDS = (1, 10)

SORT_MODES = ("playcount", "playtime")
RELEASE_SCOPES = ("same", "previous", "decade", "custom", "all")
DECADES = (
    "2020s",
    "2010s",
    "2000s",
    "1990s",
    "1980s",
    "1970s",
    "1960s",
    "1950s",
)
LIMIT_OPTIONS = ("all", "10", "25", "50", "100")

#: Every form field ``parse_album_request`` reads. The loading page's Retry
#: re-posts the form from this list's contract (tests read it from here).
FORM_FIELDS = (
    "username",
    "year",
    "sort_by",
    "include_unmatched",
    "release_scope",
    "decade",
    "release_year",
    "min_plays",
    "min_tracks",
    "limit_results",
)

# Defaults, declared once: AlbumRequest's field defaults and the parser's
# "missing means default" rule both read these.
DEFAULT_SORT_MODE = "playcount"
DEFAULT_RELEASE_SCOPE = "same"
DEFAULT_MIN_PLAYS = 10
DEFAULT_MIN_TRACKS = 3
DEFAULT_LIMIT = "all"


@dataclass(frozen=True)
class Refusal:
    """A form the listener must fix: the form field and the sentence to show."""

    field: str
    message: str


@dataclass(frozen=True)
class AlbumRequest:
    """A validated album request: the ten parameters a job runs with."""

    username: str | None
    year: int
    sort_mode: str = DEFAULT_SORT_MODE
    include_unmatched: bool = False
    release_scope: str = DEFAULT_RELEASE_SCOPE
    decade: str | None = None
    release_year: int | None = None
    min_plays: int = DEFAULT_MIN_PLAYS
    min_tracks: int = DEFAULT_MIN_TRACKS
    limit_results: str = DEFAULT_LIMIT

    def to_params(self):
        """Return the job record's params: the ten fields plus the job kind."""
        params = {f.name: getattr(self, f.name) for f in fields(self)}
        params["mode"] = jobs.MODE_ALBUM
        return params

    @classmethod
    def from_params(cls, params):
        """Rebuild a request from a job record's params.

        The record was written by ``to_params``, so nothing is re-validated.
        Keys that are not request fields (``mode``) are ignored; a record
        without ``username`` or ``year`` raises ``TypeError``.
        """
        names = {f.name for f in fields(cls)}
        return cls(**{key: value for key, value in params.items() if key in names})


def _text(form, key, default=None):
    """Return the stripped value of *key*, or *default* when absent or blank."""
    value = (form.get(key) or "").strip()
    return value if value else default


def _whole_number(raw):
    """Return *raw* as an int, or None when it is not a whole number."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _bounded(form, key, default, bounds, label):
    """Return ``(value, None)`` or ``(None, Refusal)`` for a bounded count."""
    raw = _text(form, key)
    if raw is None:
        return default, None
    low, high = bounds
    value = _whole_number(raw)
    if value is None or not low <= value <= high:
        return None, Refusal(
            key, f"{label} must be a whole number from {low} to {high}."
        )
    return value, None


def parse_album_request(
    form: Mapping, *, current_year: int, require_username: bool = True
):
    """Turn a submitted form into an ``AlbumRequest`` or a ``Refusal``.

    Checks run in the order the form reads, so the first problem a listener
    sees is the first field they would fix. A blank field counts as missing and
    takes its default. Only the release field of the chosen scope is kept: a
    hidden decade posted with a custom year cannot narrow the run. An include
    run (``include_unmatched == "1"``) is always a play-count run, because an
    unmatched album has no play time; the page disables the choice and this
    keeps a form posted without scripts to the same rule.

    Args:
        form: A mapping of field name to string (``request.form``).
        current_year: The upper bound for the listening and release years. The
            caller supplies it so this function stays pure and testable.
        require_username: False for the export route, which has no Last.fm
            name; the request then carries ``username=None``.
    """
    username = _text(form, "username")
    raw_year = _text(form, "year")
    if (require_username and username is None) or raw_year is None:
        if require_username:
            field = "username" if username is None else "year"
            return Refusal(field, "Username and year are required.")
        return Refusal("year", "Year is required.")
    if username is not None and len(username) > MAX_USERNAME_LENGTH:
        return Refusal("username", "Username is too long.")

    year = _whole_number(raw_year)
    if year is None:
        return Refusal("year", "Year must be a valid number.")
    if not MIN_LISTENING_YEAR <= year <= current_year:
        return Refusal(
            "year", f"Year must be between {MIN_LISTENING_YEAR} and {current_year}."
        )

    release_scope = _text(form, "release_scope", DEFAULT_RELEASE_SCOPE)
    if release_scope not in RELEASE_SCOPES:
        return Refusal("release_scope", "Choose a release filter from the list.")

    decade = None
    release_year = None
    if release_scope == "decade":
        decade = _text(form, "decade")
        if decade not in DECADES:
            return Refusal("decade", "Choose a decade from the list.")
    elif release_scope == "custom":
        raw_release_year = _text(form, "release_year")
        if raw_release_year is None:
            return Refusal("release_year", "Enter a release year.")
        release_year = _whole_number(raw_release_year)
        if release_year is None:
            return Refusal("release_year", "Release year must be a valid number.")
        if not MIN_RELEASE_YEAR <= release_year <= current_year:
            return Refusal(
                "release_year",
                f"Release year must be between {MIN_RELEASE_YEAR} and {current_year}.",
            )

    sort_mode = _text(form, "sort_by", DEFAULT_SORT_MODE)
    if sort_mode not in SORT_MODES:
        return Refusal("sort_by", "Choose Play count or Play time to rank by.")
    include_unmatched = form.get("include_unmatched") == "1"
    if include_unmatched and sort_mode == "playtime":
        sort_mode = "playcount"

    limit_results = _text(form, "limit_results", DEFAULT_LIMIT)
    if limit_results not in LIMIT_OPTIONS:
        return Refusal(
            "limit_results", "Choose how many albums to show from the list."
        )

    min_plays, refusal = _bounded(
        form, "min_plays", DEFAULT_MIN_PLAYS, MIN_PLAYS_BOUNDS, "Minimum plays"
    )
    if refusal:
        return refusal
    min_tracks, refusal = _bounded(
        form,
        "min_tracks",
        DEFAULT_MIN_TRACKS,
        MIN_TRACKS_BOUNDS,
        "Minimum unique tracks",
    )
    if refusal:
        return refusal

    return AlbumRequest(
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


def registration_refusal(year, registered_year):
    """Return a ``Refusal`` when *year* predates the Last.fm account, else None.

    The registration year is a hint, not a gate on the lookup: an account whose
    registration year Last.fm did not report (``None``) is never refused here.
    A failed lookup is not this function's concern: the pre-check refuses it
    before this is asked.
    """
    if registered_year and year < registered_year:
        return Refusal(
            "year",
            f"Year {year} is before your Last.fm registration year"
            f" ({registered_year}). Please choose {registered_year} or later.",
        )
    return None
```

- [ ] **Step 5: Run to verify it passes**

Run: `PY -m pytest tests/test_album_request.py -q -p no:cacheprovider`
Expected: all pass, none skipped.

- [ ] **Step 6: Mutation evidence**

`git add scrobblescope/album_request.py`, then for each row apply the defect, run `PY -m pytest tests/test_album_request.py -q -p no:cacheprovider`, record the named test failing, and `git checkout -- scrobblescope/album_request.py`:

| Planted defect | Test that must fail |
|---|---|
| `year <= current_year` becomes `year < current_year` | `test_the_edges_of_each_range_are_accepted[year-2025]` |
| remove the decade membership check (`decade not in DECADES`) | `test_an_unusable_field_is_refused_with_its_name_and_a_sentence` (decade rows) |
| drop the `elif release_scope == "custom"` requirement (accept a missing year) | same test, `Enter a release year.` row |
| delete the `include_unmatched and sort_mode == "playtime"` coercion | `test_an_include_run_is_always_a_play_count_run` |
| keep `decade` for every scope | `test_only_the_release_field_of_the_chosen_scope_survives` |
| let `min_plays` 51 through (`high` becomes `100`) | the `min_plays` 51 row |
| treat a blank field as invalid (drop the `if value else default` in `_text`) | `test_a_blank_optional_field_is_a_missing_one` |
| refuse when `registered_year` is `None` | `test_an_unknown_registration_year_is_no_reason_to_refuse` |
| remove `"100"` from `LIMIT_OPTIONS` | `test_the_server_accepts_exactly_what_the_form_offers` and the limit "100" row |
| read `form.get("source")` in the parser, or delete `"decade"` from `FORM_FIELDS` | `test_form_fields_lists_exactly_the_fields_the_parser_reads` |
| add `"fortnight"` to `RELEASE_SCOPES` | `test_every_scope_the_server_accepts_has_a_release_window_rule` |

- [ ] **Step 7: Docs in the same commit**

`.claude/SESSION_CONTEXT.md` Section 3: after the `jobs.py` line add
`  album_request.py          # AlbumRequest (the ten job parameters, defaults declared once), parse_album_request: form -> request or Refusal, registration_refusal`.
Section 4: after `jobs.py         <- config, errors` add `album_request.py <- jobs`.

`docs/architecture/runtime-system.md`: in the `Runtime` subgraph, after the `Unmatched[...]` node add `        AlbumRequest[album_request.py<br/>form -> request or refusal]`; add the edge `    AlbumRequest --> JobModule` after the `Heatmap -->` edges; add `AlbumRequest` to the `class App,Routes,...,Errors runtime` list. The `Routes --> AlbumRequest` and `Album --> AlbumRequest` edges are added in Tasks 5 and 4, in the commit whose import creates each. Validate the block with the `validate_and_render_mermaid_diagram` MCP call before commit.

- [ ] **Step 8: Section 4 entry, gates, commit**

Entry heading: `### YYYY-MM-DD - The album form has one owner`. Body: scope (a pure module, not yet wired), why (B-1: the sets lived only in the template; a bad decade showed "no albums"), the refusals that will be new once wired (listed), the username bound (64, the limit `/validate_user` already enforces; the form's `maxlength` is 100), mutation table, Validation `pytest -q` N.
Commit: `feat(album): Parse an album form into a request or a refusal`.

---

### Task 3: One Last.fm pre-check answer, with its own short timeout

**Touches:** `scrobblescope/config.py`, `scrobblescope/utils.py`, `scrobblescope/routes/__init__.py`, `scrobblescope/routes/precheck.py` (new), `tests/test_utils.py`, `tests/test_precheck.py` (new), `.claude/SESSION_CONTEXT.md`, `docs/agents/PLAYBOOK.md`
**After:** none in code. **Lands:** serially after Task 2 (both edit SESSION_CONTEXT Sections 3-4 and PLAYBOOK Section 4; N counts Task 2's tests). `tests/test_utils.py` is also edited by PR #4 (task 23a): rebase if that lands first.

**Files:**
- Modify: `scrobblescope/config.py`, `scrobblescope/utils.py`, `scrobblescope/routes/__init__.py`
- Create: `scrobblescope/routes/precheck.py`
- Modify: `tests/test_utils.py` (two new tests, one import line)
- Create: `tests/test_precheck.py`
- Modify: `.claude/SESSION_CONTEXT.md`, `docs/agents/PLAYBOOK.md`

**Interfaces:**
- Consumes: the facade functions `routes._check_user_exists(username)` and `routes._check_profile_is_public(username)`.
- Produces:
  - `utils.run_async_in_thread(coro, timeout=None)`: raises the builtin `TimeoutError` in the calling thread when the coroutine has not finished in `timeout` seconds; `None` keeps today's unbounded wait.
  - `config.LASTFM_PRECHECK_TIMEOUT_SECONDS` (float, default 5, env `LASTFM_PRECHECK_TIMEOUT_SECONDS`).
  - `routes.precheck.Verdict` (`PUBLIC`, `MISSING`, `PRIVATE`, `UNAVAILABLE`), `routes.precheck.UserCheck(verdict, registered_year=None)`, `routes.precheck.check_lastfm_user(username) -> UserCheck`, `routes.precheck.UNAVAILABLE_MESSAGE == "Validation service unavailable. Try again."`, `routes.precheck.not_found_message(username)`. An existence answer that is not a mapping, has no boolean `exists`, or has a `registered_year` that is neither an int nor None is a malformed answer and counts as `UNAVAILABLE`, exactly like a raised exception (a missing `registered_year` alone is fine: it means unknown).

Why: each of the three routes calls the same two Last.fm checks and handles their failure its own way, and none has a time limit but the HTTP session's 30 seconds per call (two calls: up to 60 seconds of one of four request threads). This commit adds the shared answer and the limit. The album route still swallows an outage until Task 5 switches it over; the heatmap and validate routes already refuse, and now give up in seconds.

- [ ] **Step 1: Write the failing tests**

Add `run_async_in_thread,` to the `from scrobblescope.utils import (...)` list in `tests/test_utils.py` (before `set_cached_response`) and append:

```python
def test_run_async_in_thread_stops_waiting_when_the_timeout_passes():
    """A stalled coroutine must not hold the calling request thread.

    Mutation: ignore the timeout argument and the call waits the full three
    seconds, then returns "late", so pytest.raises fails.
    """

    async def stalled():
        await asyncio.sleep(3)
        return "late"

    started = time.monotonic()
    with pytest.raises(TimeoutError):
        run_async_in_thread(stalled, timeout=0.05)

    assert time.monotonic() - started < 1.5


def test_run_async_in_thread_without_a_timeout_returns_the_result():
    async def quick():
        return 7

    assert run_async_in_thread(quick) == 7
```

Create `tests/test_precheck.py`:

```python
"""The shared Last.fm pre-check: one answer for the album, heatmap and validate routes."""

import asyncio
import logging
import time
from unittest.mock import patch

import pytest

from scrobblescope import routes
from scrobblescope.routes.precheck import (
    UNAVAILABLE_MESSAGE,
    UserCheck,
    Verdict,
    check_lastfm_user,
    not_found_message,
)

KNOWN = {"exists": True, "registered_year": 2016}


def test_an_existing_public_user_is_public_and_carries_the_registration_year():
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=KNOWN),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.PUBLIC, 2016)


def test_a_missing_user_is_missing_and_privacy_is_never_asked():
    """Existence first (owner's order): a ghost gets "not found", not a privacy verdict."""
    with (
        patch(
            "scrobblescope.routes._check_user_exists",
            return_value={"exists": False, "registered_year": None},
        ),
        patch("scrobblescope.routes._check_profile_is_public") as privacy,
    ):
        assert check_lastfm_user("ghost") == UserCheck(Verdict.MISSING)

    privacy.assert_not_called()


def test_an_existing_private_user_is_private():
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=KNOWN),
        patch("scrobblescope.routes._check_profile_is_public", return_value=False),
    ):
        assert check_lastfm_user("private_user") == UserCheck(Verdict.PRIVATE)


@pytest.mark.parametrize(
    "answer",
    [
        None,
        [],
        {},
        {"registered_year": 2016},
        {"exists": "yes", "registered_year": 2016},
        {"exists": None, "registered_year": 2016},
        {"exists": True, "registered_year": "2016"},
    ],
    ids=[
        "none",
        "not-a-mapping",
        "empty",
        "no-exists-key",
        "exists-not-a-bool",
        "exists-null",
        "year-not-a-number",
    ],
)
def test_a_malformed_existence_answer_is_unavailable_never_an_error(answer):
    """
    GIVEN Last.fm answers the existence check with a body that is not the
    expected shape (a missing key, a wrong type)
    WHEN the pre-check reads it
    THEN the answer is UNAVAILABLE (retryable) and privacy is not asked; it is
    neither an unhandled exception (a 500) nor a guess that the user exists.

    Mutation: read `info["exists"]` outside the try, and the rows without the
    key raise KeyError; read it with `info.get("exists")` and the
    no-exists-key row becomes MISSING.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=answer),
        patch("scrobblescope.routes._check_profile_is_public") as privacy,
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.UNAVAILABLE)

    privacy.assert_not_called()


def test_an_unreported_registration_year_is_unknown_not_malformed():
    """Last.fm may not report a registration year; that is no outage."""
    with (
        patch("scrobblescope.routes._check_user_exists", return_value={"exists": True}),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.PUBLIC, None)


def test_an_outage_on_the_existence_check_is_unavailable_and_privacy_is_not_asked():
    with (
        patch(
            "scrobblescope.routes._check_user_exists", side_effect=RuntimeError("down")
        ),
        patch("scrobblescope.routes._check_profile_is_public") as privacy,
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.UNAVAILABLE)

    privacy.assert_not_called()


def test_an_outage_on_the_privacy_check_is_unavailable_never_public():
    """Fail closed: a check that could not answer must not let a job start.

    Mutation: return PUBLIC from the privacy `except` branch and this fails.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=KNOWN),
        patch(
            "scrobblescope.routes._check_profile_is_public",
            side_effect=RuntimeError("down"),
        ),
    ):
        assert check_lastfm_user("flounder14") == UserCheck(Verdict.UNAVAILABLE)


def test_the_messages_the_routes_show():
    assert UNAVAILABLE_MESSAGE == "Validation service unavailable. Try again."
    assert not_found_message("flounder14") == (
        "User 'flounder14' was not found on Last.fm."
    )


def test_a_failed_check_logs_the_class_and_never_the_listeners_name(caplog):
    """
    GIVEN a check that raises with the listener's name and a URL in its text
    WHEN the pre-check fails
    THEN no WARNING-or-higher line carries the name or the text, only the class.

    Mutation: log the username in precheck's failure line and this fails.
    """
    secret = "zqxv_listener"
    with (
        patch(
            "scrobblescope.routes._check_user_exists",
            side_effect=RuntimeError(f"failed url=https://x/?user={secret}"),
        ),
        caplog.at_level(logging.DEBUG),
    ):
        check_lastfm_user(secret)

    loud = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("RuntimeError" in line for line in loud)
    assert not any(secret in line for line in loud)


@pytest.mark.parametrize(
    "check, provider",
    [
        ("_check_user_exists", "check_user_exists"),
        ("_check_profile_is_public", "check_profile_is_public"),
    ],
)
def test_a_stalled_last_fm_lookup_gives_up_within_the_precheck_budget(check, provider):
    """
    GIVEN Last.fm accepts the request and never answers
    WHEN the facade's lookup runs
    THEN it raises TimeoutError within the pre-check budget, not after the
    session's 30 seconds.

    Mutation: drop `timeout=` from either facade function and that row waits
    out the stall and returns instead of raising.
    """

    async def stalled(_username):
        await asyncio.sleep(3)

    with (
        patch(f"scrobblescope.routes.{provider}", stalled),
        patch("scrobblescope.routes.LASTFM_PRECHECK_TIMEOUT_SECONDS", 0.05),
    ):
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            getattr(routes, check)("someone")

    assert time.monotonic() - started < 1.5
```

- [ ] **Step 2: Run to verify they fail**

Run: `PY -m pytest tests/test_utils.py tests/test_precheck.py -q -p no:cacheprovider`
Expected: `test_utils.py` errors with `TypeError: run_async_in_thread() got an unexpected keyword argument 'timeout'`; `test_precheck.py` fails collection with `ModuleNotFoundError: No module named 'scrobblescope.routes.precheck'`.

- [ ] **Step 3: Implement**

`scrobblescope/config.py`, directly below `MAX_RETRY_AFTER_SECONDS`:

```python
# The longest one Last.fm pre-check lookup (does the user exist, is the
# profile public) may take before the form or button is answered "try again".
# Each lookup has its own budget, so a request thread is held at most twice
# this, not the HTTP session's 30 seconds per call: gunicorn runs four threads.
LASTFM_PRECHECK_TIMEOUT_SECONDS = float(
    os.getenv("LASTFM_PRECHECK_TIMEOUT_SECONDS", "5")
)
```

`scrobblescope/utils.py`: change the signature and the call, and extend the docstring.

```python
def run_async_in_thread(coro, timeout=None):
```
Add to the docstring, after the first paragraph: "*timeout* (seconds) bounds the whole coroutine: when it passes, the coroutine is cancelled and ``TimeoutError`` is raised in the calling thread, like any other failure. ``None`` waits as long as the coroutine takes." Replace the line `result.append(loop.run_until_complete(coro()))` with:

```python
            result.append(loop.run_until_complete(asyncio.wait_for(coro(), timeout)))
```

`scrobblescope/routes/__init__.py`: change `from scrobblescope.config import MAX_ACTIVE_JOBS` to

```python
from scrobblescope.config import LASTFM_PRECHECK_TIMEOUT_SECONDS, MAX_ACTIVE_JOBS
```

and in `_check_user_exists` and `_check_profile_is_public` change `return run_async_in_thread(_check)` to

```python
    return run_async_in_thread(_check, timeout=LASTFM_PRECHECK_TIMEOUT_SECONDS)
```

Extend each docstring with one sentence: "Bounded by ``LASTFM_PRECHECK_TIMEOUT_SECONDS``; a stalled Last.fm raises ``TimeoutError`` like any other failure." Change the tail import to

```python
from scrobblescope.routes import (  # noqa: E402,F401
    album_flow,
    api,
    heatmap_flow,
    pages,
    precheck,
)
```

(keep the following `from scrobblescope.routes.album_flow import (...)` statement as it is).

Create `scrobblescope/routes/precheck.py`:

```python
"""The Last.fm pre-check: one answer the album, heatmap and validate routes share.

Before a job starts, three routes ask Last.fm the same two questions: does the
user exist, and is recent listening public? Each used to carry its own copy and
its own idea of what a failure meant; the album route let an outage through and
started a job that was bound to fail. ``check_lastfm_user`` asks in the owner's
order (existence first, so a name Last.fm does not know is never given a
privacy verdict) and answers with one ``Verdict``. A lookup that cannot answer,
including one that exceeds ``LASTFM_PRECHECK_TIMEOUT_SECONDS``, is
``UNAVAILABLE``: the caller refuses retryably and starts nothing.

The two lookups are read from the ``routes`` facade at call time (see
``scrobblescope/routes/__init__.py``), so the test suite's patches at
``scrobblescope.routes._check_user_exists`` keep working.

A failure is logged by class only and never with the listener's name: the name
is listener data, and the exception text can carry the provider's URL.
"""

import enum
from dataclasses import dataclass

from scrobblescope import routes as _routes
from scrobblescope.utils import log_failure

#: What a listener is told when Last.fm could not answer. Retryable.
UNAVAILABLE_MESSAGE = "Validation service unavailable. Try again."


class Verdict(enum.Enum):
    """What Last.fm said about a name."""

    PUBLIC = "public"
    MISSING = "missing"
    PRIVATE = "private"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class UserCheck:
    """The pre-check's answer; ``registered_year`` is set only for ``PUBLIC``."""

    verdict: Verdict
    registered_year: int | None = None


def not_found_message(username):
    """Return the sentence shown when Last.fm does not know *username*."""
    return f"User '{username}' was not found on Last.fm."


def _read_existence(info):
    """Return ``(exists, registered_year)`` from the existence answer.

    Raises ``ValueError`` when the answer is not the expected shape: not a
    mapping, no boolean ``exists``, or a ``registered_year`` that is neither an
    int nor None (a missing ``registered_year`` is "unknown", not malformed).
    """
    if not isinstance(info, dict):
        raise ValueError("existence answer is not a mapping")
    exists = info.get("exists")
    if not isinstance(exists, bool):
        raise ValueError("existence answer has no boolean 'exists'")
    registered_year = info.get("registered_year")
    if registered_year is not None and (
        isinstance(registered_year, bool) or not isinstance(registered_year, int)
    ):
        raise ValueError("registered_year is not a number")
    return exists, registered_year


def check_lastfm_user(username):
    """Ask Last.fm whether *username* exists and is public; return a ``UserCheck``.

    Existence is asked first and a missing user ends the check, so the privacy
    lookup is never made for a name Last.fm does not know. An exception from
    either lookup (an HTTP failure, a bad body, a timeout) or an existence
    answer of the wrong shape is ``UNAVAILABLE``, never ``PUBLIC``: a check
    that could not answer must not let a job start, and a bad body must not
    become a 500.
    """
    try:
        exists, registered_year = _read_existence(
            _routes._check_user_exists(username)
        )
    except Exception:  # noqa: BLE001 -- logged by log_failure
        log_failure("User existence check failed")
        return UserCheck(Verdict.UNAVAILABLE)

    if not exists:
        return UserCheck(Verdict.MISSING)

    try:
        public = _routes._check_profile_is_public(username)
    except Exception:  # noqa: BLE001 -- logged by log_failure
        log_failure("Profile privacy check failed")
        return UserCheck(Verdict.UNAVAILABLE)

    if not public:
        return UserCheck(Verdict.PRIVATE)
    return UserCheck(Verdict.PUBLIC, registered_year)
```

- [ ] **Step 4: Run to verify they pass**

Run: `PY -m pytest tests/test_utils.py tests/test_precheck.py -q -p no:cacheprovider`
Expected: all pass. Then the whole suite: `PY -m pytest -q -p no:cacheprovider` -- expected: same failures as before the change: none.

- [ ] **Step 5: Mutation evidence**

| Planted defect | File | Test that must fail |
|---|---|---|
| `asyncio.wait_for(coro(), timeout)` becomes `coro()` (timeout ignored) | `scrobblescope/utils.py` | `test_run_async_in_thread_stops_waiting_when_the_timeout_passes` |
| drop `timeout=` in `_check_profile_is_public` | `scrobblescope/routes/__init__.py` | `test_a_stalled_last_fm_lookup_gives_up_within_the_precheck_budget[_check_profile_is_public-...]` |
| privacy `except` branch returns `UserCheck(Verdict.PUBLIC)` | `scrobblescope/routes/precheck.py` | `test_an_outage_on_the_privacy_check_is_unavailable_never_public` |
| call `_read_existence(...)` outside the `try` (or replace it with `info["exists"]`) | `scrobblescope/routes/precheck.py` | `test_a_malformed_existence_answer_is_unavailable_never_an_error` (rows without the key raise) |
| replace `_read_existence` with `info.get("exists")` truthiness | `scrobblescope/routes/precheck.py` | same test, `no-exists-key`, `exists-not-a-bool` and `none` rows |
| ask `_check_profile_is_public` before `_check_user_exists` | `scrobblescope/routes/precheck.py` | `test_a_missing_user_is_missing_and_privacy_is_never_asked` |
| log `f"... for {username}"` in the existence-check line | `scrobblescope/routes/precheck.py` | `test_a_failed_check_logs_the_class_and_never_the_listeners_name` |

Restore each with `git checkout -- <path>` (commit nothing yet; stage the files first with `git add` so the restore returns to the implemented version).

- [ ] **Step 6: Docs in the same commit**

SESSION_CONTEXT Section 3, in the `routes/` block after `api.py`: `    precheck.py               # check_lastfm_user: one exists/private/outage answer, each lookup timed out; shared by the album, heatmap and validate routes`.
Section 4: after the `routes/api.py` line add `routes/precheck.py     <- utils; routes (facade)`, and in the `routes/__init__.py` line change `routes/pages (imported last, for re-export)` to `routes/pages, routes/precheck (imported last, for re-export)`.
Key runtime facts (the list that holds `MAX_RETRY_AFTER_SECONDS`): after that bullet add a bullet saying `LASTFM_PRECHECK_TIMEOUT_SECONDS` (`config.py`, default 5) bounds each Last.fm pre-check lookup (exists, public) through `run_async_in_thread(coro, timeout=)`, and that a timeout is an outage, so the route refuses retryably.
`docs/architecture/runtime-system.md` is not touched here: `routes/precheck.py` is inside the `routes/` package, which that view draws as one node.

- [ ] **Step 7: Section 4 entry, gates, commit**

Entry heading: `### YYYY-MM-DD - Last.fm pre-check lookups have a time limit and one answer`. Body: scope; why (a slow Last.fm held one of four threads for up to 60 seconds; three routes each interpreted failure their own way); user-visible change now: the heatmap start and the blur check refuse after at most 5 seconds per lookup (the album route follows in the next commit); `LASTFM_PRECHECK_TIMEOUT_SECONDS`; the username leaves the pre-check's failure lines; a malformed Last.fm existence answer is an outage, not a 500; mutation table; Validation `pytest -q` N.
Commit: `feat(routes): Share one Last.fm pre-check answer with a short timeout`.

---

### Task 4: One admission path; threads read the job record

**Touches:** `scrobblescope/routes/admission.py` (new), `scrobblescope/jobs.py`, `scrobblescope/orchestrator/__init__.py`, `scrobblescope/heatmap.py`, `scrobblescope/routes/album_flow.py`, `scrobblescope/routes/heatmap_flow.py`, `scrobblescope/routes/__init__.py`, `tests/test_admission.py` (new), `tests/test_jobs.py`, `tests/services/test_orchestrator_fetch_and_process.py`, `tests/test_heatmap.py`, `tests/test_routes.py`, `.claude/SESSION_CONTEXT.md`, `docs/architecture/top-albums-sequence.md`, `docs/architecture/heatmap-sequence.md`, `docs/architecture/runtime-system.md`, `docs/agents/PLAYBOOK.md`
**After:** Task 3 (it rewrites the `routes/__init__.py` tail import and the SESSION_CONTEXT lines this task edits); uses Task 2 (`AlbumRequest.from_params`, `jobs.MODE_*`); Task 1's tests must pass unchanged after it.

**Files:** as listed above.

**Interfaces:**
- Consumes: `AlbumRequest.from_params`, `jobs.MODE_HEATMAP` (Task 2).
- Produces:
  - `jobs.params(job_id) -> dict | None`: a copy of the job's params, `None` when the job is gone; a read never renews the lease.
  - `routes.admission.Refused` (`CAPACITY`, `START_FAILED`) and `routes.admission.admit(params, target, *, label) -> str | Refused`: the new job id, or why not. `label` fills "Failed to start {label} thread" in the log.
  - `orchestrator.background_task(job_id)` and `heatmap.heatmap_task(job_id)`: read their parameters from the job record. A job that is gone, or a record that is not a usable request, runs nothing and still releases the slot the route acquired.
  - The thread is started as `start_job_thread(target, args=(job_id,))`.

Why: admission (expire, slot, create, start, delete on failure) is written twice and the ten parameters are re-passed positionally to a thread although the job record already holds them. The export route (WP-4) would be a third copy.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_admission.py`:

```python
"""Admission: expire, take a slot, create the job, start its thread."""

from unittest.mock import MagicMock, patch

from scrobblescope import jobs
from scrobblescope.routes.admission import Refused, admit


def _target(job_id):  # pragma: no cover - never run, only passed along
    raise AssertionError("the thread is stubbed in these tests")


PARAMS = {"username": "someone", "mode": "album"}


def test_an_admitted_job_holds_its_params_and_its_thread_gets_only_the_id():
    with (
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch("scrobblescope.routes.start_job_thread") as start,
    ):
        job_id = admit(PARAMS, _target, label="album task")

    assert jobs.context(job_id)["params"] == PARAMS
    start.assert_called_once_with(_target, args=(job_id,))


def test_a_full_house_refuses_and_creates_nothing(fresh_job_store):
    """Mutation: create the job before taking the slot and the store is not empty."""
    with (
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
        patch("scrobblescope.routes.start_job_thread") as start,
    ):
        result = admit(PARAMS, _target, label="album task")

    assert result is Refused.CAPACITY
    assert fresh_job_store.ids() == []
    start.assert_not_called()


def test_a_thread_that_will_not_start_leaves_no_orphan_job(fresh_job_store):
    """Mutation: remove the `jobs.delete` in the failure branch and the job stays."""
    with (
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch(
            "scrobblescope.routes.start_job_thread", side_effect=OSError("no threads")
        ),
    ):
        result = admit(PARAMS, _target, label="album task")

    assert result is Refused.START_FAILED
    assert fresh_job_store.ids() == []


def test_a_real_thread_start_failure_frees_the_slot_once_and_removes_the_job(
    fresh_job_store,
):
    """
    GIVEN every real piece of the path (the facade's acquire_job_slot and
    worker.start_job_thread are not patched) and a Thread that cannot start
    WHEN a job is admitted
    THEN admission answers START_FAILED, the store is empty, and the slot taken
    is released exactly once: by worker.start_job_thread, not again by admit.

    The semaphore is replaced by a counting double so a second release (which
    the real BoundedSemaphore would turn into a swallowed ValueError) is seen.

    Mutation: add `_routes.release_job_slot()` to admit's failure branch and
    the release count is 2; remove `jobs.delete(job_id)` and the store is not
    empty.
    """
    semaphore = MagicMock()
    semaphore.acquire.return_value = True
    with (
        patch("scrobblescope.worker._active_jobs_semaphore", semaphore),
        patch("scrobblescope.worker.threading.Thread") as thread_class,
    ):
        thread_class.return_value.start.side_effect = RuntimeError("cannot start")
        result = admit(PARAMS, _target, label="album task")

    assert result is Refused.START_FAILED
    assert fresh_job_store.ids() == []
    semaphore.acquire.assert_called_once()
    semaphore.release.assert_called_once()


def test_admission_drops_expired_jobs_first(fresh_job_store):
    """Mutation: remove `jobs.expire_stale()` from admit and the stale job survives."""
    stale = jobs.create({"username": "old", "mode": "album"})
    fresh_job_store.modify(stale, lambda record: record.update(updated_at=0))

    with (
        patch("scrobblescope.routes.acquire_job_slot", return_value=True),
        patch("scrobblescope.routes.start_job_thread"),
    ):
        admit(PARAMS, _target, label="album task")

    assert stale not in fresh_job_store.ids()
```

Append to `tests/test_jobs.py`:

```python
def test_params_returns_a_copy_and_none_for_a_missing_job():
    """
    GIVEN a job holding params
    WHEN a caller reads them and changes what it got
    THEN the job's own params are untouched; a missing job answers None.

    Mutation: return the stored dict itself and the second read sees "changed".
    """
    job_id = jobs.create(dict(TEST_JOB_PARAMS))

    got = jobs.params(job_id)
    got["username"] = "changed"

    assert jobs.params(job_id)["username"] == TEST_JOB_PARAMS["username"]
    assert jobs.params("no-such-job") is None
```

In `tests/services/test_orchestrator_fetch_and_process.py` add three tests after `test_background_task_crash_publishes_internal_error` (the first two here, the third after them):

```python
def test_background_task_runs_the_pipeline_with_the_job_records_parameters():
    """
    GIVEN a job whose record holds a value in every slot
    WHEN background_task is given only the job id
    THEN the pipeline is awaited with those values, each in its own slot.

    Mutation: pass the defaults for min_plays and min_tracks and this fails.
    """
    job_id = jobs.create(
        {
            **TEST_JOB_PARAMS,
            "username": "recorded",
            "year": 2023,
            "sort_mode": "playtime",
            "release_scope": "custom",
            "release_year": 1982,
            "min_plays": 7,
            "min_tracks": 4,
            "limit_results": "25",
            "include_unmatched": True,
        }
    )

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
        ) as mock_fp,
        patch("scrobblescope.orchestrator.release_job_slot"),
    ):
        background_task(job_id)

    mock_fp.assert_awaited_once_with(
        job_id,
        "recorded",
        2023,
        "playtime",
        "custom",
        None,
        1982,
        7,
        4,
        "25",
        include_unmatched=True,
    )


def test_background_task_for_a_vanished_job_runs_nothing_and_frees_its_slot():
    """
    GIVEN the job expired between admission and the thread's first line
    WHEN background_task runs
    THEN the pipeline is not run and the slot the route took is released once.

    Mutation: drop `release_job_slot()` from the vanished-job branch and the
    slot leaks (the assertion on mock_release fails).
    """
    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
        ) as mock_fp,
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task("no-such-job")

    mock_fp.assert_not_called()
    mock_release.assert_called_once()
```

And a third test in the same file, covering the record that is not a usable request:

```python
def test_background_task_for_an_unusable_record_fails_the_job_and_frees_its_slot():
    """
    GIVEN a job record that holds no username or year (not a usable request)
    WHEN background_task runs
    THEN the pipeline is not run, the job ends as internal_error so a polling
    page stops waiting, and the slot the route took is released once.

    Mutation: drop `jobs.fail(job_id, "internal_error")` from
    `_album_request_for` and the job never ends; drop the release in
    background_task and mock_release is not called.
    """
    job_id = jobs.create({"mode": "album"})

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
        ) as mock_fp,
        patch("scrobblescope.orchestrator.release_job_slot") as mock_release,
    ):
        background_task(job_id)

    mock_fp.assert_not_called()
    mock_release.assert_called_once()
    assert jobs.progress(job_id)["error_code"] == "internal_error"
```

In `tests/test_heatmap.py`, inside `class TestHeatmapTask`, add:

```python
    def test_the_username_comes_from_the_job_record(self):
        """heatmap_task takes only the job id and reads the name from the record.

        Mutation: pass a literal name to the pipeline and this fails.
        """
        job_id = jobs.create({"username": "recorded", "mode": "heatmap"})
        with (
            patch("scrobblescope.heatmap.release_job_slot"),
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
            ) as mock_pipeline,
        ):
            heatmap_task(job_id)

        mock_pipeline.assert_awaited_once_with(job_id, "recorded")

    def test_a_vanished_job_runs_nothing_and_frees_its_slot(self):
        """Mutation: drop the release in the vanished-job branch and the slot leaks."""
        with (
            patch("scrobblescope.heatmap.release_job_slot") as mock_release,
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
            ) as mock_pipeline,
        ):
            heatmap_task("no-such-job")

        mock_pipeline.assert_not_called()
        mock_release.assert_called_once()
```

- [ ] **Step 2: Edit the existing tests that call the old signatures**

Name each in the commit body.

Every `background_task(` and `heatmap_task(` call site in the repository (`git grep -n "background_task(\|heatmap_task(" -- tests scripts scrobblescope` at 5dde407; re-run it at implementation time and edit any further hit) is edited below. Nothing in `scripts/` calls either.

`tests/services/test_orchestrator_fetch_and_process.py` has six `background_task(` call sites. Five are the short form: replace every `background_task(job_id, "flounder14", 2025, "playcount", "same")` with `background_task(job_id)` (the five tests: `test_background_task_runs_single_event_loop`, `..._releases_slot_on_exception`, `..._releases_slot_when_event_loop_setup_raises`, `..._releases_slot_when_loop_close_raises`, `test_background_task_crash_publishes_internal_error`). The sixth is the multi-line call with eleven positional arguments in `test_background_task_stores_unmatched_rows_when_the_flag_is_on` (inside its `for flag in (True, False):` loop); replace the whole call

```python
            background_task(
                job_id,
                "flounder14",
                2025,
                "playcount",
                "same",
                None,
                None,
                10,
                3,
                "all",
                flag,
            )
```

with `            background_task(job_id)`. Its job is created from `{**TEST_JOB_PARAMS, "include_unmatched": flag}`, and `TEST_JOB_PARAMS` already holds year 2025, `playcount`, `same`, no decade or release year, 10, 3 and `all`, so the record carries every value the call used except the name (`testuser`, not `flounder14`), which the test's assertions (stored rows and the "Found N albums" message) do not read. Its Mutation sentence stays true. In `test_background_task_runs_single_event_loop` change `assert call_args[0][1] == "flounder14"` to `assert call_args[0][1] == "testuser"` (the record's name: `TEST_JOB_PARAMS`).

`tests/test_heatmap.py` `TestHeatmapTask`: add a helper first in the class,

```python
    @staticmethod
    def _job():
        return jobs.create({"username": "user", "mode": "heatmap"})
```

then replace (all seven `heatmap_task(` call sites, in `tests/test_heatmap.py`): `heatmap_task("job-ok", "user")` with `heatmap_task(self._job())`; `heatmap_task("job-err", "user")` with `heatmap_task(self._job())`; both `heatmap_task("job-loop-err", "user")` with `heatmap_task(self._job())`; and the three `heatmap_task(job_id, "user")` / `heatmap_task(job_id, "ghost")` calls with `heatmap_task(job_id)`. (Those three create their job from `TEST_JOB_PARAMS`, whose name is "testuser"; they assert only on the published error.)

`tests/test_routes.py::test_results_loading_passes_the_include_flag_to_the_job_thread`: change its docstring's "the thread receives the flag as background_task's last argument" to "the thread receives only the job id and the record holds the flag"; replace the `mock_start.call_args.kwargs["args"][-1]` element of the tuple with `mock_start.call_args.kwargs["args"]` and compare against `(job_id,)`:

```python
        flags[key] = (
            jobs.context(job_id)["params"]["include_unmatched"],
            mock_start.call_args.kwargs["args"] == (job_id,),
        )

    assert flags == {
        "all": (True, True),
        "matched": (False, True),
        "absent": (False, True),
    }
```

and change the "Mutation:" sentence to "Mutation: leave the flag out of the job record and the first element fails."

- [ ] **Step 3: Run to verify the new tests fail**

Run: `PY -m pytest tests/test_admission.py tests/test_jobs.py tests/test_heatmap.py tests/services/test_orchestrator_fetch_and_process.py -q -p no:cacheprovider`
Expected: `ModuleNotFoundError: No module named 'scrobblescope.routes.admission'` for the admission file; `AttributeError: module 'scrobblescope.jobs' has no attribute 'params'`; the thread-entry tests fail with `TypeError` (extra arguments).

- [ ] **Step 4: Implement**

`scrobblescope/jobs.py`, in the reads section after `unmatched(job_id)`:

```python
def params(job_id):
    """Return a copy of the job's params, or None if the job is gone.

    The thread entry points read their parameters here instead of receiving
    them as arguments, so the job record is the one place a run's parameters
    live. A read never renews the lease.
    """
    return _store.read(job_id, lambda record: dict(record.get("params", {})))
```

Create `scrobblescope/routes/admission.py`:

```python
"""Job admission: the one path that starts a job.

Expire stale jobs, take a concurrency slot, create the job with its
parameters, start its thread with the job id alone, and undo the job if the
thread will not start. The album route and the heatmap route used to write
this twice; the Spotify export route (Batch 23 WP-4) is the third caller.
Each route keeps its own request parsing, session key and HTTP response.

Slot ownership: ``admit`` takes the slot, and from the moment the thread is
started the thread's ``run_coroutine_in_new_loop`` releases it. When the
thread cannot be started, ``worker.start_job_thread`` releases it before
re-raising, so ``admit`` must not release it again.

The slot and thread functions are read from the ``routes`` facade at call time
(see ``scrobblescope/routes/__init__.py``), so the suite's patches at
``scrobblescope.routes.acquire_job_slot`` and ``.start_job_thread`` keep working.
"""

import enum

from scrobblescope import jobs
from scrobblescope import routes as _routes
from scrobblescope.utils import log_failure


class Refused(enum.Enum):
    """Why a job was not admitted."""

    CAPACITY = "capacity"
    START_FAILED = "start_failed"


def admit(params, target, *, label):
    """Admit one job and return its id, or a ``Refused`` member.

    Args:
        params: The job record's params, including its kind (``mode``).
        target: The thread entry point; it is called with the job id alone.
        label: Names the thread in the failure log ("Failed to start {label}
            thread").
    """
    jobs.expire_stale()

    if not _routes.acquire_job_slot():
        return Refused.CAPACITY

    job_id = jobs.create(params)

    try:
        _routes.start_job_thread(target, args=(job_id,))
    except Exception:  # noqa: BLE001 -- logged by log_failure
        log_failure(f"Failed to start {label} thread")
        jobs.delete(job_id)
        return Refused.START_FAILED

    return job_id
```

`scrobblescope/routes/__init__.py`: add `admission` to the tail import list (alphabetical, first).

`scrobblescope/orchestrator/__init__.py`: add `from scrobblescope.album_request import AlbumRequest` as the first `from scrobblescope...` import (above `from scrobblescope import jobs` is not alphabetical; place it after `from scrobblescope import jobs`, before `from scrobblescope.cache import (`). Replace `background_task` with:

```python
def _album_request_for(job_id):
    """Return the job's ``AlbumRequest`` read from its record, or None.

    None means the run cannot start: the job expired between admission and the
    thread's first line (nothing to publish to), or its record is not a usable
    request (published as ``internal_error`` so a polling page stops waiting).
    """
    params = jobs.params(job_id)
    if params is None:
        logging.warning("Album job %s was gone before its thread started.", job_id)
        return None
    try:
        return AlbumRequest.from_params(params)
    except TypeError:
        log_failure("Album job record is not a usable request")
        jobs.fail(job_id, "internal_error")
        return None


def background_task(job_id):
    """Run the album pipeline on this thread, in a loop the worker owns.

    The parameters come from the job record (``jobs.params``), not from
    arguments: admission stored them there. A job that is gone or unreadable
    runs nothing, and the slot the route acquired is still released.

    The build-run-close-release protocol lives in
    ``worker.run_coroutine_in_new_loop``. What stays here is the reaction to
    a failed run: ``_report_album_failure`` logs it and publishes
    ``internal_error``. Upstream failures are classified deeper in, inside
    ``_fetch_and_process``, so this backstop only sees faults that are ours.

    ``include_unmatched`` (default off) keeps the albums Spotify and Deezer
    could not match in the results, ranked by play count.
    """
    album = _album_request_for(job_id)
    if album is None:
        release_job_slot()
        return
    run_coroutine_in_new_loop(
        _fetch_and_process(
            job_id,
            album.username,
            album.year,
            album.sort_mode,
            album.release_scope,
            album.decade,
            album.release_year,
            album.min_plays,
            album.min_tracks,
            album.limit_results,
            include_unmatched=album.include_unmatched,
        ),
        # Passed explicitly rather than left to the helper's own defaults: the tests
        # patch ``scrobblescope.orchestrator.release_job_slot``, and a default taken
        # from the helper's module would move that patch target without failing.
        make_loop=new_thread_event_loop,
        release_slot=release_job_slot,
        on_run_error=lambda _exc: _report_album_failure(job_id, album.username, album.year),
    )
```

(If ruff format wraps the last line, accept its output.)

`scrobblescope/heatmap.py`: replace `heatmap_task` with

```python
def heatmap_task(job_id):
    """Thread entry point: run the heatmap pipeline in a dedicated event loop.

    The username comes from the job record (``jobs.params``), where admission
    stored it. A job that is gone runs nothing, and the slot the route
    acquired is still released.

    The build-run-close-release protocol, including that the loop is built inside
    the ``try`` so the slot is released in the ``finally``, lives in
    ``worker.run_coroutine_in_new_loop``. What stays here is local: a failed
    run is reported rather than raised, classified by
    ``errors.classify_exception_to_error_code`` first and falling back to
    ``internal_error`` (see ``_report_heatmap_failure``). The album entry
    point's backstop (``_report_album_failure``) does not classify: it always
    publishes ``internal_error`` (F-SWE-5).
    """
    username = (jobs.params(job_id) or {}).get("username")
    if not username:
        logging.warning("Heatmap job %s was gone before its thread started.", job_id)
        release_job_slot()
        return
    run_coroutine_in_new_loop(
        _fetch_and_process_heatmap(job_id, username),
        # Explicit, for the same reason as the album entry point: these tests patch
        # ``scrobblescope.heatmap.release_job_slot`` and ``scrobblescope.jobs.fail``.
        make_loop=new_thread_event_loop,
        release_slot=release_job_slot,
        on_run_error=lambda exc: _report_heatmap_failure(job_id, username, exc),
    )
```

`scrobblescope/routes/album_flow.py`: add `from scrobblescope.routes import admission` (after `from scrobblescope import routes as _routes`), remove the now-unused `from scrobblescope.utils import log_failure`. In `results_loading` replace everything from `jobs.expire_stale()` to the end of the function with:

```python
    params = {
        "username": username,
        "year": year,
        "sort_mode": sort_mode,
        "include_unmatched": include_unmatched,
        "release_scope": release_scope,
        "decade": decade,
        "release_year": release_year,
        "min_plays": min_plays,
        "min_tracks": min_tracks,
        "limit_results": limit_results,
    }

    admitted = admission.admit(params, background_task, label="background task")
    if admitted is admission.Refused.CAPACITY:
        return render_template("index.html", error=_routes._capacity_message())
    if admitted is admission.Refused.START_FAILED:
        return render_template(
            "index.html", error="Failed to start processing. Please try again."
        )

    session[_routes._LATEST_ALBUM_JOB] = admitted

    return redirect(url_for(".loading_page", job_id=admitted), code=303)
```

`scrobblescope/routes/heatmap_flow.py`: add `from scrobblescope.routes import admission` after the `_routes` import, and replace `_dispatch_heatmap_job` with:

```python
def _dispatch_heatmap_job(username):
    """Admit a heatmap job, saving its ID only after startup.

    Admission removes the orphan job and the slot if thread startup fails.
    """
    admitted = admission.admit(
        {"username": username, "mode": jobs.MODE_HEATMAP},
        heatmap_task,
        label="heatmap task",
    )
    if admitted is admission.Refused.CAPACITY:
        return (
            jsonify(
                {
                    "error": True,
                    "message": _routes._capacity_message(),
                    "retryable": True,
                }
            ),
            429,
        )
    if admitted is admission.Refused.START_FAILED:
        return (
            jsonify(
                {
                    "error": True,
                    "message": "Failed to start processing.",
                    "retryable": True,
                }
            ),
            500,
        )

    session[_routes._LATEST_HEATMAP_JOB] = admitted
    return jsonify({"job_id": admitted}), 202
```

- [ ] **Step 5: Run to verify**

Run: `PY -m pytest -q -p no:cacheprovider`
Expected: everything passes, including Task 1's `tests/test_request_flow_parity.py` unchanged (the inline-thread tests now exercise `background_task(job_id)` and `heatmap_task(job_id)`), `tests/test_pipeline_integration.py` (a real thread reading a real record), and `tests/services/test_failure_logging.py` (`Failed to start background task thread` / `Failed to start heatmap task thread` are unchanged).

- [ ] **Step 6: Mutation evidence**

| Planted defect | File | Test that must fail |
|---|---|---|
| `jobs.create` before `acquire_job_slot` | `scrobblescope/routes/admission.py` | `test_a_full_house_refuses_and_creates_nothing` |
| remove `jobs.delete(job_id)` | same | `test_a_thread_that_will_not_start_leaves_no_orphan_job` |
| remove `jobs.expire_stale()` | same | `test_admission_drops_expired_jobs_first` |
| pass `DEFAULT_MIN_PLAYS`/`DEFAULT_MIN_TRACKS` instead of the record's | `scrobblescope/orchestrator/__init__.py` | `test_background_task_runs_the_pipeline_with_the_job_records_parameters` and Task 1's `test_the_forms_values_reach_the_album_pipeline_in_order` |
| drop `release_job_slot()` in the vanished-job branch | `scrobblescope/orchestrator/__init__.py` | `test_background_task_for_a_vanished_job_runs_nothing_and_frees_its_slot` |
| drop `jobs.fail(job_id, "internal_error")` from `_album_request_for` | `scrobblescope/orchestrator/__init__.py` | `test_background_task_for_an_unusable_record_fails_the_job_and_frees_its_slot` |
| release the slot again in `admit`'s failure branch | `scrobblescope/routes/admission.py` | `test_a_real_thread_start_failure_frees_the_slot_once_and_removes_the_job` |
| return the stored dict from `jobs.params` | `scrobblescope/jobs.py` | `test_params_returns_a_copy_and_none_for_a_missing_job` |
| hard-code `"user"` for the heatmap name | `scrobblescope/heatmap.py` | `test_the_username_comes_from_the_job_record` |

- [ ] **Step 7: Docs in the same commit**

SESSION_CONTEXT Section 3, `routes/` block, after the new `precheck.py` line: `    admission.py              # admit: expire, slot, create, start the thread with the job id only; Refused.CAPACITY / START_FAILED`. Section 4: add `routes/admission.py   <- jobs, utils; routes (facade)`; change `orchestrator/__init__.py  <- cache, config, ...` to start `<- album_request, cache, config, ...`; change `routes/album_flow.py    <- jobs, orchestrator, spotlight, unmatched, utils; routes (facade)` to `<- admission, jobs, orchestrator, spotlight, unmatched; routes (facade)` (it no longer imports `utils`); change `routes/heatmap_flow.py  <- heatmap, jobs, utils; routes (facade)` to `<- admission, heatmap, jobs, utils; routes (facade)`; in the `routes/__init__.py` line add `routes/admission` to the imported-last list. Section 5, request flow: replace

```
    -> jobs.expire_stale()
    -> acquire_job_slot() [worker.py] -- BEFORE jobs.create; on failure the
       request is rejected and no job is created
    -> jobs.create(params) -> UUID in the job store
    -> start_job_thread(background_task, args=(...)) [worker.py]
```

with

```
    -> admission.admit (routes/admission.py): jobs.expire_stale(), then
       acquire_job_slot() [worker.py] -- BEFORE jobs.create; on failure the
       request is rejected and no job is created
    -> jobs.create(params) -> UUID in the job store
    -> start_job_thread(background_task, args=(job_id,)) [worker.py]
```

and after `background_task (orchestrator/__init__.py, daemon Thread):` add the line `  -> reads its AlbumRequest from the job record (jobs.params)`.

`docs/architecture/runtime-system.md`: add the edge `    Album --> AlbumRequest` after the `Album --> Unmatched` edge (the orchestrator now imports `album_request`; the node was added in Task 2), and in the paragraph on `jobs.py` change "the reads `progress`, `context` and\n`unmatched`" to "the reads `progress`, `context`, `params` and\n`unmatched`" (keep the file's line wrap). Validate the diagram with the `validate_and_render_mermaid_diagram` MCP call.

`docs/architecture/top-albums-sequence.md`: change `Routes->>Worker: start_job_thread(background_task, args)` to `Routes->>Worker: start_job_thread(background_task, job_id)`; change `Worker->>Orch: background_task(job_id, parameters)` to `Worker->>Orch: background_task(job_id)` and add on the next line `Orch->>Jobs: params(job_id), the parameters admission stored`. `docs/architecture/heatmap-sequence.md`: change `Routes->>Worker: start_job_thread(heatmap_task, args)` to `Routes->>Worker: start_job_thread(heatmap_task, job_id)` and `Worker->>Heatmap: heatmap_task(job_id, username)` to `Worker->>Heatmap: heatmap_task(job_id)` followed by `Heatmap->>Jobs: params(job_id), the username admission stored`. Validate both blocks with the Mermaid MCP call.

- [ ] **Step 8: Section 4 entry, gates, commit**

Entry heading: `### YYYY-MM-DD - Jobs start through one admission path`. Body: why (admission written twice, ten parameters re-passed positionally; the record already holds them); what changed (`admission.admit`, `jobs.params`, thread entry points take the job id, a vanished job frees its slot); no listener-visible change; the existing tests edited, each named (the six `background_task` call sites in `tests/services/test_orchestrator_fetch_and_process.py`: `test_background_task_runs_single_event_loop` (call and its name assertion), `..._releases_slot_on_exception`, `..._releases_slot_when_event_loop_setup_raises`, `..._releases_slot_when_loop_close_raises`, `test_background_task_crash_publishes_internal_error` and `test_background_task_stores_unmatched_rows_when_the_flag_is_on`; the seven `heatmap_task(` calls in `tests/test_heatmap.py` `TestHeatmapTask`; `tests/test_routes.py::test_results_loading_passes_the_include_flag_to_the_job_thread`); the failed-thread-start path tested for real (not patched) in `tests/test_admission.py`; Validation `pytest -q` N.
Commit: `refactor(routes): Admit jobs in one place; threads read the job record`.
Commit body lists every edited existing test by name (BATCH23_DEFINITION Intended outcome).

---

### Task 5: The album route parses, pre-checks, then admits

**Touches:** `scrobblescope/routes/album_flow.py`, `tests/test_album_request_flow.py` (new), `tests/test_precheck_routes.py` (new), `tests/test_routes.py`, `tests/test_pipeline_integration.py`, the Retry contract test (located in Step 4, item 4), `.claude/SESSION_CONTEXT.md`, `docs/architecture/top-albums-sequence.md`, `docs/architecture/runtime-system.md`, `docs/agents/PLAYBOOK.md`
**After:** Tasks 2, 3, 4

**Files:** as listed.

**Interfaces:**
- Consumes: `parse_album_request`, `Refusal`, `registration_refusal` (Task 2); `precheck.check_lastfm_user`, `precheck.Verdict`, `precheck.UNAVAILABLE_MESSAGE`, `precheck.not_found_message` (Task 3); `admission.admit`, `admission.Refused` (Task 4).
- Produces: `POST /results_loading` behaviour: a bad field is refused on the form with its sentence and no lookup; a Last.fm outage or timeout is refused with HTTP 503 and starts nothing; the job record is written by `AlbumRequest.to_params()` (so it carries `mode: "album"`).

Why: this is the user-visible change of the PR (record both in the Section 4 entry): (1) a bad filter value is refused on the form with its field named instead of showing "no albums"; (2) an outage during the pre-check is refused retryably instead of starting a job that fails.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_album_request_flow.py`:

```python
"""POST /results_loading: parse, pre-check, admit -- and refuse before any job."""

from unittest.mock import MagicMock, patch

import pytest

from scrobblescope import jobs
from tests.helpers import VALID_FORM_DATA

PUBLIC_USER = {"exists": True, "registered_year": None}


@pytest.mark.parametrize(
    "overrides, sentence",
    [
        ({"release_scope": "forever"}, "Choose a release filter from the list."),
        (
            {"release_scope": "decade", "decade": "2030s"},
            "Choose a decade from the list.",
        ),
        (
            {"release_scope": "custom", "release_year": "1899"},
            "Release year must be between 1900 and 2025.",
        ),
        ({"sort_by": "loudness"}, "Choose Play count or Play time to rank by."),
        ({"limit_results": "7"}, "Choose how many albums to show from the list."),
        (
            {"min_plays": "0"},
            "Minimum plays must be a whole number from 1 to 50.",
        ),
        (
            {"min_tracks": "11"},
            "Minimum unique tracks must be a whole number from 1 to 10.",
        ),
    ],
)
def test_a_bad_filter_is_refused_on_the_form_and_starts_nothing(
    client, fresh_job_store, overrides, sentence
):
    """
    GIVEN a form whose filter value the form never offers
    WHEN POST /results_loading is submitted
    THEN the form comes back with that field's sentence (the listener is not
    shown "no albums" later), Last.fm is not asked, and nothing starts.

    Mutation: skip the decade membership check in album_request and the
    decade row starts a job.
    """
    with (
        patch("scrobblescope.routes._current_year", return_value=2025),
        patch("scrobblescope.routes._check_user_exists") as lookup,
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post(
            "/results_loading", data={**VALID_FORM_DATA, **overrides}
        )

    assert response.status_code == 200
    assert sentence in response.get_data(as_text=True)
    lookup.assert_not_called()
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


@pytest.mark.parametrize("failing", ["exists", "privacy"])
def test_a_pre_check_outage_refuses_retryably_and_starts_nothing(
    client, fresh_job_store, failing
):
    """
    GIVEN Last.fm cannot answer the existence check, or the privacy check
    WHEN POST /results_loading is submitted
    THEN the answer is the retryable 503, no slot is taken and no job starts
    (before this the route logged "proceeding" and started a doomed job).

    Mutation: treat UNAVAILABLE like PUBLIC in the route and both rows start a job.
    """
    down = {"side_effect": RuntimeError("down")}
    exists = down if failing == "exists" else {"return_value": PUBLIC_USER}
    privacy = down if failing == "privacy" else {"return_value": True}
    with (
        patch("scrobblescope.routes._check_user_exists", **exists),
        patch("scrobblescope.routes._check_profile_is_public", **privacy),
        patch("scrobblescope.routes.acquire_job_slot", MagicMock(return_value=True)) as slot,
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert response.status_code == 503
    assert "Validation service unavailable. Try again." in response.get_data(
        as_text=True
    )
    slot.assert_not_called()
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


@pytest.mark.parametrize(
    "answer",
    [{"registered_year": 2000}, {"exists": "yes", "registered_year": 2000}, None],
    ids=["no-exists-key", "exists-not-a-bool", "none"],
)
def test_a_malformed_last_fm_answer_refuses_retryably_and_starts_nothing(
    client, fresh_job_store, answer
):
    """
    GIVEN Last.fm answers the existence check with a body of the wrong shape
    WHEN POST /results_loading is submitted
    THEN the listener gets the retryable 503, not a 500 and not a started job.

    Mutation: read `info["exists"]` outside precheck's try (the route 500s),
    or treat a missing `exists` as true (a job starts).
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=answer),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert response.status_code == 503
    assert "Validation service unavailable. Try again." in response.get_data(
        as_text=True
    )
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []


def test_an_album_job_record_says_it_is_an_album_job(client, fresh_job_store):
    """The kind is written when the job is created, not defaulted when read.

    Mutation: build the params without `mode` and this fails.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=PUBLIC_USER),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.start_job_thread"),
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert response.status_code == 303
    (job_id,) = fresh_job_store.ids()
    assert jobs.context(job_id)["params"]["mode"] == "album"
```

Create `tests/test_precheck_routes.py`:

```python
"""One Last.fm answer, three routes: the album form, the heatmap start and the blur check.

A listener must be told the same thing about a name whichever button asks.
This table is the parity test for moving the heatmap and validate routes onto
the shared pre-check (it passes for them before that move, and for the album
route once it uses the pre-check).
"""

import asyncio
import html
import time
from unittest.mock import patch

import pytest

from scrobblescope.routes import _PRIVATE_PROFILE_MESSAGE
from tests.helpers import VALID_FORM_DATA

ROUTES = ("album", "heatmap", "validate")
KNOWN = {"exists": True, "registered_year": 2016}
GHOST = {"exists": False, "registered_year": None}
DOWN = RuntimeError("down")

#: answer name -> (existence lookup, privacy lookup, what the listener is told)
ANSWERS = {
    "public": (KNOWN, True, "accepted"),
    "missing": (GHOST, True, "not_found"),
    "private": (KNOWN, False, "private"),
    "outage-on-existence": (DOWN, True, "unavailable"),
    "outage-on-privacy": (KNOWN, DOWN, "unavailable"),
}


def _kwargs(value):
    return {"side_effect": value} if isinstance(value, Exception) else {
        "return_value": value
    }


def _call(client, route):
    if route == "album":
        return client.post("/results_loading", data=VALID_FORM_DATA)
    if route == "heatmap":
        return client.post("/heatmap_loading", data={"username": "flounder14"})
    return client.get("/validate_user", query_string={"username": "flounder14"})


def _outcome(route, response):
    """Name what the listener was told, in words every route shares."""
    if route == "album":
        if response.status_code == 303:
            return "accepted"
        text = response.get_data(as_text=True)
        if response.status_code == 503 and "Validation service unavailable" in text:
            return "unavailable"
        if "was not found on Last.fm" in text:
            return "not_found"
        if html.escape(_PRIVATE_PROFILE_MESSAGE) in text:
            return "private"
        return f"unclassified {response.status_code}"
    body = response.get_json()
    if route == "heatmap":
        if response.status_code == 202:
            return "accepted"
        if response.status_code == 503:
            return "unavailable"
        return {"user_not_found": "not_found", "private_profile": "private"}.get(
            body.get("error_code"), f"unclassified {response.status_code}"
        )
    if response.status_code == 503:
        return "unavailable"
    if body["valid"]:
        return "accepted"
    if "not found" in body["message"]:
        return "not_found"
    if "private" in body["message"].lower():
        return "private"
    return f"unclassified {response.status_code}"


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("answer", list(ANSWERS))
def test_every_route_reads_the_last_fm_answer_the_same_way(
    client, fresh_job_store, route, answer
):
    """
    Mutation: ask for privacy before existence (the "missing" row then calls
    the privacy mock), or let an outage through in any route (the outage rows
    then report "accepted").
    """
    exists, public, expected = ANSWERS[answer]
    with (
        patch("scrobblescope.routes._check_user_exists", **_kwargs(exists)),
        patch(
            "scrobblescope.routes._check_profile_is_public", **_kwargs(public)
        ) as privacy,
        patch("scrobblescope.routes.start_job_thread"),
    ):
        response = _call(client, route)

    assert _outcome(route, response) == expected
    if answer in ("missing", "outage-on-existence"):
        privacy.assert_not_called()
    starts_a_job = expected == "accepted" and route != "validate"
    assert (len(fresh_job_store.ids()) == 1) is starts_a_job


@pytest.mark.parametrize("route", ROUTES)
def test_a_stalled_last_fm_costs_a_route_its_budget_not_the_session(
    client, fresh_job_store, route
):
    """
    GIVEN Last.fm accepts the lookup and never answers
    WHEN any of the three routes asks
    THEN it answers "unavailable" within the pre-check budget and starts nothing.

    Mutation: remove `timeout=` from `routes._check_user_exists` and each row
    waits the stall out and then accepts.
    """

    async def stalled(_username):
        await asyncio.sleep(3)

    with (
        patch("scrobblescope.routes.check_user_exists", stalled),
        patch("scrobblescope.routes.LASTFM_PRECHECK_TIMEOUT_SECONDS", 0.05),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        started = time.monotonic()
        response = _call(client, route)
        elapsed = time.monotonic() - started

    assert _outcome(route, response) == "unavailable"
    assert elapsed < 1.5
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []
```

- [ ] **Step 2: Run to verify the right ones fail**

Run: `PY -m pytest tests/test_album_request_flow.py tests/test_precheck_routes.py -q -p no:cacheprovider`
Expected: FAIL for the album rows only: every bad-filter row (the route starts a job), both outage rows (303 instead of 503), the three malformed-answer rows (the old route swallows the `KeyError` or `TypeError` and proceeds), `test_an_album_job_record_says_it_is_an_album_job` (`KeyError: 'mode'`), and the `album` rows of the two table tests for the outage answers. All `heatmap` and `validate` rows already PASS: that is the parity evidence for Task 6.

- [ ] **Step 3: Rewrite the route**

`scrobblescope/routes/album_flow.py`: add the imports

```python
from scrobblescope.album_request import (
    Refusal,
    parse_album_request,
    registration_refusal,
)
from scrobblescope.routes import admission, precheck
```

(replace the Task 4 `from scrobblescope.routes import admission` line with the second block) and add above `results_loading`:

```python
def _refuse(message, status=200):
    """Re-render the form with *message*.

    Every refusal is a 200 with the reason on the form, except an outage of the
    Last.fm pre-check, which is a retryable 503: the listener can try again.
    """
    return render_template("index.html", error=message), status
```

Replace the whole body of `results_loading` after its docstring (keep `@bp.route`) with:

```python
    album = parse_album_request(request.form, current_year=_routes._current_year())
    if isinstance(album, Refusal):
        logging.warning("Album form refused on field %s.", album.field)
        return _refuse(album.message)

    # Existence first, then privacy: a name Last.fm does not know gets "not
    # found", never a verdict about a ghost. A lookup that cannot answer
    # refuses retryably and starts nothing.
    check = precheck.check_lastfm_user(album.username)
    if check.verdict is precheck.Verdict.UNAVAILABLE:
        return _refuse(precheck.UNAVAILABLE_MESSAGE, status=503)
    if check.verdict is precheck.Verdict.MISSING:
        return _refuse(precheck.not_found_message(album.username))
    if check.verdict is precheck.Verdict.PRIVATE:
        return _refuse(_routes._PRIVATE_PROFILE_MESSAGE)

    # The registration-year comparison is the one optional step: an account
    # whose registration year Last.fm did not report is simply not compared.
    hint = registration_refusal(album.year, check.registered_year)
    if hint is not None:
        return _refuse(hint.message)

    admitted = admission.admit(
        album.to_params(), background_task, label="background task"
    )
    if admitted is admission.Refused.CAPACITY:
        return _refuse(_routes._capacity_message())
    if admitted is admission.Refused.START_FAILED:
        return _refuse("Failed to start processing. Please try again.")

    session[_routes._LATEST_ALBUM_JOB] = admitted

    return redirect(url_for(".loading_page", job_id=admitted), code=303)
```

Replace the docstring of `results_loading` with: `"""Turn the submitted form into a job, or re-render the form with one reason.\n\n    Order: parse the form (no network), pre-check the Last.fm user, compare the\n    registration year, admit the job. Each step that refuses ends the request\n    before the next one runs, so a refusal never costs a slot or a job.\n    """`.

The imports `logging`, `jsonify`, `redirect`, `render_template`, `request`, `session`, `url_for` are all still used; remove nothing else.

- [ ] **Step 4: Edit the existing tests that asserted the old fail-open**

Three existing tests change, plus the Retry contract test. In `tests/test_routes.py`:

1. Replace `test_results_loading_registration_check_unavailable_proceeds` with:

```python
def test_results_loading_lookup_unavailable_refuses_and_starts_nothing(
    client, fresh_job_store
):
    """
    GIVEN the Last.fm lookup raises (Last.fm unavailable)
    WHEN POST /results_loading is submitted
    THEN the route refuses retryably (503) and starts no job; it no longer
    proceeds without the check.
    """
    with (
        patch(
            "scrobblescope.routes.run_async_in_thread",
            side_effect=Exception("network error"),
        ),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)
    assert response.status_code == 503
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []
```

2. In `test_results_loading_registration_check_failure_logs_no_message`: rename it `test_results_loading_lookup_failure_logs_no_message_and_no_name`, change its docstring to "The pre-check writes the exception class, not its message and not the listener's name, when the Last.fm call fails.", and replace the assertion `assert "Registration year check failed for flounder14" in text` with `assert "User existence check failed" in text` and add `assert "flounder14" not in text` after the `Zqxv` assertion.

3. In `tests/test_pipeline_integration.py::test_album_pipeline_runs_on_a_real_thread_end_to_end`, change the mock

```python
        patch(
            "scrobblescope.routes.check_user_exists",
            return_value={"registered_year": 2000},
        ),
```

to

```python
        patch(
            "scrobblescope.routes.check_user_exists",
            return_value={"exists": True, "registered_year": 2000},
        ),
```

Reason (also the commit body's sentence): the old mock had no `exists` key; the old route read `user_info["exists"]` inside a broad `except` that logged "proceeding" and went on, so the test passed by accident on a swallowed `KeyError`. The pre-check now treats a malformed Last.fm answer as an outage and refuses, so the mock must be a well-formed answer for the test to reach the pipeline it exists to exercise. Nothing else in that test changes.

4. The Retry contract (PR #256, fix F3). The loading page's Retry (`retryCurrentSearch` in `static/js/loading.js`) must post back every form field the album route reads; PR #256 adds a contract test for it. After this task those fields are read in `album_request.parse_album_request`, no longer in `results_loading`, so a test that finds the field set by scanning the source of `results_loading` for `request.form.get(` finds nothing and would pass vacuously or fail. At implementation time run `git grep -n "retryCurrentSearch" -- tests` in the worktree. At 5dde407 (`C:/ssw/kb`) it finds no test (only `static/js/loading.js` and a history log): the test is PR #256's and has not landed there. The rule:
   - If the grep finds the test: make it read the expected field set from `scrobblescope.album_request.FORM_FIELDS` (import the constant; scan no route source), keep its assertion that every name in the set is among the inputs `retryCurrentSearch` posts, and add `assert "include_unmatched" in FORM_FIELDS and len(FORM_FIELDS) == 10` so a vacuous pass is impossible. Name the test in the commit body. Proof: in a scratch edit add `"source"` to `FORM_FIELDS`; the contract test fails because `loading.js` does not post it; restore with `git checkout -- <path>`.
   - If the grep finds nothing (PR #256 is not in the base): write no contract test here (it is #256's), tell the controller before landing so this task is rebased after #256 merges, and say in the Section 4 entry that `FORM_FIELDS` is the list that contract must read.

No other existing test changes. `test_results_loading_year_below_registration_year_rejected`, `..._at_registration_year_allowed`, `..._no_registered_year_proceeds`, the private/missing-user order tests, the capacity tests and the include-unmatched tests are untouched and must pass.

- [ ] **Step 5: Run to verify**

Run: `PY -m pytest -q -p no:cacheprovider`
Expected: all pass, including every Task 1 parity test unchanged, `tests/test_pipeline_integration.py` (with the edited mock) and, when present, the Retry contract test reading `FORM_FIELDS`.

- [ ] **Step 6: Mutation evidence**

| Planted defect | File | Test that must fail |
|---|---|---|
| remove the decade membership check | `scrobblescope/album_request.py` | `test_a_bad_filter_is_refused_on_the_form_and_starts_nothing[...decade...]` |
| treat `Verdict.UNAVAILABLE` like `PUBLIC` (delete its branch) | `scrobblescope/routes/album_flow.py` | `test_a_pre_check_outage_refuses_retryably_and_starts_nothing` (both rows) and the table's album outage rows |
| build the params from a literal dict without `mode` | `scrobblescope/routes/album_flow.py` | `test_an_album_job_record_says_it_is_an_album_job` |
| read `info["exists"]` outside the `try` in `check_lastfm_user` | `scrobblescope/routes/precheck.py` | `test_a_malformed_last_fm_answer_refuses_retryably_and_starts_nothing` (and Task 3's malformed table) |
| ask privacy first in `check_lastfm_user` | `scrobblescope/routes/precheck.py` | `test_every_route_reads_the_last_fm_answer_the_same_way[missing-*]` |
| drop `timeout=` from `_check_user_exists` | `scrobblescope/routes/__init__.py` | `test_a_stalled_last_fm_costs_a_route_its_budget_not_the_session` (all three rows) |

- [ ] **Step 7: Docs in the same commit**

`docs/architecture/runtime-system.md`: add the edge `    Routes --> AlbumRequest` after the `Routes --> Unmatched` edge (`routes/album_flow.py` now imports `album_request`); validate the diagram with the `validate_and_render_mermaid_diagram` MCP call.
SESSION_CONTEXT Section 4: change `routes/album_flow.py    <- admission, jobs, orchestrator, spotlight, unmatched; routes (facade)` to `<- admission, album_request, jobs, orchestrator, precheck, spotlight, unmatched; routes (facade)`. Section 5, request flow, insert directly after `  -> POST /results_loading (routes/album_flow.py)`:

```
    -> album_request.parse_album_request: form -> AlbumRequest or Refusal
       (a Refusal re-renders the form with that field's sentence, no lookup)
    -> precheck.check_lastfm_user: exists, then public, each lookup timed out;
       an outage refuses with 503 and starts nothing
    -> registration_refusal: the optional registration-year hint
```

`docs/architecture/top-albums-sequence.md` (edit these exact lines, keep the rest):

- `alt Missing field, non-numeric input, or year outside 2002 to this year` becomes `alt A field is missing, malformed, or outside what the form offers`, and the next line `Routes-->>Browser: index.html + error` becomes `Routes-->>Browser: index.html + error naming the field, no lookup made`.
- After the `else Recent listening is private (HTTP 403, error 17)` branch's response line, add:
  ```
          else Last.fm cannot answer, or not within the pre-check timeout
              Routes-->>Browser: index.html + "Validation service unavailable. Try again.", HTTP 503, no job created
  ```
- `else Registration year satisfied, unknown, or either lookup failed` becomes `else Registration year satisfied or unknown`, and the Note beneath it becomes `Note over Routes,LastFM: Only the registration-year comparison is optional, an unknown year is not compared. A failed lookup refuses and never proceeds`.
- The Note `include_unmatched is stored in params, and an include run is always stored as a play-count run` becomes `The AlbumRequest is stored as the job's params with mode album, and an include run is always stored as a play-count run`.
- The prose paragraph above the diagram: after "The concurrency slot is acquired before job creation." add "The form is parsed and the Last.fm pre-check answered before the slot is touched, so a refusal costs neither a slot nor a job."

Validate the edited block with the Mermaid MCP call; fix any `;` before committing.

- [ ] **Step 8: Section 4 entry, gates, commit**

Entry heading: `### YYYY-MM-DD - The album form is refused with a reason, never started doomed`. Body: user-visible changes, both recorded (a filter value the form never offers is refused on the form with the field's sentence, including a `custom` scope without a year and a `decade` scope without a decade, which used to widen to every year; a Last.fm outage or timeout during the pre-check is refused with a retryable 503 instead of starting a job); also stricter than before: the form's own ranges are now enforced on the server (`min_plays` 1-50, `min_tracks` 1-10, release year 1900 to this year, username up to 64 characters), and the username is trimmed; the server username bound is 64, the `/validate_user` limit (the form's input allows 100; a Last.fm name is far shorter); deviations (none); the existing tests edited, named; the Retry contract (`FORM_FIELDS`, see Step 4 item 4); mutation table; Validation `pytest -q` N.
Commit: `refactor(routes): Parse and pre-check album requests before any job`.
Commit body names `test_results_loading_registration_check_unavailable_proceeds` (replaced by `test_results_loading_lookup_unavailable_refuses_and_starts_nothing`), `test_results_loading_registration_check_failure_logs_no_message` (renamed and re-pointed) and `tests/test_pipeline_integration.py::test_album_pipeline_runs_on_a_real_thread_end_to_end` (its `check_user_exists` mock gains `"exists": True`: the old mock had no `exists` key and passed only because the route swallowed the `KeyError`; a malformed Last.fm answer is now an outage), plus the Retry contract test when present.

---

### Task 6: The heatmap and validate routes answer from the shared pre-check

**Touches:** `scrobblescope/routes/heatmap_flow.py`, `scrobblescope/routes/api.py`, `tests/test_precheck_routes.py`, `tests/services/test_failure_logging.py`, `.claude/SESSION_CONTEXT.md`, `docs/agents/PLAYBOOK.md`
**After:** Task 5 (the cross-route table in `tests/test_precheck_routes.py` is this task's parity test)

**Files:** as listed.

**Interfaces:**
- Consumes: `precheck.check_lastfm_user`, `precheck.Verdict`, `precheck.UNAVAILABLE_MESSAGE`, `precheck.not_found_message`.
- Produces: no behaviour change: the HTTP statuses and JSON bodies of `/heatmap_loading` and `/validate_user` are exactly what Task 1 and Task 5 pin.

Why: the last two copies of the pre-check go; each route keeps only its own response shapes. The one visible difference: the failure log lines no longer contain the Last.fm username (F-B23-40 names three lines; the heatmap route's two were a fourth and fifth).

- [ ] **Step 1: Confirm the parity tests pass before the change**

Run: `PY -m pytest tests/test_precheck_routes.py tests/test_request_flow_parity.py tests/test_routes.py -q -p no:cacheprovider -k "heatmap or validate or precheck or parity"`
Expected: all pass, except possibly the six heatmap and validate rows of the new malformed-answer test below (the album rows pass).

Then append this test to `tests/test_precheck_routes.py` (it uses that file's `ROUTES`, `_call` and `_outcome`). Written before the rewrite: the album row passes already (Task 5); the heatmap and validate rows are the new behaviour this task delivers, so they may fail or pass before Step 2, whatever the old routes did with a bad body, and must pass after it.

```python
@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize(
    "answer",
    [{"registered_year": 2016}, {"exists": "yes"}, None],
    ids=["no-exists-key", "exists-not-a-bool", "none"],
)
def test_a_malformed_last_fm_answer_is_unavailable_on_every_route(
    client, fresh_job_store, route, answer
):
    """
    GIVEN Last.fm answers the existence check with a body of the wrong shape
    WHEN the album form, the heatmap start or the blur check asks
    THEN each says "unavailable" (retryable) and starts nothing: a bad body is
    an outage, never a 500 and never a guess.

    Mutation: read `info["exists"]` outside precheck's try and every row 500s.
    """
    with (
        patch("scrobblescope.routes._check_user_exists", return_value=answer),
        patch("scrobblescope.routes._check_profile_is_public", return_value=True),
        patch("scrobblescope.routes.start_job_thread") as mock_start,
    ):
        response = _call(client, route)

    assert _outcome(route, response) == "unavailable"
    mock_start.assert_not_called()
    assert fresh_job_store.ids() == []
```

- [ ] **Step 2: Rewrite `_validate_heatmap_user`**

In `scrobblescope/routes/heatmap_flow.py` add `from scrobblescope.routes import admission, precheck` (extend the Task 4 import), remove `from scrobblescope.utils import log_failure` if nothing else in the file uses it (`PY -m ruff check scrobblescope/routes/heatmap_flow.py` says), and replace `_validate_heatmap_user` with:

```python
def _validate_heatmap_user(username):
    """Return a JSON validation error, or None for an existing public user.

    The answer is the shared pre-check's (``routes/precheck.py``); this maps
    it to the heatmap's JSON. A lookup or privacy outage is a retryable 503
    that reserves no worker slot and leaves this browser's saved heatmap job
    alone.
    """
    check = precheck.check_lastfm_user(username)

    if check.verdict is precheck.Verdict.PUBLIC:
        return None
    if check.verdict is precheck.Verdict.UNAVAILABLE:
        return (
            jsonify(
                {
                    "error": True,
                    "message": precheck.UNAVAILABLE_MESSAGE,
                    "retryable": True,
                }
            ),
            503,
        )
    if check.verdict is precheck.Verdict.MISSING:
        return (
            jsonify(
                {
                    "error": True,
                    "error_code": "user_not_found",
                    "message": precheck.not_found_message(username),
                    "retryable": False,
                }
            ),
            404,
        )
    return (
        jsonify(
            {
                "error": True,
                "error_code": "private_profile",
                "message": _routes._PRIVATE_PROFILE_MESSAGE,
                "retryable": False,
            }
        ),
        403,
    )
```

- [ ] **Step 3: Rewrite `validate_user`**

In `scrobblescope/routes/api.py` add `from scrobblescope.routes import precheck` (after the `_routes` import), remove the now-unused `log_failure` from `from scrobblescope.utils import create_optimized_session, log_failure`, and replace the body of `validate_user` after the two length checks with:

```python
    check = precheck.check_lastfm_user(username)
    if check.verdict is precheck.Verdict.UNAVAILABLE:
        return (
            jsonify({"valid": False, "message": precheck.UNAVAILABLE_MESSAGE}),
            503,
        )
    if check.verdict is precheck.Verdict.PRIVATE:
        return jsonify({"valid": False, "message": _routes._PRIVATE_PROFILE_MESSAGE})
    if check.verdict is precheck.Verdict.MISSING:
        return jsonify({"valid": False, "message": "Username not found on Last.fm."})

    payload = {"valid": True, "message": "Username found."}
    if check.registered_year:
        payload["registered_year"] = check.registered_year
    return jsonify(payload)
```

- [ ] **Step 4: Edit the one existing test whose log fragment moved**

`tests/services/test_failure_logging.py::test_validate_user_failure_logs_the_class_only_at_error`: change `error_fragment="Username validation failed"` to `error_fragment="User existence check failed"`. The heatmap tests' fragments ("User existence check failed", "Profile privacy check failed") are unchanged and still pass.

- [ ] **Step 5: Run to verify**

Run: `PY -m pytest -q -p no:cacheprovider` -- expected: all pass, Task 1 and Task 5 tests unchanged.
Run: `PY -m ruff check scrobblescope tests` -- expected: `All checks passed!`

- [ ] **Step 6: Mutation evidence**

The behaviour is pinned by Task 5's table; show it catches a regression in these routes:

| Planted defect | File | Test that must fail |
|---|---|---|
| map `Verdict.PRIVATE` to the 404 branch | `scrobblescope/routes/heatmap_flow.py` | `test_every_route_reads_the_last_fm_answer_the_same_way[private-heatmap]` |
| return 200 `valid: True` for `Verdict.UNAVAILABLE` | `scrobblescope/routes/api.py` | `test_every_route_reads_the_last_fm_answer_the_same_way[outage-*-validate]` |
| omit `registered_year` from the success payload | `scrobblescope/routes/api.py` | `test_validate_user_success` |
| read `info["exists"]` outside the `try` in `check_lastfm_user` | `scrobblescope/routes/precheck.py` | `test_a_malformed_last_fm_answer_is_unavailable_on_every_route` (all nine rows) |

- [ ] **Step 7: Docs in the same commit**

SESSION_CONTEXT Section 4: `routes/heatmap_flow.py  <- admission, heatmap, jobs, precheck; routes (facade)` (its last `log_failure` use is gone, so `utils` leaves the line), `routes/api.py           <- domain, jobs, precheck, release_checks, spotify, utils; routes (facade)`. SESSION_CONTEXT Section 3: change the `api.py` line's `validate_user,` entry to `validate_user (via precheck),`. No diagram changes: the heatmap sequence already shows the same three branches.

- [ ] **Step 8: Section 4 entry, gates, commit**

Entry heading: `### YYYY-MM-DD - The heatmap and the blur check use the shared pre-check`. Body: no visible behaviour change (statuses and bodies pinned by the cross-route table); the Last.fm username leaves two more log lines (note for the lastfm-scrobbles PR: they need not be counted under F-B23-40); the existing test edited, named; Validation `pytest -q` N.
Commit: `refactor(routes): Answer heatmap and validate from one pre-check`.

---

### Task 7: Job kind is a record field; WP-4 amended

**Touches:** `scrobblescope/routes/__init__.py`, `scrobblescope/routes/album_flow.py`, `scrobblescope/routes/api.py`, `tests/helpers.py`, `tests/test_routes.py`, `scripts/dev/_frontend_gate_results.py`, `scripts/dev/_frontend_gate_include.py`, `scripts/dev/_frontend_gate_spotify_icon.py`, `BATCH23_DEFINITION.md`, `.claude/SESSION_CONTEXT.md`, `docs/agents/PLAYBOOK.md` (Section 3 and Section 4)
**After:** Task 6

**Files:** as listed (plus any other seed the grep in Step 2 finds).

**Interfaces:**
- Consumes: `jobs.MODE_ALBUM`, `jobs.MODE_HEATMAP`; every job created by Tasks 4-6 already carries `mode`.
- Produces: a job record with no `mode` is neither an album job nor a heatmap job: the album pages and `/api/release_checks` answer 404 for it. No code reads `params.get("mode", "album")` any more.

Why: B-12's server half. A default of "album" means a record that forgot its kind is silently served as an album run. Now that every writer sets the kind, the default is a trap, not a convenience.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_routes.py`:

```python
@pytest.mark.parametrize(
    "path", ["/results", "/loading", "/unmatched", "/api/release_checks"]
)
def test_a_job_that_never_said_its_kind_is_not_served_as_an_album_job(client, path):
    """
    GIVEN a job record with no `mode`
    WHEN an album page or the release-check API is asked for it
    THEN the answer is 404 (it is not assumed to be an album run).

    Mutation: restore `.get("mode", "album")` in routes._get_validated_job_context
    or api.release_checks and the matching rows return 200.
    """
    job_id = jobs.create({"username": "someone", "year": 2025, "sort_mode": "playcount"})

    response = client.get(f"{path}?job_id={job_id}")

    assert response.status_code == 404
```

- [ ] **Step 2: Run to verify it fails**

Run: `PY -m pytest tests/test_routes.py -q -p no:cacheprovider -k never_said_its_kind`
Expected: FAIL (the pages answer 200 or render with the defaults).

- [ ] **Step 3: Make every album-job fixture say what it is**

`tests/helpers.py`: add `"mode": "album",` as the last entry of `TEST_JOB_PARAMS`. `tests/test_routes.py`: add `"mode": "album",` as the last entry of the three literal `jobs.create({...})` album dicts (`test_results_complete_renders_no_matches_for_empty_results` and the two results-page tests after it; each literal starts `"username": "flounder14", "year": 2025`). Step 5's suite run finds any other fixture that needs it.

Find every other seed: run `grep -rn "jobs.create(" scripts tests | grep -v "TEST_JOB_PARAMS\|HEATMAP_JOB_PARAMS\|\"mode\"\|heatmap"` and `grep -n "create(" scripts/dev/_frontend_gate_*.py`. Known sites needing `"mode": "album"` (six): `scripts/dev/_frontend_gate_results.py` (three `jobs.create({"username": "gate", "year": 2025, "sort_mode": "playcount"})` calls), `scripts/dev/_frontend_gate_include.py` (the `jobs.create({... "include_unmatched": True})` call) and `scripts/dev/_frontend_gate_spotify_icon.py` (two of the same `jobs.create({"username": "gate", ...})` calls, one in each of its two checks). Use `jobs.MODE_ALBUM` there (`from scrobblescope import jobs` is already imported). `scripts/dev/_frontend_gate_pipeline.py` and `_frontend_gate_heatmap_access.py` already set `mode`.

- [ ] **Step 4: Delete the defaults**

`scrobblescope/routes/__init__.py`, `_get_validated_job_context`: replace `actual_mode = job_context.get("params", {}).get("mode", "album")` with `actual_mode = job_context.get("params", {}).get("mode")`; in `_latest_heatmap_job` replace `.get("mode") != "heatmap"` with `.get("mode") != jobs.MODE_HEATMAP`.

`scrobblescope/routes/api.py`, `release_checks`: replace `if job_context.get("params", {}).get("mode", "album") != "album":` with `if job_context.get("params", {}).get("mode") != jobs.MODE_ALBUM:`.

`scrobblescope/routes/album_flow.py`: the three `expected_mode="album"` become `expected_mode=jobs.MODE_ALBUM`; delete the `"mode": params.get("mode", "album"),` entry of `_extract_job_params` (nothing reads `p["mode"]`; `grep -rn '\["mode"\]' scrobblescope templates` confirms).

- [ ] **Step 5: Run to verify**

Run: `PY -m pytest -q -p no:cacheprovider`
Expected: all pass. If a test fails with a 404 where it expected a page, its fixture lacks `mode`: add `"mode": "album"` to that fixture (and list it in the commit body).

- [ ] **Step 6: Mutation evidence**

| Planted defect | File | Test that must fail |
|---|---|---|
| restore `.get("mode", "album")` | `scrobblescope/routes/__init__.py` | `test_a_job_that_never_said_its_kind_is_not_served_as_an_album_job[/results|/loading|/unmatched]` |
| restore the same default | `scrobblescope/routes/api.py` | `...[/api/release_checks]` |

- [ ] **Step 7: Frontend gate (owner's machine, one at a time)**

Run: `PY scripts/dev/frontend_gate.py`
Expected: last line `[frontend_gate] N checks passed ...` and no failures. The seeds changed here (results x3, include x1, spotify_icon x2) are exercised by it.

- [ ] **Step 8: Amend `BATCH23_DEFINITION.md` WP-4**

In `BATCH23_DEFINITION.md`, directly after the paragraph that begins `**Scope amended 2026-10-20** (owner directive to keep planned scope current)` and ends `No work package is added.`, add:

```
**Scope amended 2026-10-20** (pre-Batch-23 tranche, PR #3): the album request
module, the Last.fm pre-check and the admission module now exist, so WP-4
reuses them instead of writing them. No work package is added.
```

In WP-4, replace

```
- [ ] `POST /spotify_export_loading` takes the file and mode plus the
  existing album fields through the existing validators, runs `open_export`
```

with

```
- [ ] `POST /spotify_export_loading` takes the file and mode plus the
  existing album fields through `album_request.parse_album_request(form,
  current_year=..., require_username=False)` (an `AlbumRequest` with
  `username=None`, or a `Refusal` naming the field), runs `open_export`
```

and after the admission bullet that ends `what makes the extraction worth doing here (owner ruling, 2026-09-21).` add the continuation (same bullet, new lines):

```
  The module exists: `scrobblescope/routes/admission.py`, `admit(params,
  target, *, label)`, written by the album-request-module PR, which also
  tests, through the admission path the album and heatmap routes share, that
  a failed thread start leaves no slot held and no orphan job. WP-4 adds the
  export route as the third caller and `EXPORT_MAX_IN_FLIGHT` inside it. A
  thread entry point takes only the job id and reads its parameters from the
  job record (`jobs.params`); the export thread follows that shape. The job
  kind is `params["mode"]`, written at creation and never defaulted when
  read (`jobs.MODE_ALBUM`, `jobs.MODE_HEATMAP`). An export album job keeps
  `mode` "album", because every album page answers 404 for any other kind,
  and records where its data came from in the separate `source` field
  (`_extract_job_params` gains `source`, as this work package already says).
```

In the WP-4 Acceptance paragraph, change `For admission: a failed thread start leaves no slot held and no orphaned job, tested for each of the three routes.` to `For admission: a failed thread start leaves no slot held and no orphaned job, tested for each of the three routes (PR #3 tests the path the album and heatmap routes share; WP-4 adds the export route's).` (the sentence wraps across lines in the file; keep the wrap style).

- [ ] **Step 9: Remaining docs**

`docs/agents/PLAYBOOK.md` Section 3 (the spec: "Section 3 is updated as each PR lands, so it always names the work still ahead of WP-1"). In the "Before WP-1" bullet, after the sentence ending `normalized Last.fm scrobbles with one album aggregate.` add the sentence `The album request module is done (PR #3, branch refactor/album-request-module); the other three seams remain.` (keep the file's line wrap, and leave the "What PR #245 ships" and "Architecture seams" bullets as they are: they record the 2026-09-29 owner rulings, which stay true as history). Do not change the `Branch:` line or any "Last verified" date. This edit is named in the Section 4 entry below.

SESSION_CONTEXT Section 3: no new module; change the `routes/__init__.py` line only if its description mentions job modes (it does not). Section 5: no change. Confirm with `git grep -n 'get("mode", "album")'` -- expected no output.

- [ ] **Step 10: Section 4 entry, gates, commit**

Entry heading: `### YYYY-MM-DD - A job says what kind it is`. Body: B-12's server half; the defaults gone from three sites; fixtures and the frontend-gate seeds updated (listed); the WP-4 amendment (quote it); the PLAYBOOK Section 3 sentence naming the album request module done; frontend gate result; the existing tests/fixtures edited, named; Validation `pytest -q` N.
Commit: `refactor(jobs): Make job kind a record field and amend WP-4`.

---

## Self-Review

**1. Spec and master "Must cover" coverage**
- A form becomes a validated album request or a typed refusal for `sort_mode`, `release_scope`, `decade`, `limit_results`, `include_unmatched`: Task 2 (module), Task 5 (route).
- One Last.fm pre-check answer shared by album and heatmap routes (and validate): Task 3 (answer), Task 5 (album), Task 6 (heatmap, validate).
- Short timeout of its own (owner Q4): Task 3 (`LASTFM_PRECHECK_TIMEOUT_SECONDS`, `run_async_in_thread(timeout=)`); end-to-end in Task 5's `test_a_stalled_last_fm_costs_a_route_its_budget_not_the_session`.
- Outage refuses retryably and never starts a job: Task 5 (`test_a_pre_check_outage_refuses_retryably_and_starts_nothing`).
- One admission path; the thread reads parameters from the job record: Task 4.
- Parity tests for today's route behaviour first: Task 1, plus the cross-route table written before Task 6.
- `BATCH23_DEFINITION.md` WP-4 amendment naming the module the export route reuses: Task 7, Step 8, exact text.
- Docs follow code: SESSION_CONTEXT Sections 3-4 in Tasks 2, 3, 4, 5, 6; `docs/architecture/runtime-system.md` node and edges in Tasks 2, 4 and 5 and the `jobs.params` read in Task 4; sequence diagrams in Tasks 4 and 5; PLAYBOOK Section 3 in Task 7; each task its own atomic commit and Section 4 entry.
- Hosting ceiling: no database call, no machine, no service added.
- Out of this PR (not in "Must cover"): the Retry button dropping `include_unmatched` (PR #256; Task 5 keeps its contract test reading `FORM_FIELDS`); `_extract_job_params`' page-side defaults (WP-4 reworks that function to add `source`); the client half of B-12.

**2. Placeholder scan.** Dates in the Section 4 headings are "today's date" by instruction; the only `YYYY-MM-DD` tokens are those headings. No TBD/TODO. Every code step shows code; every run step names a command and expected result.

**3. Type and name consistency.** `AlbumRequest` fields and `to_params()` keys match `jobs.context(...)["params"]` keys used by `_extract_job_params` (`sort_mode`, `release_scope`, `decade`, `release_year`, `min_plays`, `min_tracks`, `limit_results`, `include_unmatched`). `admission.admit(params, target, *, label)` is called identically in Tasks 4, 5 and for the heatmap. `Verdict`/`UserCheck`/`UNAVAILABLE_MESSAGE`/`not_found_message` are used with the Task 3 names in Tasks 5 and 6. `jobs.params` (Task 4) is the reader used by both thread entry points. `jobs.MODE_ALBUM`/`MODE_HEATMAP` (Task 2) are used in Tasks 4 and 7.

## Decisions made in this plan

Each of the five questions an earlier draft asked turned out not to be the owner's: an existing brief, ruling or definition settles it. Recorded here with its source so the owner sees the choice in the PR, not as a stalled gate.

1. **Pre-check timeout: 5 seconds per lookup**, overridable by `LASTFM_PRECHECK_TIMEOUT_SECONDS`. Source: the owner ruled the principle (a short timeout of its own, 2026-10-20); the number is an engineering default. Last.fm's usual answer is well under a second, and a shared budget would change the facade's two function signatures and many existing patches.
2. **Album-form refusals keep HTTP 200; only a Last.fm outage is 503.** Source: the Task 26 brief fixes the outage as "the same message and status family the heatmap route uses today" (503); every other refusal keeps today's behaviour under the refactor rule (statuses are a separate, visible change).
3. **The server enforces what the form enforces**: `min_plays` 1-50, `min_tracks` 1-10, release year 1900 to this year, a decade from the form's eight, a `custom` scope needs a year and a `decade` scope needs a decade, username up to 64 characters (the limit `/validate_user` already enforces; the form's input allows 100, a Last.fm name is far shorter). Source: the Task 26 brief (validate year, release year, min plays, min tracks and the four unvalidated fields) and the master plan's "no doomed submission". Recorded as a user-visible change in Task 5's Section 4 entry.
4. **The Retry button dropping "All albums"** is not decided here: PR #256 (fix F3) fixes it and adds the contract test; this plan only keeps that test covering the moved fields (Task 5, Step 4 item 4).
5. **Export reuse shape**: `parse_album_request(..., require_username=False)` returns an `AlbumRequest` with `username=None`. Source: `BATCH23_DEFINITION.md` WP-4 already says "never put a placeholder in `username`, because error messages format it"; the amendment text (Task 7, Step 8) shows the owner the shape in the PR.

## Owner questions

None.

## Revision 1 (2026-10-20)

Maps each review finding (plan-review.md, verdict Needs fixes: 7 Important, 7 Minor) to its change.

| Finding | Change |
|---|---|
| I1 pipeline-integration mock; malformed answer outside the try | Task 5 Step 4 item 3 names `tests/test_pipeline_integration.py::test_album_pipeline_runs_on_a_real_thread_end_to_end`, gives the new mock (`{"exists": True, "registered_year": 2000}`) and the reason, adds the file to Touches and the commit body, and limits "No other existing test changes" to tests beyond those listed. Task 3's `check_lastfm_user` now reads the answer through `_read_existence` inside its `try`: a non-mapping, a missing or non-bool `exists`, or a non-int `registered_year` is `UNAVAILABLE`. Tests: Task 3 `test_a_malformed_existence_answer_is_unavailable_never_an_error`, Task 5 `test_a_malformed_last_fm_answer_refuses_retryably_and_starts_nothing`, Task 6 `test_a_malformed_last_fm_answer_is_unavailable_on_every_route`, each with a planted defect. |
| I2 sixth `background_task(` call site | Task 4 Step 2 lists all six `background_task(` sites and all seven `heatmap_task(` sites (git grep at 5dde407), gives the edit for the multi-line one in `test_background_task_stores_unmatched_rows_when_the_flag_is_on`, and names every edited test in the Section 4 entry. |
| I3 slot-release claim | Task 4 adds `test_a_real_thread_start_failure_frees_the_slot_once_and_removes_the_job` (real `worker.start_job_thread`, a Thread that cannot start, a counting semaphore double; planted defect: a second release in `admit`). The WP-4 amendment now claims only the shared admission path. |
| I4 runtime-system.md | Task 2 adds the `AlbumRequest` node and its `jobs` edge; Task 4 the `Album -->` edge and `params` in the jobs reads list; Task 5 the `Routes -->` edge; each validated with the Mermaid call. |
| I5 PLAYBOOK Section 3 | Task 7 Step 9 adds the sentence naming the album request module done, in the Task 7 Section 4 entry. |
| I6 Retry contract | Assumptions row replaced by a pointer to PR #256; Owner question 4 removed. Task 2 adds `FORM_FIELDS` and a spy test that it equals the fields the parser reads; Task 5 Step 4 item 4 gives the rule for the contract test (grep `retryCurrentSearch` in `tests/` at implementation time; none exists at 5dde407; repoint it to `FORM_FIELDS`, or report and rebase after #256). |
| I7 Touches/After | Task 4 is After Task 3; the ordering paragraph says Tasks 1-3 all touch PLAYBOOK (and 2-3 SESSION_CONTEXT) so landings are serial though code phases may overlap; `tests/test_utils.py` overlap with PR #4 (23a) is stated in Task 3. |
| M1 username bound | Stated as `/validate_user`'s 64 (form `maxlength` is 100) in the module, Task 2's Section 4 entry, Task 5's entry and Decision 3. |
| M2 unusable-record branch | Task 4 adds `test_background_task_for_an_unusable_record_fails_the_job_and_frees_its_slot` with a planted defect. |
| M3 six seeds | Task 7 lists all six (results x3, include x1, spotify_icon x2) and adds `_frontend_gate_spotify_icon.py` to Touches. |
| M4 amendment wording | The amendment says an export album job keeps `mode` "album" and carries `source` separately. |
| M5 Task 1 overlap | Task 1 states the overlap and that the rows are kept for their delta (no lookup, no job, boundaries). |
| M6 scopes vs `release_window` | Task 2 adds `test_every_scope_the_server_accepts_has_a_release_window_rule`. |
| M7 gotchas line | Task 3 Step 6 adds the `LASTFM_PRECHECK_TIMEOUT_SECONDS` bullet to SESSION_CONTEXT Key runtime facts. |
| Controller rulings 6 and 7 | Done as above; none of Q1-Q5 is the owner's, each is decided with its source under "Decisions made in this plan", and "Owner questions" says None. |
