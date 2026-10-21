# Album metadata encoding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give an album's metadata one encoding from the provider, through the shared cache, to the Results page, and give the cache module its own operation: it opens, uses and closes its database connection and decides what a database error means, so `orchestrator.process_albums` manages no connection.

**Architecture:** Four code tasks and one controller task on `refactor/metadata-encoding`, each code task its own atomic commit. Task 1 pins today's storage, read-back and failure behaviour through an in-memory PostgreSQL and the real cache module, so the same tests run unchanged before and after. Task 2 teaches `enrichment.AlbumMetadata` to read itself from a cache row (additive). Task 3 makes the cache take and return `AlbumMetadata`, deletes `as_cache_row`, the six-tuple branch, the 4-key and 7-key `cached` dicts, `_album_provider` and `_album_url`. Task 4 adds `AlbumCache` / `open_album_cache` so the cache owns connection lifetime and failure policy, and amends `BATCH23_DEFINITION.md` WP-3. The sources are review card B-5 (`docs/history/reports/architecture-review-20260930-0040.html`), the Task 27 brief and `FINDINGS.md` F-B23-3 (all checked against `C:/ssw/kb`, see "Assumptions checked"); the tranche order is `docs/superpowers/plans/2026-10-20-pre-batch23-tranche.md` (PR #5).

**This plan is written for `main` after PR #4 (Last.fm scrobbles) has merged**, and so after PR #3 (album request module). It uses the public cache names PR #4's Task 3 introduces (`get_db_connection`, `batch_lookup_metadata`, `batch_persist_metadata`, `batch_lookup_original_release`, `batch_persist_original_release`, `cleanup_stale_metadata`, `domain.matches_release_criteria`) and its `tests/test_module_boundaries.py`. Nothing in #3 or #4 changes `process_albums`' signature, the phase modules under `orchestrator/` or the shape of a result row; "Dependence on PRs #3, #4 and #6" lists what was read.

**Tech Stack:** Python 3.13, asyncio/asyncpg (optional import), Flask, pytest with pytest-asyncio, ruff, pre-commit, docsync (`scripts/doc_state_sync.py`), Mermaid diagrams under `docs/architecture/`.

## Global Constraints

- Every commit is atomic and carries its own untagged PLAYBOOK Section 4 entry, placed directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` line (AGENTS.md "Side-Task Handling"). The entry heading is `### <ISO date of the commit> - <title given in the task>`; the body gives the scope, why, what changed, deviations, the mutation evidence and the line ``Validation: `pytest -q` -- **N passed**.`` with the measured N.
- Commit procedure, every commit, in this order (AGENTS.md "Commit Rules"): write the Section 4 entry; `pytest -q` and measure N; `doc_state_sync.py --fix --test-count N` (bare `--fix` when N is unchanged); stage by name, never `git add -A` or `git add .`; `pre-commit run --all-files` and re-stage anything a hook rewrote; `doc_state_sync.py --check` exits 0; commit.
- Commit subject `<type>(<scope>): <Capitalised imperative>`, at most 72 characters (each task gives its subject, measured); body explains why and names every existing test file or test it edited (owner ruling 2026-09-29, recorded in `BATCH23_DEFINITION.md`: a seam refactor commit may edit existing tests). No `Co-authored-by` trailer.
- From the linked worktree `C:/ssw/me`, every Python command uses the primary checkout's interpreter. In every command below, `PY`, `RUFF` and `PRECOMMIT` are shell variables; set them once per shell:
  `PY="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe"`, `RUFF="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/ruff.exe"`, `PRECOMMIT="C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pre-commit.exe"`. Always quote them: `"$PY" -m pytest ...`.
- Markdown is ASCII only (`--`, never an em dash). Cite code by name, not line number.
- New tests assert intended behaviour, not the code as written (owner, 2026-10-20), and each comes with mutation evidence: the planted defect named and the test shown failing, then restored and shown passing. Plant each mutation in a scratch copy of the tree (a private directory named for this PR and task, removed afterwards), or copy the file aside before planting and copy it back after. Never restore with `git checkout -- <file>` or `git restore`: a file under edit holds the task's uncommitted work (`constraints.md` R9).
- A refactor starts from parity tests in a preceding commit (AGENTS.md "Refactor requires parity tests"): Task 1 precedes Tasks 3 and 4. A parity test must pass on the unchanged tree; if one fails there, the test is wrong, never the code.
- Use the Python 3.13 spellings the hygiene PR (#2) establishes: `from datetime import UTC`, never `timezone.utc`, in every line this plan adds.
- Docstrings: every new function has a docstring; comments say why (AGENTS.md "Docstrings and comments"). Log lines name a job id, an exception class, counts and elapsed time. They never carry a Last.fm username, an artist, album or track name (`BATCH23_DEFINITION.md` "Data handling").
- **Hosting cost ceiling (spec):** nothing here keeps the production database awake, adds a machine or adds a service. This PR adds no database traffic: a job opens one connection, issues the same statements in the same order, and closes it, exactly as before. Task 1 pins the statement sequence and the connection count; Tasks 3 and 4 re-run those tests unchanged. No task adds a query, a reconnect, a retry or a second connection.
- **The cache stays optional at runtime (spec):** a missing or sleeping database degrades to provider calls and never fails a job. Task 1 pins that behaviour (no `DATABASE_URL`, a connection that never answers, a failing read, a failing write, a failing correction read) with planted defects; Task 4 extends it to a failing `close()`, which today raises out of `process_albums`.
- Seams spec rule: "When a seam changes what a Batch 23 work package may assume, the same PR amends `BATCH23_DEFINITION.md`: ... #5 for WP-3's metadata shape". Task 4 does it (exact text there). WP-6 is untouched here; PR #6 amends it.
- Metadata and release-check cache policy stay separate (`FINDINGS.md` F-B23-3). `release_checks.py` keeps its own connection, its own failure messages and the public connection-level names; this PR does not edit it.
- This PR changes no template, stylesheet or script, and no schema (`init_db.py` is not touched).
- `WT003 refactor/metadata-encoding` and `WT010` are expected advisories from the `worktree-alignment` hook; the hook still passes.
- Do not push. The controller pushes after Task 4 is accepted and opens the PR (Task 5).
- Branch and merge order (tranche master plan): this plan is committed first on the branch, before Task 1. The branch starts from `main` after PR #4 merges. PR #6 runs in parallel; see "Dependence on PRs #3, #4 and #6" for the shared files.

---

## Assumptions checked against `C:/ssw/kb` (5dde407, re-checked at eb0db9e)

The Task 27 brief and card B-5 predate PR #245; the code was read at 5dde407 and re-checked at eb0db9e, after PRs #3 and #4 merged (drift review, 2026-10-21). The names those PRs introduced are public at eb0db9e; Task 1 Step 1 confirms them again at the start of the work.

| Assumption | Held? | What `C:/ssw/kb` shows | Effect on this plan |
|---|---|---|---|
| B-5: three encodings and two hand-built translators | Held | `AlbumMetadata.as_cache_row` builds a nine-tuple; `cache.batch_lookup_metadata` returns a 7-key dict; `_details.py` builds a 4-key `cached` dict (`spotify_id`, `release_date`, `album_image_url`, `track_durations`); `_deezer_fallback.py` builds a 7-key one; `cache.batch_persist_metadata` unpacks positions with `len(r) > 6`, `> 7`, `> 8` branches | Task 3 replaces all of them with `AlbumMetadata` |
| `_album_provider` and `_album_url` exist only to rebuild what the Spotify inline dict never carried | Held, with a second reason | They also rebuild legacy rows: a row with no `provider` column value is a Spotify row (`provider` falls back to `"spotify"`), and one with no `provider_url` gets the classic Spotify link. The same rule must move into `AlbumMetadata.from_row`, not vanish | Task 2 writes the rule once, with tests; Task 1's parity tests pin it first |
| The six-tuple branch is reached only by tests | Held | Two tests pass six-element rows: `test_batch_persist_metadata_defaults_provider_for_legacy_six_tuple` in `tests/services/test_cache.py` (which exists to pin the branch) and `test_batch_persist_metadata_upsert_call_shape` in `tests/test_repositories.py`; `as_cache_row` always yields nine elements | Task 3 deletes the first and says so, and rewrites the second's rows to `AlbumMetadata`; the legacy-row rule the first stood for is covered by Task 1's legacy-row parity test and Task 2's `from_row` tests |
| Callers manage the connection | Held | `process_albums` calls `get_db_connection()` (renamed from `_get_db_connection` by #4), holds it across Spotify and Deezer, and closes it in a `finally` that does not guard `close()`; `orchestrator/_cache.py` owns lookup and persist failure policy; `release_checks.run_release_checks` has its own open, use and guarded close | Task 4 moves the first two behind `open_album_cache`; the third stays (F-B23-3) |
| Failure policy is in three places | Held | connect (`cache.get_db_connection`: asyncpg missing, no `DATABASE_URL`, retries with backoff, `db-down`), read and write (`orchestrator/_cache.py`, with a schema-out-of-date message), and the correction worker (own) | Task 4 gathers the first two in `AlbumCache`; every existing log line is kept word for word |
| The brief: "Touches ... `init_db.py` only if the schema is restated" | Not needed | The schema is unchanged; the SQL statements are unchanged | `init_db.py` is not in any Touches |
| The brief: "After: 20 (Postgres job adapter) and 23 (orchestrator seams)" | 20 no longer applies | Job persistence is out of scope for the tranche (spec: it would keep the database awake); 23 is PR #4 | This plan builds on #4 only |
| The brief: results read attributes | Held | `_build_results` reads `cached.get(...)` in two row builders (the exclusion entry and the result row) | Task 3 changes both to attribute reads |
| New: the live Spotify path and the cache-hit path differ in the link | Found | The live `cached` dict has no `provider_url`, so `_album_url` rebuilds `https://open.spotify.com/album/<id>`; a cache hit shows the stored `provider_url`, which `album_metadata_from_details` set from `external_urls.spotify` | Identical when Spotify returns its canonical link (it does; the test fixtures name none, so they fall back to the same string). Task 1 pins live-equals-cached; Task 3 uses the stored link on both paths. Recorded in Decisions |
| New: a cache row with a NULL `release_date` would crash the exclusion reason | Found, unreachable from our writes | `_get_user_friendly_reason` does `"-" in release_date`, and `release_date` is a nullable column; every write passes a string (`details.get("release_date", "")`) | `from_row` reads NULL as `""` (Task 2 test) |
| `release_checks` uses the connection-level cache functions | Held | It imports `get_db_connection` (after #4), `batch_lookup_original_release`, `batch_persist_original_release`, `schema_is_out_of_date`, `SCHEMA_OUT_OF_DATE_REMEDIATION` | Left alone; those names stay public. The three metadata functions (`batch_lookup_metadata`, `batch_persist_metadata`, `cleanup_stale_metadata`) get a single caller, `AlbumCache`, and a guard test (Task 4) |
| Existing process_albums tests patch the connection and the SQL wrappers at `scrobblescope.orchestrator.<name>` | Held | 46 patch lines in `tests/services/test_orchestrator_process_albums.py`, two in `test_orchestrator_helpers.py`, two in `test_orchestrator_fetch_spotify.py`, three in `test_pipeline_integration.py` | Task 4 re-points them with a byte-safe script to `scrobblescope.cache.<name>`: they keep proving behaviour through the change |
| PR #4 renames the cache names and edits `orchestrator/__init__.py`, `_cache.py`, `_results.py` (imports only) | Held at eb0db9e | `get_db_connection`, `batch_lookup_metadata`, `batch_persist_metadata`, `batch_lookup_original_release`, `batch_persist_original_release`, `cleanup_stale_metadata`; `domain.matches_release_criteria`; `tests/test_module_boundaries.py` (all present at eb0db9e) | Task 1 Step 1 re-checks them; every command below uses the public names |
| `process_albums(job_id, filtered_albums, year, sort_mode, release_scope, decade=None, release_year=None)` is unchanged by #3 and #4 | Held at eb0db9e | #4's Task 5 changed `_fetch_and_process` and added `finish_album_job`, which calls `_process_filtered_albums` unchanged | Task 1 Step 1 re-checks the signature |
| The master plan says #5 and #6 both edit `orchestrator/_results.py` | Did NOT hold for #6 | #6's draft lists no `_results.py` edit: its `listening_stats.py` reads result rows by `play_count` and `unmatched_reason` | See "Dependence on PRs #3, #4 and #6" |

## Dependence on PRs #3, #4 and #6

**On #3 (album request module).** #3 and this plan both touch `orchestrator/__init__.py` (#3: `background_task` and the thread entry points; this plan: `process_albums`, `_fetch_spotify_misses`, the import block), `tests/test_pipeline_integration.py` (#3: the route-driven setup; this plan: three patch strings), `tests/services/test_failure_logging.py` (#3: route sites; this plan: database sites), and the two architecture documents (#3: the admission and route steps; this plan: the cache steps). Different functions, sites and lines, and #3 merges first, so the overlap is a textual rebase at worst. `process_albums` takes no request object and is not changed by #3.

**On #4 (Last.fm scrobbles).** The names listed above; `tests/test_module_boundaries.py` (Task 4 adds one test to it); `finish_album_job`, which reaches the cache only through `_process_filtered_albums` and `process_albums`. #4's Task 5 says it leaves `_process_filtered_albums` and `_build_results` unchanged. If at execution `process_albums`' signature or the phase module names differ from this plan, stop and return to the controller.

**On #6 (statistics module), and the `_results.py` ordering question.** The master plan expects both PRs to edit `orchestrator/_results.py`. #6's approved draft does not: it adds `scrobblescope/listening_stats.py`, which reads each result row's `play_count` and `unmatched_reason`, and it edits `heatmap.py`, `routes/album_flow.py`, `templates/results.html`, JavaScript and gate files. This plan's `_results.py` edit is confined to deleting `_album_provider` and `_album_url` and reading `entry["cached"]` as an `AlbumMetadata` in `_build_results`; **no result row key, value or type changes** (Task 1 pins the key set; Task 3 re-runs it). So the two PRs' `_results.py` edits do not meet, and either may land first. The rule if #6's final form does edit `_results.py` (say, WP-6 per-album fields on the row): #5 lands first because it is the smaller, mechanical change; #6 rebuilds on it by reading `entry["cached"]` as an `AlbumMetadata` (attributes `release_date`, `track_durations`, ...) and by not reintroducing `_album_provider` / `_album_url`. Files both PRs may touch: `.claude/SESSION_CONTEXT.md`, `docs/agents/PLAYBOOK.md`, `docs/architecture/runtime-system.md` (textual only: keep both sides), `BATCH23_DEFINITION.md` (different work packages: #5 WP-3, #6 WP-6). This plan adds test helpers in new files (`tests/fake_postgres.py`, `tests/album_metadata.py`) and not in `tests/helpers.py`, which #6 edits.

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `tests/fake_postgres.py` (create) | `FakePostgres`: an in-memory stand-in for the two cache tables, answering exactly the statements `cache.py` sends and refusing any other; `fake_postgres()` patches `asyncpg` and `DATABASE_URL` in `scrobblescope.cache` | 1 |
| `tests/test_album_cache_parity.py` (create) | Storage, read-back, results rows, failure policy and statement traffic, through `process_albums` and the correction worker, naming no `cache.py` function | 1 |
| `tests/album_metadata.py` (create) | `spotify_metadata()` and `deezer_metadata()` builders for tests | 3 |
| `scrobblescope/enrichment.py` (modify) | `AlbumMetadata.spotify_id`, `AlbumMetadata.from_row`, `SPOTIFY_ALBUM_URL`; loses `as_cache_row` | 2, 3 |
| `scrobblescope/spotify.py` (modify) | One line: `album_metadata_from_details` uses `SPOTIFY_ALBUM_URL` | 2 |
| `scrobblescope/cache.py` (modify) | Metadata functions take and return `AlbumMetadata`; later `AlbumCache`, `open_album_cache`, imports `enrichment` | 3, 4 |
| `scrobblescope/orchestrator/_details.py`, `_deezer_fallback.py`, `_results.py`, `__init__.py`, `_cache.py` (modify) | Hits carry `AlbumMetadata`; phases return `{key: AlbumMetadata}`; results read attributes; `process_albums` uses `open_album_cache` | 3, 4 |
| `tests/test_module_boundaries.py` (modify, one test) | Only `cache.py` touches the metadata functions and writes the metadata table | 4 |
| `docs/architecture/runtime-system.md`, `top-albums-sequence.md`, `.claude/SESSION_CONTEXT.md`, `BATCH23_DEFINITION.md`, `docs/agents/FINDINGS.md`, `docs/agents/PLAYBOOK.md` | Follow the code in the same commit | 3, 4 |

---

### Task 1: Pin album metadata storage, read-back and cache failure behaviour

**Touches:** `tests/fake_postgres.py` (new), `tests/test_album_cache_parity.py` (new), `.claude/SESSION_CONTEXT.md` (Tests row, module count), `docs/agents/FINDINGS.md` (header line, module count), `docs/agents/PLAYBOOK.md`.
**After:** nothing (first task; PR #4 merged).

**Files:**
- Create: `tests/fake_postgres.py`, `tests/test_album_cache_parity.py`
- Modify: `docs/agents/PLAYBOOK.md` (Section 4 entry), `.claude/SESSION_CONTEXT.md` and `docs/agents/FINDINGS.md` (the tracked test-module count, see Step 6)

**Interfaces:**
- Consumes: `scrobblescope.cache` (`asyncpg`, `_DATABASE_URL` module names; `get_db_connection` calls `asyncpg.connect(dsn, timeout=...)`), `orchestrator.process_albums`, `release_checks.run_release_checks`, `tests.helpers.TEST_JOB_PARAMS`.
- Produces: `tests.fake_postgres.FakePostgres` (`metadata`, `original_releases`, `statements`, `connect_attempts`, `closes`, `seed_metadata(artist_norm, album_norm, **columns)`, `seed_original_release(...)`, `fail(verb, table, error)`), `tests.fake_postgres.fake_postgres(db=None, *, connect_error=None, url=...)` (a context manager yielding the `FakePostgres`), `tests.fake_postgres.METADATA_FIELDS`. Tasks 3 and 4 reuse them.

Why: AGENTS.md "Refactor requires parity tests". Every existing test of this area patches `cache.py`'s own functions, so none of them can say whether the rows written, the rows read back and the Results JSON survive a change of encoding. These tests drive the real cache module against a fake database, so they hold across Tasks 3 and 4 without edits. They also pin the two spec constraints: the statement sequence and connection count (no new database traffic), and that every database fault degrades to provider calls.

- [ ] **Step 1: Confirm the names this plan was written against**

Run from `C:/ssw/me` (a worktree of `main` after #4):

```bash
git grep -nE "def (get_db_connection|batch_lookup_metadata|batch_persist_metadata|batch_lookup_original_release|batch_persist_original_release|cleanup_stale_metadata)\b" -- scrobblescope/cache.py
git grep -n "async def process_albums" -A9 -- scrobblescope/orchestrator/__init__.py
git grep -n "def test_" -- tests/test_module_boundaries.py
# the names fake_postgres patches or relies on
git grep -nE "^_DATABASE_URL|^    import asyncpg|^    asyncpg = None|asyncpg\.connect\(|DB_CONNECT_MAX_ATTEMPTS|DB_CONNECT_BASE_DELAY_SECONDS" -- scrobblescope/cache.py
git grep -nE "fetch_spotify_access_token|create_optimized_session|search_for_spotify_album_id|fetch_spotify_album_details_batch|search_deezer_album|fetch_deezer_album" -- scrobblescope/orchestrator/__init__.py
```

Expected: the six public definitions; `process_albums(job_id, filtered_albums, year, sort_mode, release_scope, decade=None, release_year=None,)`; the boundary tests; `scrobblescope.cache._DATABASE_URL` and `scrobblescope.cache.asyncpg` (optional import, `None` fallback) and the `asyncpg.connect(dsn, timeout=...)` call; the six provider names on the `orchestrator` facade (`fetch_spotify_access_token`, `create_optimized_session`, `search_for_spotify_album_id`, `fetch_spotify_album_details_batch`, `search_deezer_album`, `fetch_deezer_album`). If a name differs, stop: the plan was written for different code.

- [ ] **Step 2: Create the fake database**

Create `tests/fake_postgres.py`:

```python
"""An in-memory PostgreSQL for the album metadata cache.

``scrobblescope.cache`` sends a handful of statements: a batch read of
``spotify_cache``, an upsert into it, a stale-row delete, and a read and an
upsert of ``original_release_cache``. This fake answers exactly those against
two dicts and refuses anything else with an ``AssertionError``, so a test that
drives the real cache module sees what the SQL's arguments would store, not a
mock's call list, and notices at once if a change adds a statement.

``statements`` records ``(verb, table)`` for every statement, in order, which
is how a test proves a job's database traffic did not grow. ``connect_attempts``
counts calls to ``asyncpg.connect`` and ``closes`` counts ``close()`` calls.
"""

import json
from contextlib import contextmanager
from unittest.mock import patch

#: The seven data columns of ``spotify_cache`` after the two key columns, in
#: the order ``cache.py``'s upsert passes its arrays.
METADATA_FIELDS = (
    "spotify_id",
    "release_date",
    "album_image_url",
    "track_durations",
    "provider",
    "provider_album_id",
    "provider_url",
)

_ORIGINAL_FIELDS = ("mb_release_group", "original_release")


class _Row(dict):
    """What asyncpg returns: read by column name, with ``.get``."""


class FakePostgres:
    """One database, doubling as the connection the cache module is handed."""

    def __init__(self):
        self.metadata = {}
        self.original_releases = {}
        self.statements = []
        self.connect_attempts = 0
        self.closes = 0
        self._failures = {}

    def seed_metadata(self, artist_norm, album_norm, **columns):
        """Store a ``spotify_cache`` row; unnamed columns are NULL.

        ``track_durations`` may be given as a dict, which is stored as the JSON
        string asyncpg returns for a JSONB column with no codec registered.
        """
        row = dict.fromkeys(METADATA_FIELDS)
        unknown = set(columns) - set(row)
        assert not unknown, f"not a spotify_cache column: {sorted(unknown)}"
        row.update(columns)
        if isinstance(row["track_durations"], dict):
            row["track_durations"] = json.dumps(row["track_durations"])
        self.metadata[(artist_norm, album_norm)] = row

    def seed_original_release(
        self, artist_norm, album_norm, mb_release_group, original_release
    ):
        """Store an ``original_release_cache`` row."""
        self.original_releases[(artist_norm, album_norm)] = {
            "mb_release_group": mb_release_group,
            "original_release": original_release,
        }

    def fail(self, verb, table, error):
        """Make every statement of this kind raise *error*."""
        self._failures[(verb, table)] = error

    def _begin(self, sql):
        """Record a statement, raise its planted failure, return (verb, table)."""
        verb = sql.split(None, 1)[0].upper()
        if "original_release_cache" in sql:
            table = "original_release_cache"
        elif "spotify_cache" in sql:
            table = "spotify_cache"
        else:
            raise AssertionError(f"FakePostgres: unknown table in {sql[:80]!r}")
        self.statements.append((verb, table))
        error = self._failures.get((verb, table))
        if error is not None:
            raise error
        return verb, table

    async def fetch(self, sql, *args):
        """Answer the two batch reads; the TTL argument is accepted and ignored."""
        verb, table = self._begin(sql)
        if verb != "SELECT":
            raise AssertionError(f"FakePostgres.fetch got {verb} on {table}")
        artists, albums, _days = args
        wanted = set(zip(artists, albums))
        rows = self.metadata if table == "spotify_cache" else self.original_releases
        return [
            _Row(artist_norm=artist, album_norm=album, **row)
            for (artist, album), row in rows.items()
            if (artist, album) in wanted
        ]

    async def execute(self, sql, *args):
        """Apply the two upserts and accept the stale-row delete."""
        verb, table = self._begin(sql)
        if (verb, table) == ("INSERT", "spotify_cache"):
            artists, albums, *columns = args
            assert len(columns) == len(METADATA_FIELDS), (
                f"FakePostgres: spotify_cache upsert passed {len(columns)} "
                f"column arrays, expected {len(METADATA_FIELDS)}"
            )
            for index, key in enumerate(zip(artists, albums)):
                self.metadata[key] = {
                    name: values[index] for name, values in zip(METADATA_FIELDS, columns)
                }
        elif (verb, table) == ("INSERT", "original_release_cache"):
            artists, albums, *columns = args
            assert len(columns) == len(_ORIGINAL_FIELDS)
            for index, key in enumerate(zip(artists, albums)):
                self.original_releases[key] = {
                    name: values[index]
                    for name, values in zip(_ORIGINAL_FIELDS, columns)
                }
        elif (verb, table) == ("DELETE", "spotify_cache"):
            pass
        else:
            raise AssertionError(f"FakePostgres.execute got {verb} on {table}")
        return f"{verb} OK"

    async def close(self):
        """Count a close; the cache module must close exactly once per job."""
        self.closes += 1


@contextmanager
def fake_postgres(db=None, *, connect_error=None, url="postgresql://fake.invalid/cache"):
    """Point ``scrobblescope.cache`` at *db* (a new ``FakePostgres`` by default).

    ``connect_error`` makes every ``asyncpg.connect`` raise it, which is a
    database that is asleep or unreachable. ``url=None`` is a deployment with
    no ``DATABASE_URL``.
    """
    db = db or FakePostgres()

    class _Driver:
        @staticmethod
        async def connect(dsn, timeout=None):
            db.connect_attempts += 1
            if connect_error is not None:
                raise connect_error
            return db

    with (
        patch("scrobblescope.cache.asyncpg", _Driver),
        patch("scrobblescope.cache._DATABASE_URL", url),
    ):
        yield db
```

- [ ] **Step 3: Write the parity tests**

Create `tests/test_album_cache_parity.py`:

```python
"""Album metadata through the real cache module, end to end.

These tests drive ``process_albums`` (and the correction worker) against
``tests/fake_postgres.py``. They name no function of ``scrobblescope.cache``,
so they hold unchanged across the encoding change and the connection-ownership
change (AGENTS.md "Refactor requires parity tests"). What they pin:

* what a provider's album looks like once stored, and that reading it back
  answers a repeat search exactly as the live fetch did;
* that a stored row holds album facts only (``BATCH23_DEFINITION.md`` "Data
  handling": shared cache rows contain no listening facts);
* that the cache is optional: no database, a sleeping one, a failing read, a
  failing write all leave the search to the providers;
* the database traffic of one search, so a later change cannot add any (the
  hosting cost ceiling).
"""

import json
import os
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrobblescope import jobs, release_checks
from scrobblescope.domain import normalize_track_name
from scrobblescope.enrichment import AlbumMetadata
from scrobblescope.errors import SpotifyUnavailableError
from scrobblescope.orchestrator import process_albums
from tests.fake_postgres import METADATA_FIELDS, fake_postgres
from tests.helpers import TEST_JOB_PARAMS

ORCH = "scrobblescope.orchestrator."
KEY = ("radiohead", "ok computer")
SECOND_KEY = ("mitski", "laurel hell")
SPOTIFY_ID = "sp-radiohead"
SPOTIFY_URL = f"https://open.spotify.com/album/{SPOTIFY_ID}"
PLAY_COUNT = 4242
LISTENER = "listener_zq"
PARANOID = normalize_track_name("Paranoid Android")
KARMA = normalize_track_name("Karma Police")
DURATIONS = {PARANOID: 383, KARMA: 264}

SPOTIFY_DETAILS = {
    "release_date": "1997-06-16",
    "images": [{"url": "https://img.example.com/ok.jpg"}],
    "tracks": {
        "items": [
            {"name": "Paranoid Android", "duration_ms": 383000},
            {"name": "Karma Police", "duration_ms": 264000},
        ]
    },
}
DEEZER_ALBUM = AlbumMetadata(
    provider="deezer",
    album_id="9",
    url="https://www.deezer.com/album/9",
    release_date="1997-06-16",
    image_url="https://img.example.com/dz.jpg",
    track_durations=dict(DURATIONS),
)

#: The keys of one Results row. A change of encoding must not add, drop or
#: rename one: the page and the JSON endpoints read them by name.
RESULT_FIELDS = {
    "artist",
    "album",
    "play_count",
    "play_time",
    "play_time_mobile",
    "play_time_seconds",
    "different_songs",
    "release_date",
    "album_image",
    "spotify_id",
    "provider",
    "album_url",
    "_normalized_key",
    "proportion_of_max",
    "proportion_of_total",
}


def _entry(artist, album):
    """One album as the Last.fm stage hands it to enrichment."""
    return {
        "play_count": PLAY_COUNT,
        "track_counts": {PARANOID: 10, KARMA: 8},
        "original_artist": artist,
        "original_album": album,
    }


FILTERED = {KEY: _entry("Radiohead", "OK Computer")}
TWO_ALBUMS = {
    KEY: _entry("Radiohead", "OK Computer"),
    SECOND_KEY: _entry("Mitski", "Laurel Hell"),
}


def _session_ctx():
    """An async context manager standing in for an aiohttp session."""
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


@contextmanager
def _spotify(release_date="1997-06-16"):
    """Spotify matches every album (id ``sp-<artist>``) and details it."""
    details = {**SPOTIFY_DETAILS, "release_date": release_date}

    async def search(session, artist, album, token, semaphore=None):
        return f"sp-{artist}"

    async def batch(session, ids, token, semaphore=None, on_fallback=None):
        return {spotify_id: details for spotify_id in ids}

    with (
        patch(ORCH + "fetch_spotify_access_token", AsyncMock(return_value="tok")),
        patch(ORCH + "create_optimized_session", side_effect=lambda: _session_ctx()),
        patch(ORCH + "search_for_spotify_album_id", side_effect=search),
        patch(ORCH + "fetch_spotify_album_details_batch", side_effect=batch),
    ):
        yield


@contextmanager
def _deezer():
    """Spotify matches nothing; Deezer matches every album as ``DEEZER_ALBUM``."""
    with (
        patch(ORCH + "fetch_spotify_access_token", AsyncMock(return_value="tok")),
        patch(ORCH + "create_optimized_session", side_effect=lambda: _session_ctx()),
        patch(ORCH + "search_for_spotify_album_id", AsyncMock(return_value=None)),
        patch(ORCH + "search_deezer_album", AsyncMock(return_value="9")),
        patch(ORCH + "fetch_deezer_album", AsyncMock(return_value=DEEZER_ALBUM)),
    ):
        yield


@contextmanager
def _providers_forbidden():
    """A cache hit must reach no provider: any call fails the test."""
    fault = AssertionError("a provider was called on a cache hit")
    with (
        patch(ORCH + "fetch_spotify_access_token", AsyncMock(side_effect=fault)),
        patch(ORCH + "search_deezer_album", AsyncMock(side_effect=fault)),
    ):
        yield


async def _search(filtered=None, *, year=1997, scope="same", params=None):
    """Run ``process_albums`` for a fresh job; return ``(job_id, results)``."""
    job_id = jobs.create(params or TEST_JOB_PARAMS)
    results = await process_albums(
        job_id, filtered or FILTERED, year, "playcount", scope
    )
    return job_id, results


def _stats(job_id):
    """The job's recorded stats."""
    return jobs.progress(job_id)["stats"]


# ---------------------------------------------------------------------------
# Storage and read-back
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it():
    """
    GIVEN Spotify details an album that is not cached
    WHEN the search runs, then runs again with every provider forbidden
    THEN the stored row holds the album's facts under the provider columns,
    and the second search returns exactly the rows the first returned.
    """
    with fake_postgres() as db:
        with _spotify():
            _, first = await _search()
        stored = dict(db.metadata[KEY])
        durations = json.loads(stored.pop("track_durations"))
        with _providers_forbidden():
            _, second = await _search()

    assert durations == DURATIONS
    assert stored == {
        "spotify_id": SPOTIFY_ID,
        "release_date": "1997-06-16",
        "album_image_url": "https://img.example.com/ok.jpg",
        "provider": "spotify",
        "provider_album_id": SPOTIFY_ID,
        "provider_url": SPOTIFY_URL,
    }
    assert second == first
    (row,) = first
    assert set(row) == RESULT_FIELDS
    assert (row["spotify_id"], row["provider"], row["album_url"]) == (
        SPOTIFY_ID,
        "spotify",
        SPOTIFY_URL,
    )
    assert row["play_time_seconds"] == 383 * 10 + 264 * 8


@pytest.mark.asyncio
async def test_a_deezer_album_is_stored_without_a_spotify_id_and_a_repeat_search_matches_it():
    """
    GIVEN Spotify has no match and Deezer details the album
    WHEN the search runs, then runs again with every provider forbidden
    THEN the legacy spotify_id column stays NULL, the Deezer id and link are
    stored under the provider columns, and the repeat search returns the
    same rows.
    """
    with fake_postgres() as db:
        with _deezer():
            _, first = await _search()
        stored = dict(db.metadata[KEY])
        with _providers_forbidden():
            _, second = await _search()

    assert stored["spotify_id"] is None
    assert (
        stored["provider"],
        stored["provider_album_id"],
        stored["provider_url"],
    ) == ("deezer", "9", "https://www.deezer.com/album/9")
    assert second == first
    (row,) = first
    assert set(row) == RESULT_FIELDS
    assert (row["spotify_id"], row["provider"], row["album_url"]) == (
        None,
        "deezer",
        "https://www.deezer.com/album/9",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "columns",
    [
        {"spotify_id": "sp9"},
        {"spotify_id": "sp9", "provider": "spotify", "provider_album_id": "sp9"},
    ],
    ids=["written_before_the_provider_columns", "backfilled_without_a_link"],
)
async def test_an_older_spotify_row_reads_as_a_spotify_album_with_the_classic_link(
    columns,
):
    """
    GIVEN a cached row from before the provider columns, or one the migration
    backfilled with no link
    WHEN a search reads it
    THEN it is a Spotify album and its link is Spotify's classic album page.
    """
    with fake_postgres() as db:
        db.seed_metadata(
            *KEY,
            release_date="1997-06-16",
            album_image_url="https://img.example.com/ok.jpg",
            track_durations=DURATIONS,
            **columns,
        )
        with _providers_forbidden():
            _, results = await _search()

    (row,) = results
    assert (row["provider"], row["spotify_id"], row["album_url"]) == (
        "spotify",
        "sp9",
        "https://open.spotify.com/album/sp9",
    )
    assert row["play_time_seconds"] == 383 * 10 + 264 * 8


@pytest.mark.asyncio
@pytest.mark.parametrize("providers", [_spotify, _deezer], ids=["spotify", "deezer"])
async def test_a_stored_row_carries_no_listening_fact(providers):
    """
    GIVEN an album entry that carries the listener's name next to the 4242
    plays the listener made
    WHEN the album is stored in the shared cache
    THEN the row has exactly the album-fact columns, its durations are track
    name to seconds and nothing else, and neither the play count nor the
    listener's name appears anywhere in it (BATCH23 Data handling).
    """
    entry = {**_entry("Radiohead", "OK Computer"), "listener": LISTENER}
    with fake_postgres() as db:
        with providers():
            await _search({KEY: entry})

    (row,) = db.metadata.values()
    assert set(row) == set(METADATA_FIELDS)
    assert json.loads(row["track_durations"]) == DURATIONS
    stored = json.dumps(row)
    assert str(PLAY_COUNT) not in stored
    assert LISTENER not in stored


# ---------------------------------------------------------------------------
# The cache is optional
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_search_with_no_database_configured_uses_the_providers_and_connects_to_nothing():
    """
    GIVEN no DATABASE_URL
    WHEN a search runs
    THEN the providers answer it, no connection is attempted, and the job
    records that the cache was off.
    """
    with fake_postgres(url=None) as db:
        with _spotify():
            job_id, results = await _search()

    assert [row["spotify_id"] for row in results] == [SPOTIFY_ID]
    assert db.connect_attempts == 0
    assert db.statements == []
    assert _stats(job_id)["db_cache_enabled"] is False
    assert "db_cache_warning" in _stats(job_id)


@pytest.mark.asyncio
async def test_a_search_while_the_database_is_asleep_uses_the_providers_after_bounded_attempts():
    """
    GIVEN a database that never answers (every connect times out)
    WHEN a search runs
    THEN it makes exactly DB_CONNECT_MAX_ATTEMPTS attempts, no more, then the
    providers answer it and the job records a cache warning. A sleeping
    database must cost one bounded wake-up attempt, not a failed job.
    """
    env = {"DB_CONNECT_MAX_ATTEMPTS": "3", "DB_CONNECT_BASE_DELAY_SECONDS": "0"}
    with fake_postgres(connect_error=TimeoutError()) as db:
        with patch.dict(os.environ, env), _spotify():
            job_id, results = await _search()

    assert [row["spotify_id"] for row in results] == [SPOTIFY_ID]
    assert db.connect_attempts == 3
    assert db.statements == []
    assert _stats(job_id)["db_cache_enabled"] is False
    assert "db_cache_warning" in _stats(job_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("statement", "warning"),
    [
        (("SELECT", "spotify_cache"), "DB lookup failed; cache bypassed."),
        (("INSERT", "spotify_cache"), "DB persist failed."),
        (("SELECT", "original_release_cache"), None),
    ],
    ids=["read", "write", "correction_read"],
)
async def test_a_failing_cache_statement_never_fails_the_search(statement, warning):
    """
    GIVEN one cache statement raises (a dropped connection)
    WHEN a search runs
    THEN the providers still answer it, the job carries the matching warning
    (none for the correction read), and the search used one connection, closed
    once: a failure never opens a second connection.
    """
    with fake_postgres() as db:
        db.fail(*statement, OSError("connection reset"))
        with _spotify():
            job_id, results = await _search()

    assert [row["spotify_id"] for row in results] == [SPOTIFY_ID]
    assert _stats(job_id).get("db_cache_warning") == warning
    assert (db.connect_attempts, db.closes) == (1, 1)


@pytest.mark.asyncio
async def test_the_connection_is_closed_once_when_the_search_succeeds():
    """A finished search leaves no connection open."""
    with fake_postgres() as db:
        with _spotify():
            await _search()

    assert (db.connect_attempts, db.closes) == (1, 1)


@pytest.mark.asyncio
async def test_the_connection_is_closed_once_when_no_provider_can_answer():
    """
    GIVEN Spotify cannot issue a token and Deezer finds nothing
    WHEN the search raises SpotifyUnavailableError
    THEN the connection was still closed, once.
    """
    with fake_postgres() as db:
        with (
            patch(ORCH + "fetch_spotify_access_token", AsyncMock(return_value=None)),
            patch(
                ORCH + "create_optimized_session", side_effect=lambda: _session_ctx()
            ),
            patch(ORCH + "search_deezer_album", AsyncMock(return_value=None)),
            pytest.raises(SpotifyUnavailableError),
        ):
            await _search()

    assert (db.connect_attempts, db.closes) == (1, 1)


# ---------------------------------------------------------------------------
# Database traffic: the hosting cost ceiling
# ---------------------------------------------------------------------------

SELECT_METADATA = ("SELECT", "spotify_cache")
DELETE_STALE = ("DELETE", "spotify_cache")
INSERT_METADATA = ("INSERT", "spotify_cache")
SELECT_CORRECTIONS = ("SELECT", "original_release_cache")


@pytest.mark.asyncio
async def test_a_search_costs_one_connection_and_a_fixed_statement_sequence():
    """
    GIVEN two albums, neither cached
    WHEN a search runs, then runs again with both cached
    THEN the first costs one connection and four statements (one batch read,
    one stale-row delete, ONE upsert for both albums, one correction read) and
    the second three (no upsert). A change that persists per album, retries,
    reconnects or adds a statement wakes the database more often than the
    hosting cost ceiling allows, and fails here.
    """
    with fake_postgres() as db:
        with _spotify():
            await _search(TWO_ALBUMS)
        assert db.statements == [
            SELECT_METADATA,
            DELETE_STALE,
            INSERT_METADATA,
            SELECT_CORRECTIONS,
        ]
        assert (db.connect_attempts, db.closes) == (1, 1)

        db.statements.clear()
        with _providers_forbidden():
            await _search(TWO_ALBUMS)
        assert db.statements == [SELECT_METADATA, DELETE_STALE, SELECT_CORRECTIONS]
        assert (db.connect_attempts, db.closes) == (2, 2)


# ---------------------------------------------------------------------------
# MusicBrainz year correction, and the exclusion record
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_musicbrainz_finding_is_stored_and_corrects_the_next_search():
    """
    GIVEN an album a provider dates 2011 (a reissue) and MusicBrainz dates 1977
    WHEN the correction worker checks the finished job, then a 1977 search runs
    THEN the finding is stored, and the later search shows the album under
    1977 while keeping the provider's date beside it.
    """
    first_params = {**TEST_JOB_PARAMS, "year": 2011, "release_scope": "same"}
    with fake_postgres() as db:
        with _spotify(release_date="2011-01-31"):
            job_id, results = await _search(year=2011, params=first_params)
        assert [row["release_date"] for row in results] == ["2011-01-31"]
        jobs.succeed(job_id, results, "done")

        with (
            patch.object(release_checks, "MUSICBRAINZ_ENABLED", True),
            patch.object(
                release_checks,
                "lookup_original_release",
                AsyncMock(return_value=("mbid-1", "1977-02-04")),
            ),
            patch.object(
                release_checks,
                "create_optimized_session",
                side_effect=lambda: _session_ctx(),
            ),
        ):
            await release_checks.run_release_checks(job_id)
        assert db.original_releases[KEY] == {
            "mb_release_group": "mbid-1",
            "original_release": "1977-02-04",
        }

        with _providers_forbidden():
            _, corrected = await _search(year=1977)

    (row,) = corrected
    assert row["release_date"] == "1977-02-04"
    assert row["provider_release_date"] == "2011-01-31"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("providers", "expected"),
    [
        (
            _spotify,
            {
                "spotify_id": SPOTIFY_ID,
                "provider": "spotify",
                "album_url": SPOTIFY_URL,
                "album_image": "https://img.example.com/ok.jpg",
            },
        ),
        (
            _deezer,
            {
                "spotify_id": None,
                "provider": "deezer",
                "album_url": "https://www.deezer.com/album/9",
                "album_image": "https://img.example.com/dz.jpg",
            },
        ),
    ],
    ids=["spotify", "deezer"],
)
async def test_an_album_outside_the_release_scope_is_listed_with_its_provider_facts(
    providers, expected
):
    """
    GIVEN an album released in 1997 and a 2024 search
    WHEN the release filter excludes it
    THEN the unmatched record carries the provider, link, cover and provider
    date, and exactly the fields the Unmatched page reads.
    """
    with fake_postgres():
        with providers():
            job_id, results = await _search(year=2024)

    assert results == []
    (entry,) = jobs.unmatched(job_id).values()
    assert entry["reason_code"] == "release_scope"
    assert {name: entry[name] for name in expected} == expected
    assert entry["provider_release_date"] == "1997-06-16"
    assert set(entry) == {
        "artist",
        "album",
        "reason",
        "reason_code",
        "album_image",
        "spotify_id",
        "provider",
        "album_url",
        "play_count",
        "provider_release_date",
    }
```

- [ ] **Step 4: Run them on the unchanged tree; they pass**

Run: `"$PY" -m pytest tests/test_album_cache_parity.py -q -p no:cacheprovider`
Expected: `17 passed` (count the `def test_` lines and the parametrize rows if it differs). A failure here means the test describes behaviour the code does not have: fix the test, never `scrobblescope/`.

- [ ] **Step 5: Mutation evidence**

For each row: plant the edit in a scratch copy of the tree (or copy the named file aside first and copy it back after; this task changes no source file, but the later tasks do, so use the same routine throughout), run the named test, confirm it FAILS, then restore and confirm it passes again. Never use `git checkout -- <file>`. Run: `"$PY" -m pytest tests/test_album_cache_parity.py -q -p no:cacheprovider -k "<test name fragment>"`.

| # | Planted defect | File | Test that must fail |
|---|---|---|---|
| 1 | in `batch_lookup_metadata`'s result dict, `"album_image_url": r["album_image_url"]` becomes `r["spotify_id"]` | `scrobblescope/cache.py` | `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` |
| 2 | `AlbumMetadata.as_cache_row` writes `self.album_id` into the `spotify_id` slot for every provider (drop the `if self.provider == "spotify" else None`) | `scrobblescope/enrichment.py` | `test_a_deezer_album_is_stored_without_a_spotify_id_and_a_repeat_search_matches_it` |
| 3 | `_album_provider` returns `cached.get("provider")` only (drop the Spotify fallback) | `scrobblescope/orchestrator/_results.py` | `test_an_older_spotify_row_reads_as_a_spotify_album_with_the_classic_link[written_before_the_provider_columns]` |
| 4 | `_album_url` ends `return None` before it builds the classic link | `scrobblescope/orchestrator/_results.py` | the same test, both rows |
| 5 | in `_run_spotify_batch_detail_phase`, replace `new_metadata_rows.append(metadata.as_cache_row(key[0], key[1]))` with `row = metadata.as_cache_row(key[0], key[1]); new_metadata_rows.append(row[:5] + ({**row[5], "plays": original_data["play_count"]},) + row[6:])` | `scrobblescope/orchestrator/_details.py` | `test_a_stored_row_carries_no_listening_fact[spotify]` (play count) |
| 6 | in `get_db_connection`'s `if attempt >= max_attempts:` block, replace `return None` with `raise` | `scrobblescope/cache.py` | `test_a_search_while_the_database_is_asleep_uses_the_providers_after_bounded_attempts` |
| 7 | in `get_db_connection`, delete the `if not dsn:` branch (the `logging.info(...)` and `return None`) | `scrobblescope/cache.py` | `test_a_search_with_no_database_configured_uses_the_providers_and_connects_to_nothing` |
| 8 | in `_persist_new_metadata`, remove the `try`/`except` so the call is bare | `scrobblescope/orchestrator/_cache.py` | `test_a_failing_cache_statement_never_fails_the_search[write]` |
| 9 | in `process_albums`, replace `await conn.close()` with `pass` | `scrobblescope/orchestrator/__init__.py` | both `test_the_connection_is_closed_once_*` tests |
| 10 | `batch_persist_metadata` issues its upsert twice (call `conn.execute` a second time with the same arguments) | `scrobblescope/cache.py` | `test_a_search_costs_one_connection_and_a_fixed_statement_sequence` |
| 11 | in `batch_persist_original_release`, pass `original_releases` where `mb_release_groups` goes and the reverse | `scrobblescope/cache.py` | `test_a_musicbrainz_finding_is_stored_and_corrects_the_next_search` |
| 12 | the exclusion entry in `_build_results` sets `"provider": None` | `scrobblescope/orchestrator/_results.py` | `test_an_album_outside_the_release_scope_is_listed_with_its_provider_facts` (both rows) |
| 13 | in `_lookup_cached_metadata`, remove the `try`/`except` so the read is bare | `scrobblescope/orchestrator/_cache.py` | `test_a_failing_cache_statement_never_fails_the_search[read]` |
| 14 | in `_lookup_cached_original_release`, remove the `try`/`except` so the read is bare | `scrobblescope/orchestrator/_cache.py` | `test_a_failing_cache_statement_never_fails_the_search[correction_read]` |
| 15 | in `_run_spotify_batch_detail_phase`, plant the row-5 edit with `"listener": original_data["listener"]` in place of `"plays": original_data["play_count"]` | `scrobblescope/orchestrator/_details.py` | `test_a_stored_row_carries_no_listening_fact[spotify]` (listener's name) |

Row 9 note: `process_albums` closes in a `finally`; if the edit leaves a syntax error, fix the edit, not the test. Rows 8, 13 and 14 note: the other `failing_cache_statement` rows must still pass. Row 15 needs the `"listener"` key the test puts on the album entry. The `[deezer]` case runs the same assertions; Step 5 plants the leak in the Spotify path only.

- [ ] **Step 6: Section 4 entry, gates, commit**

Entry heading: `### <commit date> - Cache storage and failure behaviour are pinned end to end`. Body: scope (one fake database, 17 tests through the real cache module and the correction worker); why (every existing test patches `cache.py`'s own functions, so none could prove the stored row, the read-back or the Results JSON survives the encoding change; PR #5 follows); what the tests pin (stored columns per provider; live equals cached; legacy rows; no listening fact; no database, asleep, failing read, failing write, failing correction read; one connection and a fixed statement sequence, which is the hosting-cost evidence Tasks 3 and 4 re-run); deviations (none); the 15 mutation rows; the Validation line (``Validation: `pytest -q` -- **N passed**.``).
Run the commit procedure. This task adds a `test_*.py` module, so after staging it (`git add tests/fake_postgres.py tests/test_album_cache_parity.py`) measure the module count with `git ls-files tests | grep -c '/test_[^/]*\.py$'` (never "+1") and write it, with the new test total N, into the two places `--fix` does not render: `.claude/SESSION_CONTEXT.md`'s Tests row (and Section 6 if it states the count) and the header line of `docs/agents/FINDINGS.md` ("N tests across M tracked test modules."). Stage: `git add tests/fake_postgres.py tests/test_album_cache_parity.py .claude/SESSION_CONTEXT.md docs/agents/FINDINGS.md docs/agents/PLAYBOOK.md` plus whatever `doc_state_sync.py --fix --test-count N` rewrote (name each file).
Subject: `test(cache): Pin album metadata storage and cache failure policy` (64 characters).

---
### Task 2: An album reads itself from a cache row

**Touches:** `scrobblescope/enrichment.py`, `scrobblescope/spotify.py` (one line), `tests/services/test_enrichment.py`, `.claude/SESSION_CONTEXT.md` (Section 3, one line), `docs/agents/PLAYBOOK.md`.
**After:** Task 1.

**Files:**
- Modify: `scrobblescope/enrichment.py`, `scrobblescope/spotify.py`, `tests/services/test_enrichment.py`, `.claude/SESSION_CONTEXT.md`, `docs/agents/PLAYBOOK.md`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `enrichment.SPOTIFY_ALBUM_URL` (`"https://open.spotify.com/album/{album_id}"`); `AlbumMetadata.spotify_id` (property, `str | None`: the album id for a Spotify album, `None` for any other provider); `AlbumMetadata.from_row(row) -> AlbumMetadata | None` (classmethod; *row* is any mapping with `.get`, such as an asyncpg `Record` of `spotify_cache` or a dict). Task 3 calls `from_row` from the cache and `spotify_id` from the cache's writer and from the results builder.

Why: the rules for reading a cache row, including rows older than the provider columns, are written today in two places that disagree about where they live: `cache.batch_lookup_metadata` builds a dict and `_results._album_provider` / `_album_url` finish the job later. This task writes the rules once, with their own tests, before anything calls them. It is additive: no caller changes, so the suite and Task 1's tests are untouched.

- [ ] **Step 1: Write the failing tests**

Replace the imports at the top of `tests/services/test_enrichment.py` with the block below (keep the three existing tests as they are until Task 3), and append the tests:

```python
import dataclasses

import pytest

from scrobblescope.enrichment import SPOTIFY_ALBUM_URL, AlbumMetadata
```

```python
def _row(**overrides):
    """A modern spotify_cache row for a Spotify album; override columns freely."""
    row = {
        "spotify_id": "sp1",
        "release_date": "1997-06-16",
        "album_image_url": "https://img.example.com/ok.jpg",
        "track_durations": {"paranoid android": 383},
        "provider": "spotify",
        "provider_album_id": "sp1",
        "provider_url": "https://open.spotify.com/album/sp1",
    }
    row.update(overrides)
    return row


_DEEZER_COLUMNS = {
    "spotify_id": None,
    "provider": "deezer",
    "provider_album_id": "6237061",
    "provider_url": "https://www.deezer.com/album/6237061",
}


def test_only_a_spotify_album_has_a_spotify_id():
    """The legacy spotify_id column and the Results page's spotify_id field hold
    a Spotify id and nothing else; a Deezer id is not one."""
    spotify = AlbumMetadata.from_row(_row())
    deezer = AlbumMetadata.from_row(_row(**_DEEZER_COLUMNS))

    assert spotify.spotify_id == "sp1"
    assert deezer.spotify_id is None


def test_a_stored_row_maps_every_field_to_the_album():
    """Each column lands in its own field (distinct values, so a swap shows)."""
    album = AlbumMetadata.from_row(_row())

    assert album == AlbumMetadata(
        provider="spotify",
        album_id="sp1",
        url="https://open.spotify.com/album/sp1",
        release_date="1997-06-16",
        image_url="https://img.example.com/ok.jpg",
        track_durations={"paranoid android": 383},
    )


def test_a_deezer_row_keeps_the_deezer_id_and_link():
    """A Deezer row has no spotify_id; its id and link come from the provider
    columns."""
    album = AlbumMetadata.from_row(_row(**_DEEZER_COLUMNS))

    assert (album.provider, album.album_id, album.url) == (
        "deezer",
        "6237061",
        "https://www.deezer.com/album/6237061",
    )


@pytest.mark.parametrize(
    "columns",
    [
        {"provider": None, "provider_album_id": None, "provider_url": None},
        {"provider_url": None},
    ],
    ids=["written_before_the_provider_columns", "backfilled_without_a_link"],
)
def test_an_older_spotify_row_is_a_spotify_album_with_the_classic_link(columns):
    """A row with no provider value is a Spotify row, and a Spotify row with no
    stored link gets Spotify's classic album page: the rule `_album_provider`
    and `_album_url` carried."""
    album = AlbumMetadata.from_row(_row(**columns))

    assert (album.provider, album.album_id) == ("spotify", "sp1")
    assert album.url == SPOTIFY_ALBUM_URL.format(album_id="sp1")
    assert album.url == "https://open.spotify.com/album/sp1"


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ('{"a": 1, "b": 2}', {"a": 1, "b": 2}),
        ({"a": 1}, {"a": 1}),
        ("{}", {}),
        ("", {}),
        (None, {}),
    ],
    ids=["json_text", "dict", "empty_object", "empty_text", "null"],
)
def test_track_durations_read_as_a_dict_whatever_the_driver_returned(stored, expected):
    """asyncpg returns JSONB as text unless a codec is registered; either way the
    album's durations are a dict, empty when there are none."""
    assert AlbumMetadata.from_row(_row(track_durations=stored)).track_durations == (
        expected
    )


def test_a_row_with_no_release_date_has_an_empty_one():
    """release_date is a nullable column. An album with no date is excluded by
    every release scope but "all"; it must not carry None into the filter, which
    splits the date as text."""
    assert AlbumMetadata.from_row(_row(release_date=None)).release_date == ""


@pytest.mark.parametrize(
    "columns",
    [
        {"provider": None, "spotify_id": None, "provider_album_id": None},
        {"provider": "deezer", "spotify_id": None, "provider_album_id": None},
    ],
    ids=["no_provider", "no_album_id"],
)
def test_a_row_that_names_no_provider_album_reads_as_nothing(columns):
    """Such a row cannot be shown or linked; reading it as None makes it a cache
    miss that the next fetch overwrites."""
    assert AlbumMetadata.from_row(_row(**columns)) is None


def test_album_metadata_holds_album_facts_only():
    """These fields are the shared cache's columns (BATCH23 "Data handling":
    shared cache rows contain no listening facts). Adding a field here adds a
    column there, so the field set is pinned: a change must be deliberate."""
    assert {field.name for field in dataclasses.fields(AlbumMetadata)} == {
        "provider",
        "album_id",
        "url",
        "release_date",
        "image_url",
        "track_durations",
    }
```

- [ ] **Step 2: Run them; they fail**

Run: `"$PY" -m pytest tests/services/test_enrichment.py -q -p no:cacheprovider`
Expected: collection error `ImportError: cannot import name 'SPOTIFY_ALBUM_URL'`.

- [ ] **Step 3: Implement**

In `scrobblescope/enrichment.py`, add `import json` and `from collections.abc import Mapping` and `from typing import Any` above the dataclass import (keep import order: standard library, alphabetical), then the constant, the property and the classmethod. The existing `as_cache_row` stays until Task 3.

```python
#: Spotify's classic album page. A cache row older than the provider columns
#: carries no link, and a Spotify payload that names none falls back to this.
SPOTIFY_ALBUM_URL = "https://open.spotify.com/album/{album_id}"
```

Inside `AlbumMetadata`, after the field list and before `as_cache_row`:

```python
    @property
    def spotify_id(self) -> str | None:
        """The Spotify album id, or None for an album from any other provider.

        The legacy ``spotify_id`` column and the Results page's ``spotify_id``
        field hold a Spotify id only. A Deezer album keeps its own id in
        ``album_id``.
        """
        return self.album_id if self.provider == "spotify" else None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "AlbumMetadata | None":
        """Read one ``spotify_cache`` row as an album, or None if it names none.

        The one place a stored row becomes an ``AlbumMetadata``. Rows written
        before the provider columns existed hold only ``spotify_id``: they are
        Spotify albums, and a Spotify album with no stored link gets
        ``SPOTIFY_ALBUM_URL``. A NULL release date reads as ``""`` and
        ``track_durations`` as a dict (the driver may hand back JSON text). A
        row with no provider and no album id returns None, so the caller treats
        it as a miss.

        Args:
            row: A mapping with the ``spotify_cache`` data columns, read with
                ``.get`` (an asyncpg ``Record`` or a dict).
        """
        spotify_id = row.get("spotify_id")
        provider = row.get("provider") or ("spotify" if spotify_id else None)
        album_id = row.get("provider_album_id") or spotify_id
        if not provider or not album_id:
            return None
        url = row.get("provider_url")
        if not url:
            url = (
                SPOTIFY_ALBUM_URL.format(album_id=album_id)
                if provider == "spotify"
                else ""
            )
        durations = row.get("track_durations")
        if isinstance(durations, str):
            durations = json.loads(durations) if durations else {}
        return cls(
            provider=provider,
            album_id=album_id,
            url=url,
            release_date=row.get("release_date") or "",
            image_url=row.get("album_image_url"),
            track_durations=durations or {},
        )
```

In `scrobblescope/spotify.py` import the constant (`from scrobblescope.enrichment import SPOTIFY_ALBUM_URL, AlbumMetadata`) and, in `album_metadata_from_details`, replace the f-string default:

```python
        url=details.get("external_urls", {}).get(
            "spotify", SPOTIFY_ALBUM_URL.format(album_id=spotify_id)
        ),
```

In `.claude/SESSION_CONTEXT.md` Section 3, change the `enrichment.py` line to `# AlbumMetadata, the one contract every enrichment provider returns, and the reader for a cache row (from_row)`.

- [ ] **Step 4: Run the tests; they pass**

Run: `"$PY" -m pytest tests/services/test_enrichment.py tests/services/test_spotify_service.py tests/test_album_cache_parity.py -q -p no:cacheprovider`
Expected: all pass (`test_spotify_service` pins that the Spotify link is unchanged).

- [ ] **Step 5: Mutation evidence**

| # | Planted defect | Test that must fail |
|---|---|---|
| 1 | `spotify_id` returns `self.album_id` for every provider | `test_only_a_spotify_album_has_a_spotify_id` |
| 2 | in `from_row`, `release_date=row.get("album_image_url")` and `image_url=row.get("release_date")` | `test_a_stored_row_maps_every_field_to_the_album` |
| 3 | `album_id = spotify_id` (drop the `provider_album_id` read) | `test_a_deezer_row_keeps_the_deezer_id_and_link` |
| 4 | `provider = row.get("provider")` (drop the Spotify fallback) | `test_an_older_spotify_row_is_a_spotify_album_with_the_classic_link[written_before_the_provider_columns]` |
| 5 | `url = row.get("provider_url")` with the fallback block deleted | the same test, both rows |
| 6 | `track_durations=durations` (drop the `json.loads` and the `or {}`) | `test_track_durations_read_as_a_dict_whatever_the_driver_returned` (json_text, empty_text, null) |
| 7 | `release_date=row.get("release_date")` | `test_a_row_with_no_release_date_has_an_empty_one` |
| 8 | delete the `if not provider or not album_id: return None` guard | `test_a_row_that_names_no_provider_album_reads_as_nothing` |
| 9 | add the field `play_count: int = 0` to `AlbumMetadata` | `test_album_metadata_holds_album_facts_only` |

Plant each in a scratch copy of the tree, or copy `scrobblescope/enrichment.py` aside first and copy it back after each row (never `git checkout -- <file>`: the file holds this task's uncommitted `from_row`), and re-run to see it pass.

- [ ] **Step 6: Section 4 entry, gates, commit**

Entry heading: `### <commit date> - An album reads itself from a cache row`. Body: scope (one classmethod, one property, one constant, one line in `spotify.py`); why (the legacy-row rules lived in `_results._album_provider` and `_album_url`; Task 3 deletes those and needs the rule in one tested place); deviations (a row naming no provider album now reads as None; no write path produces one); the nine mutation rows; the Validation line (R4 form).
Subject: `feat(enrichment): Read an album from a cache row` (48 characters).

---

### Task 3: Store and read album metadata as one record

**Touches:** `scrobblescope/cache.py`, `scrobblescope/enrichment.py`, `scrobblescope/orchestrator/__init__.py`, `scrobblescope/orchestrator/_cache.py`, `scrobblescope/orchestrator/_details.py`, `scrobblescope/orchestrator/_deezer_fallback.py`, `scrobblescope/orchestrator/_results.py`, `tests/album_metadata.py` (new), `tests/services/test_cache.py`, `tests/test_repositories.py`, `tests/services/test_enrichment.py`, `tests/services/test_orchestrator_process_albums.py`, `tests/services/test_orchestrator_helpers.py`, `tests/services/test_orchestrator_fetch_spotify.py`, `tests/services/test_failure_logging.py`, `.claude/SESSION_CONTEXT.md`, `docs/architecture/runtime-system.md`, `docs/agents/FINDINGS.md`, `docs/agents/PLAYBOOK.md`.
**After:** Tasks 1 and 2.

**Files:**
- Create: `tests/album_metadata.py`
- Modify: the files above

**Interfaces:**
- Consumes: Task 2's `AlbumMetadata.from_row`, `AlbumMetadata.spotify_id`; Task 1's tests (unchanged).
- Produces:
  - `cache.batch_lookup_metadata(conn, keys) -> dict[tuple[str, str], AlbumMetadata]` (rows naming no provider album are left out).
  - `cache.batch_persist_metadata(conn, albums)` where *albums* is `Mapping[tuple[str, str], AlbumMetadata]`; one statement for all of them; `{}` is a no-op.
  - `orchestrator._run_spotify_batch_detail_phase(...)`, `_run_deezer_fallback_phase(...)` and `_fetch_spotify_misses(...)` return `dict[tuple[str, str], AlbumMetadata]` (was a list of nine-tuples); `process_albums`' `cache_hits[key]["cached"]` is an `AlbumMetadata` for hits and live fetches alike.
  - `orchestrator._persist_new_metadata(conn, job_id, new_metadata)` takes that dict.
  - `tests.album_metadata.spotify_metadata(album_id="sp1", release_date="2025-01-01", image_url="https://img.example.com/a.jpg", track_durations=None)` and `deezer_metadata(album_id="dz1", release_date="2025-02-02", image_url="https://cdn.example/dz.jpg", track_durations=None)` -> `AlbumMetadata`.
  - Deleted: `AlbumMetadata.as_cache_row`, `_results._album_provider`, `_results._album_url`, the `len(r) > 6` branches, both inline `cached` dicts.

Why: B-5. After the providers an album is re-encoded as a nine-tuple for the database, as a 4-key or 7-key dict for results and as a 7-key dict from cache reads; two functions in `_results.py` exist to repair what the shortest of them lacks. One record from provider to page deletes all of it, and leaves one place a stored row is read (`from_row`) and one statement that writes the shared table.

- [ ] **Step 1: Create the test builders**

Create `tests/album_metadata.py`:

```python
"""Builders for the album records tests hand to the cache and the results."""

from scrobblescope.enrichment import AlbumMetadata


def spotify_metadata(
    album_id="sp1",
    release_date="2025-01-01",
    image_url="https://img.example.com/a.jpg",
    track_durations=None,
):
    """A Spotify album as ``album_metadata_from_details`` would return it."""
    return AlbumMetadata(
        provider="spotify",
        album_id=album_id,
        url=f"https://open.spotify.com/album/{album_id}",
        release_date=release_date,
        image_url=image_url,
        track_durations={} if track_durations is None else track_durations,
    )


def deezer_metadata(
    album_id="dz1",
    release_date="2025-02-02",
    image_url="https://cdn.example/dz.jpg",
    track_durations=None,
):
    """A Deezer album as ``fetch_deezer_album`` would return it."""
    return AlbumMetadata(
        provider="deezer",
        album_id=album_id,
        url=f"https://www.deezer.com/album/{album_id}",
        release_date=release_date,
        image_url=image_url,
        track_durations={} if track_durations is None else track_durations,
    )
```

- [ ] **Step 2: Rewrite the existing tests that name the old encodings**

Do these edits first; the suite fails until Steps 3-6 are done.

**`tests/services/test_enrichment.py`.** In `test_album_metadata_carries_its_provider_and_url`, delete the `as_cache_row` assertion (the `assert meta.as_cache_row(...) == (...)` block) and replace it with `assert meta.url == "https://www.deezer.com/album/6237061"`. Delete `test_cache_row_matches_what_the_persistence_layer_unpacks` and `test_cache_row_puts_a_spotify_album_id_in_the_spotify_column`: they pin a tuple order that no longer exists; the stored columns are pinned by Task 1 (`test_a_spotify_album_is_stored_as_album_facts...`, `test_a_deezer_album_is_stored_without_a_spotify_id...`) and by the cache tests below.

**`tests/services/test_cache.py`.** Change the import block to:

```python
from unittest.mock import AsyncMock

import pytest

from scrobblescope.cache import (
    SCHEMA_OUT_OF_DATE_REMEDIATION,
    batch_lookup_metadata,
    batch_lookup_original_release,
    batch_persist_metadata,
    batch_persist_original_release,
    schema_is_out_of_date,
)
from scrobblescope.enrichment import AlbumMetadata
from tests.album_metadata import deezer_metadata, spotify_metadata
```

(keep any other import the file already has). Replace the four tests `test_batch_lookup_metadata_selects_and_returns_provider_columns`, `test_batch_lookup_metadata_defaults_provider_fields_when_absent`, `test_batch_persist_metadata_writes_provider_columns_when_given` and `test_batch_persist_metadata_defaults_provider_for_legacy_six_tuple` with:

```python
@pytest.mark.asyncio
async def test_batch_lookup_metadata_returns_albums_with_their_provider_columns():
    """A row carrying the provider columns comes back as that provider's album."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(
        return_value=[
            {
                "artist_norm": "grey orton",
                "album_norm": "rumours",
                "spotify_id": None,
                "release_date": "1977-02-04",
                "album_image_url": "https://cdn.example/cover.jpg",
                "track_durations": {},
                "provider": "deezer",
                "provider_album_id": "6237061",
                "provider_url": "https://www.deezer.com/album/6237061",
            }
        ]
    )

    result = await batch_lookup_metadata(mock_conn, [("grey orton", "rumours")])

    fetch_sql = mock_conn.fetch.call_args[0][0]
    assert "provider" in fetch_sql
    assert "provider_album_id" in fetch_sql
    assert "provider_url" in fetch_sql
    assert result == {
        ("grey orton", "rumours"): AlbumMetadata(
            provider="deezer",
            album_id="6237061",
            url="https://www.deezer.com/album/6237061",
            release_date="1977-02-04",
            image_url="https://cdn.example/cover.jpg",
            track_durations={},
        )
    }


@pytest.mark.asyncio
async def test_batch_lookup_metadata_reads_a_pre_provider_row_as_a_spotify_album():
    """A row written before the provider columns (none in the mock) must not
    raise: it is a Spotify album with Spotify's classic link."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(
        return_value=[
            {
                "artist_norm": "radiohead",
                "album_norm": "ok computer",
                "spotify_id": "abc123",
                "release_date": "1997-06-16",
                "album_image_url": None,
                "track_durations": {},
            }
        ]
    )

    result = await batch_lookup_metadata(mock_conn, [("radiohead", "ok computer")])

    album = result[("radiohead", "ok computer")]
    assert (album.provider, album.album_id) == ("spotify", "abc123")
    assert album.url == "https://open.spotify.com/album/abc123"


@pytest.mark.asyncio
async def test_a_row_naming_no_provider_album_is_a_cache_miss():
    """A row with neither a provider nor an album id cannot be shown; leaving it
    out makes it a miss, so the next fetch overwrites it."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(
        return_value=[
            {
                "artist_norm": "a",
                "album_norm": "b",
                "spotify_id": None,
                "release_date": "2000",
                "album_image_url": None,
                "track_durations": {},
                "provider": None,
                "provider_album_id": None,
                "provider_url": None,
            }
        ]
    )

    assert await batch_lookup_metadata(mock_conn, [("a", "b")]) == {}


@pytest.mark.asyncio
async def test_batch_persist_metadata_writes_a_deezer_album_without_a_spotify_id():
    """A Deezer album persists its own id and link in the provider columns and
    leaves the legacy spotify_id column NULL."""
    mock_conn = AsyncMock()
    albums = {("grey orton", "rumours"): deezer_metadata("6237061", "1977-02-04")}

    await batch_persist_metadata(mock_conn, albums)

    mock_conn.execute.assert_awaited_once()
    call_args = mock_conn.execute.call_args[0]
    sql = call_args[0]
    assert "provider" in sql
    assert "provider_album_id" in sql
    assert "provider_url" in sql
    assert call_args[3] == [None]  # spotify_id
    assert call_args[7] == ["deezer"]
    assert call_args[8] == ["6237061"]
    assert call_args[9] == ["https://www.deezer.com/album/6237061"]


@pytest.mark.asyncio
async def test_batch_persist_metadata_writes_a_spotify_id_to_both_columns():
    """A Spotify album's id goes to spotify_id and provider_album_id, and its
    link is stored rather than left NULL."""
    mock_conn = AsyncMock()
    albums = {("artist1", "album1"): spotify_metadata("sp1")}

    await batch_persist_metadata(mock_conn, albums)

    call_args = mock_conn.execute.call_args[0]
    assert call_args[3] == ["sp1"]
    assert call_args[7] == ["spotify"]
    assert call_args[8] == ["sp1"]
    assert call_args[9] == ["https://open.spotify.com/album/sp1"]
```

(`test_cache.py`'s other tests, for original-release rows and the stale-schema helpers, are unchanged.)

**`tests/test_repositories.py`.** Add `from tests.album_metadata import spotify_metadata` to the imports. In `test_batch_lookup_metadata_parses_track_durations` change the final assertions to

```python
    album = result[("radiohead", "ok computer")]
    assert album.track_durations == {"paranoid android": 383, "karma police": 264}
```

In `test_batch_persist_metadata_empty_rows` call `await batch_persist_metadata(mock_conn, {})` and change `WHEN`/`THEN` wording from "rows" to "albums". Replace the `rows = [...]` list in `test_batch_persist_metadata_upsert_call_shape` and its call with:

```python
    albums = {
        ("artist1", "album1"): spotify_metadata(
            "sp1", "2025-01-01", "https://img/1.jpg", {"track a": 200}
        ),
        ("artist2", "album2"): spotify_metadata("sp2", "2024-06-15", None, {}),
    }

    await batch_persist_metadata(mock_conn, albums)
```

(the assertions below it, on the array parameters, stay as they are).

**`tests/services/test_orchestrator_process_albums.py`.** Add `from tests.album_metadata import spotify_metadata` to the imports. Edit by test name:

- `test_process_albums_cache_hit_skips_spotify` and `test_process_albums_partial_cache_token_failure_uses_cached_results`: replace the `mock_cached = {... {"spotify_id": "abc123", ...}}` dict with
  `mock_cached = {("radiohead", "ok computer"): spotify_metadata("abc123", "1997-06-16", "https://img.example.com/ok.jpg", {"paranoid android": 383, "karma police": 264})}`.
- `test_process_albums_applies_cached_original_release_before_filtering` and `test_process_albums_records_provider_date_on_an_uncorrected_exclusion`: replace `cached_metadata = {album_key: {...}}` with
  `cached_metadata = {album_key: spotify_metadata("sp-rumours", "2011-01-31", "https://img.example.com/rumours.jpg", {"dreams": 257})}`.
- `test_process_albums_cache_miss_fetches_and_persists`: replace the `persist_rows` assertions with
  ```python
      mock_persist.assert_awaited_once()
      persisted = mock_persist.call_args[0][1]
      assert list(persisted) == [("artist", "album")]
      assert persisted[("artist", "album")].album_id == "sp1"
  ```
- `test_process_albums_deezer_row_persists_provider_fields`: replace everything after `mock_persist.assert_awaited_once()` with
  ```python
      persisted = mock_persist.call_args[0][1]
      assert persisted == {
          ("artist", "album"): AlbumMetadata(
              provider="deezer",
              album_id="dz1",
              url="https://www.deezer.com/album/dz1",
              release_date="2025-02-02",
              image_url="https://cdn.example/dz.jpg",
              track_durations={"t1": 200},
          )
      }
      assert persisted[("artist", "album")].spotify_id is None
  ```
- `test_process_albums_persists_a_spotify_row_through_the_contract`: replace its `(row,) = ...; assert row == (...)` tail with
  ```python
      mock_persist.assert_awaited_once()
      assert mock_persist.call_args[0][1] == {
          ("artist", "album"): AlbumMetadata(
              provider="spotify",
              album_id="sp1",
              url="https://open.spotify.com/album/sp1",
              release_date="2025-01-01",
              image_url="https://img.example.com/a.jpg",
              track_durations={normalize_track_name("Track One"): 240},
          )
      }
  ```
  and change its docstring's "nine-element form" to "provider record, so the Spotify URL is stored rather than left NULL (F-B22-7)".

**`tests/services/test_orchestrator_helpers.py`.** Add `from tests.album_metadata import spotify_metadata`. Replace the three `"cached": {...}` dicts:

- in `test_build_results_zero_playtime_no_division_error`: `"cached": spotify_metadata("sp1", "2025-01-01", "https://img.example.com/a.jpg", {}),`, and change its docstring's last sentence to "An album with no durations gives play_time_seconds=0 rather than a TypeError."
- in `_corrected_cache_hits`: `"cached": spotify_metadata("sp1", provider_release_date, "https://img.example.com/a.jpg", {}),`
- in `test_build_results_records_reason_code`: `"cached": spotify_metadata("sp1", "2018-01-01", "https://img.example.com/a.jpg", {}),`

Append one new test:

```python
def test_a_cached_album_with_no_link_has_a_null_album_url():
    """An album whose record holds an empty link is listed with album_url null,
    as the page and the JSON have always had it, not with an empty string."""
    job_id = jobs.create(TEST_JOB_PARAMS)
    album = AlbumMetadata(
        provider="deezer",
        album_id="9",
        url="",
        release_date="2025-01-01",
        image_url=None,
        track_durations={},
    )
    cache_hits = {
        ("artist", "album"): {
            "cached": album,
            "original": {
                "play_count": 20,
                "track_counts": {"song a": 5},
                "original_artist": "Artist",
                "original_album": "Album",
            },
        }
    }

    (row,) = _build_results(
        cache_hits, job_id, year=2025, sort_mode="playcount", release_scope="same"
    )

    assert row["album_url"] is None
```

(add `from scrobblescope.enrichment import AlbumMetadata` to the file's imports).

**`tests/services/test_orchestrator_fetch_spotify.py`.** Add `from scrobblescope.enrichment import AlbumMetadata` to the imports. Replace the helper `_deezer_metadata(key)` with

```python
def _deezer_metadata():
    """The Deezer album every fake Deezer lookup in this file returns."""
    return AlbumMetadata(
        provider="deezer",
        album_id="9",
        url="u",
        release_date="2020-01-01",
        image_url="img",
        track_durations={"t": 1},
    )
```

and in `test_deezer_throttling_degrades_and_records_the_album_as_unavailable`, which builds its own `MagicMock` metadata (`metadata = MagicMock(... provider="deezer" ...)` followed by `metadata.as_cache_row.return_value = ("found", "alb")`), delete the `MagicMock` block and the `as_cache_row` line and write `metadata = _deezer_metadata()`; its assertion `assert rows == [("found", "alb")]` becomes `assert rows == {("found", "alb"): metadata}`. Then, with `git grep -n "as_cache_row\|rows ==\|new_rows\|_deezer_metadata(" tests/services/test_orchestrator_fetch_spotify.py` as the worklist, apply:

- every `_deezer_metadata(("found", "album"))` becomes `_deezer_metadata()`;
- every `assert rows == [("found", "album")]` or `[("found", "alb")]` becomes `assert rows == {("found", "album"): _deezer_metadata()}` (and `"alb"` for the one test that uses it);
- every `assert rows == [] and hits == {}` becomes `assert rows == {} and hits == {}`;
- in the malformed-details test (`new_rows = await _fetch_spotify_misses(...)`): `promoted = cache_hits[("artist1", "album1")]["cached"]` then `assert promoted.track_durations == {}` and `assert promoted.spotify_id == "sp1"`, and replace the last two assertions with `assert list(new_rows) == [("artist1", "album1")]` and `assert new_rows[("artist1", "album1")].album_id == "sp1"`;
- `assert len(rows) == 1` stays (a dict has a length).

**`tests/services/test_failure_logging.py`.** In `_database_site`, the `metadata_persist` site passes `[("row",)]`: change it to `{("a", "b"): spotify_metadata()}` and add `from tests.album_metadata import spotify_metadata` to the file's imports. Nothing else in this file names an encoding.

- [ ] **Step 3: Run the edited tests; they fail**

Run: `"$PY" -m pytest tests/services tests/test_repositories.py -q -p no:cacheprovider -x`
Expected: FAIL, first on an `AttributeError`/`TypeError` that shows a dict or tuple where an `AlbumMetadata` is now expected.

- [ ] **Step 4: Change the cache module**

In `scrobblescope/cache.py` add `from scrobblescope.enrichment import AlbumMetadata` to the imports (after `from scrobblescope.config import ...`). Replace `batch_lookup_metadata` and `batch_persist_metadata` (their SQL text is unchanged) with:

```python
async def batch_lookup_metadata(conn, keys):
    """Look up cached album metadata for a batch of (artist_norm, album_norm) keys.

    Executes a single SELECT using unnest() for efficient batch lookup.
    Only rows updated within the configured TTL are returned.
    Returns a dict keyed by (artist_norm, album_norm) with ``AlbumMetadata``
    values. ``AlbumMetadata.from_row`` owns how a stored row is read, rows
    older than the provider columns included; a row that names no provider
    album is left out, so it is a miss and the next fetch overwrites it.
    """
    if not keys:
        return {}
    artists = [k[0] for k in keys]
    albums = [k[1] for k in keys]
    rows = await conn.fetch(
        """
        SELECT artist_norm, album_norm, spotify_id, release_date,
               album_image_url, track_durations, provider, provider_album_id,
               provider_url
        FROM spotify_cache
        WHERE (artist_norm, album_norm) IN (
            SELECT unnest($1::text[]), unnest($2::text[])
        )
        AND updated_at > NOW() - make_interval(days => $3)
        """,
        artists,
        albums,
        METADATA_CACHE_TTL_DAYS,
    )
    result = {}
    for r in rows:
        metadata = AlbumMetadata.from_row(r)
        if metadata is not None:
            result[(r["artist_norm"], r["album_norm"])] = metadata
    return result
```

```python
async def batch_persist_metadata(conn, albums):
    """Persist newly fetched album metadata in a single INSERT statement.

    *albums* maps (artist_norm, album_norm) to the ``AlbumMetadata`` a provider
    returned. This is the only statement that writes ``spotify_cache``, and
    ``AlbumMetadata`` has no field a listening fact could travel in, so the
    shared table's contract (BATCH23 "Data handling": no listening facts, no
    link to a listener) is held by the type. Uses INSERT ... SELECT FROM
    unnest() with ON CONFLICT DO UPDATE (upsert). The legacy ``spotify_id``
    column takes the album id for a Spotify album and NULL for any other
    provider; ``provider_album_id`` always takes the id the provider issued.
    """
    if not albums:
        return
    keys = list(albums)
    metadata = [albums[key] for key in keys]
    artists = [key[0] for key in keys]
    album_norms = [key[1] for key in keys]
    spotify_ids = [m.spotify_id for m in metadata]
    release_dates = [m.release_date for m in metadata]
    image_urls = [m.image_url for m in metadata]
    track_durations_json = [
        json.dumps(m.track_durations) if m.track_durations else "{}" for m in metadata
    ]
    providers = [m.provider for m in metadata]
    provider_album_ids = [m.album_id for m in metadata]
    provider_urls = [m.url for m in metadata]
    await conn.execute(
        """
        INSERT INTO spotify_cache
            (artist_norm, album_norm, spotify_id, release_date,
             album_image_url, track_durations, provider, provider_album_id,
             provider_url)
        SELECT * FROM unnest(
            $1::text[], $2::text[], $3::text[], $4::text[],
            $5::text[], $6::jsonb[], $7::text[], $8::text[], $9::text[]
        )
        ON CONFLICT (artist_norm, album_norm) DO UPDATE SET
            spotify_id        = EXCLUDED.spotify_id,
            release_date      = EXCLUDED.release_date,
            album_image_url   = EXCLUDED.album_image_url,
            track_durations   = EXCLUDED.track_durations,
            provider          = EXCLUDED.provider,
            provider_album_id = EXCLUDED.provider_album_id,
            provider_url      = EXCLUDED.provider_url,
            updated_at        = NOW()
        """,
        artists,
        album_norms,
        spotify_ids,
        release_dates,
        image_urls,
        track_durations_json,
        providers,
        provider_album_ids,
        provider_urls,
    )
```

In `scrobblescope/enrichment.py` delete the `as_cache_row` method (and, if nothing else uses it, nothing else changes: `json`, `Mapping`, `Any` stay for `from_row`).

- [ ] **Step 5: Change the orchestrator phases**

`scrobblescope/orchestrator/_details.py`: in `_run_spotify_batch_detail_phase`, change the docstring sentence "Promotes enriched albums into cache_hits (mutated in place). Returns new_metadata_rows." to "Promotes enriched albums into cache_hits (mutated in place). Returns the newly fetched metadata as ``{(artist_norm, album_norm): AlbumMetadata}``, for persistence."; replace `new_metadata_rows = []` (just after the docstring) with `new_metadata = {}`; and replace the loop's tail (from `metadata = _orchestrator.album_metadata_from_details(...)` to the end of the function) with:

```python
        metadata = _orchestrator.album_metadata_from_details(spotify_id, album_details)

        cache_hits[key] = {"cached": metadata, "original": original_data}
        new_metadata[key] = metadata

    return new_metadata
```

`scrobblescope/orchestrator/_deezer_fallback.py`: in `_run_deezer_fallback_phase` change the docstring's "Returns new_metadata_rows for the newly matched Deezer albums." to "Returns the newly matched Deezer albums as ``{(artist_norm, album_norm): AlbumMetadata}``."; `if not misses: return []` becomes `return {}`; `new_metadata_rows = []` becomes `new_metadata = {}`; the `if metadata is not None:` branch becomes

```python
            if metadata is not None:
                matched_count += 1
                cache_hits[key] = {"cached": metadata, "original": data}
                new_metadata[key] = metadata
```

and the final `return new_metadata_rows` becomes `return new_metadata`.

`scrobblescope/orchestrator/__init__.py`: in `_fetch_spotify_misses` change the docstring's "Returns a list of new_metadata_rows tuples for DB persistence." to "Returns the newly fetched metadata as ``{(artist_norm, album_norm): AlbumMetadata}`` for DB persistence."; `return []` (no misses) becomes `return {}`; `new_metadata_rows = []` becomes `new_metadata = {}`; `new_metadata_rows = await _run_spotify_batch_detail_phase(` becomes `new_metadata = await _run_spotify_batch_detail_phase(`; `deezer_rows = await _run_deezer_fallback_phase(` becomes `deezer_metadata = await _run_deezer_fallback_phase(` and `new_metadata_rows.extend(deezer_rows)` becomes `new_metadata.update(deezer_metadata)`; `not new_metadata_rows` becomes `not new_metadata`; the last line returns `new_metadata`. In `process_albums` change the partition comment to `cache_hits = {}  # key -> {"cached": AlbumMetadata, "original": original_data}`, `new_metadata_rows = await _fetch_spotify_misses(` to `new_metadata = await _fetch_spotify_misses(`, and `await _persist_new_metadata(conn, job_id, new_metadata_rows)` to `await _persist_new_metadata(conn, job_id, new_metadata)`.

`scrobblescope/orchestrator/_cache.py`: replace `_persist_new_metadata` with

```python
async def _persist_new_metadata(conn, job_id, new_metadata):
    """DB Batch Persist. Non-fatal on failure.

    *new_metadata* maps (artist_norm, album_norm) to the ``AlbumMetadata`` the
    providers returned this job.
    """
    if not (conn and new_metadata):
        return
    try:
        await _orchestrator.batch_persist_metadata(conn, new_metadata)
        jobs.record_stat(job_id, "db_cache_persisted", len(new_metadata))
        logging.info(f"Persisted {len(new_metadata)} new metadata rows to DB cache")
    # Fail open: a failed persist costs the next job a lookup, not this one.
    except Exception:  # noqa: BLE001
        log_failure("DB persist failed (non-fatal)", logging.WARNING)
        jobs.record_stat(job_id, "db_cache_warning", "DB persist failed.")
```

and change `_lookup_cached_metadata`'s docstring to say it returns `{key: AlbumMetadata}`.

- [ ] **Step 6: Change the results builder**

`scrobblescope/orchestrator/_results.py`: delete the functions `_album_provider` and `_album_url`. In `_build_results` replace the loop head and the two row builders as follows (everything not shown is unchanged):

```python
    for key, entry in cache_hits.items():
        metadata = entry["cached"]
        original_data = entry["original"]

        provider_release_date = metadata.release_date
```

In `unmatched_entry` use

```python
                "album_image": metadata.image_url,
                "spotify_id": metadata.spotify_id,
                "provider": metadata.provider,
                # An empty link is no link: the page tests it for truth and
                # the JSON has always said null.
                "album_url": metadata.url or None,
```

then `track_durations = metadata.track_durations`, and in `result`

```python
            "album_image": metadata.image_url,
            "spotify_id": metadata.spotify_id,
            "provider": metadata.provider,
            "album_url": metadata.url or None,
```

- [ ] **Step 7: Run the suite**

Run: `"$PY" -m pytest tests/test_album_cache_parity.py tests/services tests/test_repositories.py tests/test_pipeline_integration.py -q -p no:cacheprovider`
Expected: all pass. Task 1's tests passing unchanged is the parity proof: `git diff HEAD --stat -- tests/test_album_cache_parity.py tests/fake_postgres.py` shows nothing.

Run: `"$PY" -m pytest -q -p no:cacheprovider`
Expected: all pass. N equals the count after Task 2 (five `test_cache.py` tests replace four, one null-link test is new, two `as_cache_row` tests are deleted); measure it, do not predict, and use bare `--fix` if it is unchanged.

Sweep: `git grep -nE "as_cache_row|_album_provider|_album_url|new_metadata_rows|persist_rows" -- scrobblescope tests scripts ':!docs'`
Expected: no output.

- [ ] **Step 8: Docs follow the code**

`.claude/SESSION_CONTEXT.md` Section 4: change `cache.py         <- config, utils` to `cache.py         <- config, enrichment, utils`.

`docs/architecture/runtime-system.md`: in the Mermaid block add the edge `    Cache --> Enrichment` directly after `    Cache --> Utils`. Render the edited block with the Mermaid validator tool (`validate_and_render_mermaid_diagram`) and fix any error before committing. The "eleven nodes import config" paragraph stays true; say in the Section 4 entry that the count was re-checked with an `ast` walk.

`docs/agents/FINDINGS.md`, F-B23-32: replace "`_results.py` `_album_url`" in its first sentence with "`enrichment.py` `AlbumMetadata.from_row` (the one place a cached link enters), `_results.py`". Its status stays open.

- [ ] **Step 9: Mutation evidence**

Apply one at a time in a scratch copy of the tree (or copy the file aside, plant, run, copy it back; never `git checkout -- <file>`, the file holds this task's uncommitted work), run the named tests, confirm failure, restore and confirm they pass.

| # | Planted defect | File | Test that must fail |
|---|---|---|---|
| 1 | `spotify_ids = [m.album_id for m in metadata]` | `scrobblescope/cache.py` | `test_a_deezer_album_is_stored_without_a_spotify_id_and_a_repeat_search_matches_it`, `test_batch_persist_metadata_writes_a_deezer_album_without_a_spotify_id` |
| 2 | swap `provider_album_ids` and `provider_urls` in the `conn.execute` arguments | `scrobblescope/cache.py` | `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it`, `test_batch_persist_metadata_writes_a_spotify_id_to_both_columns` |
| 3 | delete `if metadata is not None:` (keep the assignment) | `scrobblescope/cache.py` | `test_a_row_naming_no_provider_album_is_a_cache_miss` |
| 4 | `"album_url": metadata.image_url` in the result row | `scrobblescope/orchestrator/_results.py` | `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` |
| 5 | `"album_url": metadata.url` (drop `or None`) in the result row | `scrobblescope/orchestrator/_results.py` | `test_a_cached_album_with_no_link_has_a_null_album_url` |
| 6 | delete the line `new_metadata[key] = metadata` | `scrobblescope/orchestrator/_details.py` | `test_a_spotify_album_is_stored_as_album_facts_and_a_repeat_search_matches_it` (nothing stored, so the repeat search calls a provider) |
| 7 | delete `new_metadata.update(deezer_metadata)` | `scrobblescope/orchestrator/__init__.py` | `test_a_deezer_album_is_stored_without_a_spotify_id_and_a_repeat_search_matches_it`, `test_spotify_search_outage_degrades_to_deezer_and_lists_the_rest_as_unavailable` |
| 8 | in `batch_lookup_metadata`, replace `AlbumMetadata.from_row(r)` with `AlbumMetadata.from_row({"spotify_id": r["spotify_id"], "release_date": r["release_date"], "album_image_url": r["album_image_url"], "track_durations": r["track_durations"]})` (drop the three provider columns) | `scrobblescope/cache.py` | `test_batch_lookup_metadata_returns_albums_with_their_provider_columns` |
| 9 | in `batch_lookup_metadata`'s SELECT list, delete `provider_url` | `scrobblescope/cache.py` | `test_batch_lookup_metadata_returns_albums_with_their_provider_columns` (the SQL assertion) |
| 10 | in `batch_lookup_metadata`, replace `AlbumMetadata.from_row(r)` with `AlbumMetadata.from_row({**r, "provider": r["provider"]})` (a pre-provider row has no such column) | `scrobblescope/cache.py` | `test_batch_lookup_metadata_reads_a_pre_provider_row_as_a_spotify_album` |

- [ ] **Step 10: Section 4 entry, gates, commit**

Entry heading: `### <commit date> - Album metadata is one record from provider to results`. Body: scope (cache, three phases, results builder, seven test files); why (B-5: nine-tuple, 4-key and 7-key dicts, 7-key cache dict, two repair functions, a six-tuple branch that only a test reached); owner intent (card B-5 and the Task 27 brief: "one `AlbumMetadata.from_row` ... replaces ... `_album_provider` and `_album_url` delete"); what changed; deviations (a live Spotify result now shows the link Spotify returned in `external_urls.spotify` rather than a rebuilt classic link: the same string in practice; a stored row naming no provider album is a miss; `cache_hits[key]["cached"]` keeps its key name though it now also holds live fetches); the first view of a search now renders the provider-supplied URL (`external_urls.spotify`) where it used to render a constructed one, so F-B23-32's exposure to unchecked provider URLs widens slightly (the finding is edited in this commit); the Task 1 tests unchanged and passing; the ten mutation rows; the Validation line (R4 form).
Commit body names every edited existing test file: `tests/services/test_enrichment.py` (two `as_cache_row` tests deleted, replaced by Task 1's stored-column tests and Task 3's persist tests), `tests/services/test_cache.py` (four tests replaced; the six-tuple test is deleted because no caller builds a six-tuple, its legacy-row rule now lives in `from_row`), `tests/test_repositories.py`, `tests/services/test_orchestrator_process_albums.py` (four fixtures, three persist assertions), `tests/services/test_orchestrator_helpers.py` (three fixtures, one new test), `tests/services/test_orchestrator_fetch_spotify.py` (return type of the phases), `tests/services/test_failure_logging.py` (one argument).
Subject: `refactor(cache): Store and read album metadata as one record` (60 characters).

---
### Task 4: Let the cache own its connection and failures

**Touches:** `scrobblescope/cache.py`, `scrobblescope/orchestrator/__init__.py`, `scrobblescope/orchestrator/_cache.py`, `tests/services/test_cache.py`, `tests/services/test_orchestrator_process_albums.py`, `tests/services/test_orchestrator_helpers.py`, `tests/services/test_orchestrator_fetch_spotify.py` (patch strings only), `tests/services/test_failure_logging.py`, `tests/test_pipeline_integration.py` (patch strings only), `tests/test_module_boundaries.py` (one test), `.claude/SESSION_CONTEXT.md`, `docs/architecture/runtime-system.md`, `docs/architecture/top-albums-sequence.md`, `BATCH23_DEFINITION.md`, `docs/agents/FINDINGS.md`, `docs/agents/PLAYBOOK.md`.
**After:** Task 3 (shares `cache.py`, `orchestrator/_cache.py`, `orchestrator/__init__.py`).

**Files:**
- Modify: the files above (no new file)

**Interfaces:**
- Consumes: Task 3's `batch_lookup_metadata(conn, keys) -> {key: AlbumMetadata}` and `batch_persist_metadata(conn, {key: AlbumMetadata})`; the existing `get_db_connection`, `cleanup_stale_metadata`, `batch_lookup_original_release`, `schema_is_out_of_date`, `SCHEMA_OUT_OF_DATE_REMEDIATION`, `log_failure`; Task 1's `fake_postgres`; Task 3's `tests.album_metadata`.
- Produces (Batch 23 WP-3's export job reaches the cache only through `process_albums`, which uses exactly these):
  - `cache.AlbumCache(conn)`: `enabled` (property, True when a connection is open), `lookup_failed` and `persist_failed` (bool attributes, False until that operation fails), `async lookup(keys) -> dict[key, AlbumMetadata]` (reads, then runs the stale-row cleanup; `{}` when disabled or on failure), `async persist(albums)` (one upsert; a no-op when disabled or `albums` is empty), `async lookup_original_releases(keys) -> dict` (`{}` when disabled or on failure), `async close()` (closes at most once; a failure is logged, never raised).
  - `cache.open_album_cache()`: an async context manager that opens the connection through `get_db_connection()` (so `DATABASE_URL`, retries and the connect timeout are unchanged), yields an `AlbumCache` (disabled when no connection could be had) and closes it when the block ends, however it ends.
  - `orchestrator._lookup_cached_metadata(album_cache, job_id, album_keys)` and `_persist_new_metadata(album_cache, job_id, new_metadata)`: the same job stats and log lines as before, now fed by the cache's flags.
  - Deleted: `orchestrator._lookup_cached_original_release` (its body is `AlbumCache.lookup_original_releases`); the orchestrator facade no longer imports `get_db_connection`, `batch_lookup_metadata`, `batch_persist_metadata`, `batch_lookup_original_release` or `cleanup_stale_metadata`.

Why: F-B23-3. `process_albums` opens the connection, holds it across provider work and closes it in a `finally` that does not guard `close()`; `orchestrator/_cache.py` owns the failure policy and writes job warnings. "The cache is optional" takes both modules to understand, a failing `close()` fails the job, and the connection-closure test has to configure the provider machinery. The cache module takes the operation: open, use, close, and what an error means. The job-facing messages stay with the caller, as the finding asks. The correction worker keeps its own connection and policy (the finding: "Metadata and release-check cache policy stay separate").

- [ ] **Step 1: Write the failing tests**

**`tests/services/test_cache.py`.** Add to its imports `import logging`, `from unittest.mock import AsyncMock, patch` (extend the existing `unittest.mock` import), `from scrobblescope.cache import AlbumCache, open_album_cache` (extend the existing `scrobblescope.cache` import) and `from tests.fake_postgres import fake_postgres`. Append:

```python
KEY = ("radiohead", "ok computer")
MARKER = "secret-marker-do-not-log"


@pytest.mark.asyncio
async def test_a_cache_with_no_database_does_nothing_and_fails_nothing():
    """
    GIVEN no DATABASE_URL
    WHEN every operation runs
    THEN each returns its empty answer, nothing connects, and no failure is
    flagged: a missing cache is not an error.
    """
    with fake_postgres(url=None) as db:
        async with open_album_cache() as album_cache:
            assert album_cache.enabled is False
            assert await album_cache.lookup([KEY]) == {}
            await album_cache.persist({KEY: spotify_metadata()})
            assert await album_cache.lookup_original_releases([KEY]) == {}

    assert (album_cache.lookup_failed, album_cache.persist_failed) == (False, False)
    assert db.connect_attempts == 0
    assert db.statements == []


@pytest.mark.asyncio
@pytest.mark.parametrize("block_raises", [False, True])
async def test_the_connection_closes_once_however_the_block_ends(block_raises):
    """The block's own failure (a provider outage, say) still closes the
    connection, and a normal exit closes it once."""
    with fake_postgres() as db:
        try:
            async with open_album_cache():
                if block_raises:
                    raise RuntimeError("a provider failed")
        except RuntimeError:
            assert block_raises

    assert (db.connect_attempts, db.closes) == (1, 1)


@pytest.mark.asyncio
async def test_a_failing_close_is_logged_by_class_and_never_raised(caplog):
    """
    GIVEN a connection whose close() raises
    WHEN the block ends
    THEN nothing is raised (the job's work is done and its results are built),
    and the log names the exception class, not its text.
    """
    with fake_postgres() as db:

        async def broken_close():
            raise RuntimeError(MARKER)

        db.close = broken_close
        with caplog.at_level(logging.WARNING):
            async with open_album_cache():
                pass

    assert "Closing the cache DB connection failed" in caplog.text
    assert "RuntimeError" in caplog.text
    assert MARKER not in caplog.text


@pytest.mark.asyncio
async def test_a_failed_read_is_a_miss_and_a_failed_write_is_not_an_error():
    """
    GIVEN the metadata read and the metadata write both fail
    WHEN the cache is used
    THEN the read answers {}, the write returns, and each failure is flagged
    for the caller to report.
    """
    with fake_postgres() as db:
        db.fail("SELECT", "spotify_cache", OSError("down"))
        db.fail("INSERT", "spotify_cache", OSError("down"))
        async with open_album_cache() as album_cache:
            assert await album_cache.lookup([KEY]) == {}
            await album_cache.persist({KEY: spotify_metadata()})

    assert album_cache.lookup_failed is True
    assert album_cache.persist_failed is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "album",
    [
        spotify_metadata("sp1", "1997-06-16", "https://img.example.com/ok.jpg", {"a": 1}),
        deezer_metadata("6237061", "1977-02-04"),
        spotify_metadata("sp2", "2001-01-01", None, {}),
    ],
    ids=["spotify", "deezer", "spotify_without_cover_or_durations"],
)
async def test_what_persist_writes_lookup_reads_back(album):
    """Every provider's album survives the cache unchanged, and a healthy cache
    flags no failure."""
    with fake_postgres():
        async with open_album_cache() as album_cache:
            await album_cache.persist({KEY: album})
            assert await album_cache.lookup([KEY]) == {KEY: album}

    assert (album_cache.lookup_failed, album_cache.persist_failed) == (False, False)


@pytest.mark.asyncio
async def test_a_stored_row_naming_no_provider_album_is_a_miss_not_an_album():
    """A row with no provider and no album id is left out of a lookup."""
    with fake_postgres() as db:
        db.seed_metadata(*KEY, release_date="1997", provider=None, spotify_id=None)
        async with open_album_cache() as album_cache:
            assert await album_cache.lookup([KEY]) == {}


@pytest.mark.asyncio
async def test_original_release_lookup_without_a_connection_skips_the_query():
    """No DB connection means no correction lookup and an empty result."""
    with patch(
        "scrobblescope.cache.batch_lookup_original_release", new_callable=AsyncMock
    ) as mock_lookup:
        result = await AlbumCache(None).lookup_original_releases([("artist", "album")])

    assert result == {}
    mock_lookup.assert_not_awaited()


@pytest.mark.asyncio
async def test_original_release_lookup_failure_is_non_fatal(caplog):
    """A correction-cache failure is logged and cannot block album results."""
    with (
        caplog.at_level(logging.WARNING),
        patch(
            "scrobblescope.cache.batch_lookup_original_release",
            new_callable=AsyncMock,
            side_effect=RuntimeError("database unavailable"),
        ),
    ):
        result = await AlbumCache(AsyncMock()).lookup_original_releases(
            [("artist", "album")]
        )

    assert result == {}
    assert "Original-release cache lookup failed (non-fatal): RuntimeError" in (
        caplog.text
    )
    assert "database unavailable" not in caplog.text
```

**`tests/services/test_orchestrator_process_albums.py`.** Append:

```python
@pytest.mark.asyncio
async def test_process_albums_survives_a_connection_that_fails_to_close():
    """
    GIVEN a cache connection whose close() raises
    WHEN process_albums has built its results
    THEN it returns them: the cache is optional at runtime, so closing it must
    not fail a job whose work is done.
    """
    job_id = jobs.create(TEST_JOB_PARAMS)
    key = ("radiohead", "ok computer")
    filtered = {
        key: {
            "play_count": 50,
            "track_counts": {"paranoid android": 10},
            "original_artist": "Radiohead",
            "original_album": "OK Computer",
        }
    }
    mock_conn = AsyncMock()
    mock_conn.close = AsyncMock(side_effect=RuntimeError("close failed"))

    with (
        patch(
            "scrobblescope.cache.get_db_connection",
            new_callable=AsyncMock,
            return_value=mock_conn,
        ),
        patch(
            "scrobblescope.cache.batch_lookup_metadata",
            new_callable=AsyncMock,
            return_value={
                key: spotify_metadata(
                    "abc123", "2025-01-01", None, {"paranoid android": 383}
                )
            },
        ),
        patch(
            "scrobblescope.cache.batch_lookup_original_release",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        results = await process_albums(job_id, filtered, 2025, "playcount", "same")

    assert [row["spotify_id"] for row in results] == ["abc123"]
    mock_conn.close.assert_awaited_once()
```

**`tests/test_module_boundaries.py`** (PR #4's file; it defines `SRC` and `_module_name`, checked in Step 2 below). Append:

```python
METADATA_CACHE_FUNCTIONS = frozenset(
    {"batch_lookup_metadata", "batch_persist_metadata", "cleanup_stale_metadata"}
)


def test_only_the_cache_module_reads_or_writes_the_metadata_table():
    """
    GIVEN every module under scrobblescope/
    WHEN its imports, attribute reads and string constants are walked
    THEN no module but cache.py names the metadata table's read, write or
    cleanup functions, and exactly one module holds an INSERT into it.

    The shared table's contract (no listening facts) is held by one write
    path: ``AlbumCache.persist`` taking ``AlbumMetadata``. A second writer
    would be a second place to inspect.

    Planted defect: add ``from scrobblescope.cache import batch_persist_metadata``
    to ``release_checks.py``; the test names it.
    """
    offenders = []
    writers = []
    for path in sorted(SRC.rglob("*.py")):
        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if module != "scrobblescope.cache":
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module == "scrobblescope.cache"
                ):
                    offenders += [
                        f"{module} imports {item.name}"
                        for item in node.names
                        if item.name in METADATA_CACHE_FUNCTIONS
                    ]
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr in METADATA_CACHE_FUNCTIONS
                ):
                    offenders.append(f"{module} reads .{node.attr}")
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "INSERT INTO spotify_cache" in node.value
            ):
                writers.append(module)
    assert offenders == []
    assert writers == ["scrobblescope.cache"]
```

**`tests/services/test_failure_logging.py`.** In `_database_site`: delete `from scrobblescope import orchestrator as orch` and add `from scrobblescope.cache import AlbumCache` to the function's imports (or the file's); replace `def metadata_lookup():` with

```python
    def metadata_lookup():
        # AsyncMock: the stale-row cleanup that follows must succeed.
        return AlbumCache(AsyncMock()).lookup([("a", "b")])
```

and the four `sites` entries `metadata_lookup`, `metadata_lookup_schema`, `metadata_persist`, `correction_lookup` with:

```python
        "metadata_lookup": (
            patched(cache, "batch_lookup_metadata"),
            metadata_lookup,
            ["DB lookup failed, proceeding without cache"],
            "RuntimeError",
        ),
        "metadata_lookup_schema": (
            patched(cache, "batch_lookup_metadata", _SchemaError(MARKER)),
            metadata_lookup,
            ["DB lookup failed, proceeding without cache" + _remedy()],
            "_SchemaError",
        ),
        "metadata_persist": (
            patched(cache, "batch_persist_metadata"),
            lambda: AlbumCache(MagicMock()).persist({("a", "b"): spotify_metadata()}),
            ["DB persist failed (non-fatal)"],
            "RuntimeError",
        ),
        "correction_lookup": (
            patched(cache, "batch_lookup_original_release"),
            lambda: AlbumCache(MagicMock()).lookup_original_releases([("a", "b")]),
            ["Original-release cache lookup failed (non-fatal)"],
            "RuntimeError",
        ),
```

(The `site` list of `test_fail_open_database_sites_log_the_class_only_at_warning` needs no new entry: no site is added. The `release_check_*` sites that patch `release_checks`'s own names are unchanged.)

- [ ] **Step 2: Run them; they fail**

Run: `git grep -n "^SRC\|^def _module_name" -- tests/test_module_boundaries.py` (both must exist; if not, stop: PR #4's guard file differs from this plan).
Run: `"$PY" -m pytest tests/services/test_cache.py tests/services/test_failure_logging.py tests/test_module_boundaries.py -q -p no:cacheprovider`
Expected: FAIL: `ImportError: cannot import name 'AlbumCache'`.

- [ ] **Step 3: Implement the cache's operation**

In `scrobblescope/cache.py` add `from contextlib import asynccontextmanager` to the imports (standard library group, alphabetical). Append, after `batch_persist_original_release`:

```python
class AlbumCache:
    """One job's use of the shared album cache, and what its failures mean.

    The cache is optional at runtime (BATCH23 / the hosting cost ceiling): a
    missing, sleeping or failing database never fails a job. This class is the
    one place that says so. Every operation answers with an empty value instead
    of raising, and records which operation failed in ``lookup_failed`` and
    ``persist_failed`` so the caller can tell the job (job messages stay with
    the caller). It issues the same statements the pipeline always did, on the
    one connection ``open_album_cache`` opened: it never reconnects and never
    retries a statement.

    Build one with ``open_album_cache``; the constructor takes the connection
    (or None for a disabled cache) so tests can hand it a fake.
    """

    def __init__(self, conn):
        self._conn = conn
        self.lookup_failed = False
        self.persist_failed = False

    @property
    def enabled(self):
        """True while a database connection is open."""
        return self._conn is not None

    async def lookup(self, keys):
        """Return cached ``AlbumMetadata`` for *keys*, then clear stale rows.

        Returns {} when the cache is disabled or the read fails (every album is
        then a miss and the providers answer). A schema that is out of date
        gets its own remediation text: until it is fixed every read misses.
        The stale-row cleanup runs after the read whether or not it succeeded.
        """
        if self._conn is None:
            return {}
        try:
            hits = await batch_lookup_metadata(self._conn, keys)
        # Fail open: a failed cache read makes every album a miss, not a failed job.
        except Exception as exc:  # noqa: BLE001
            self.lookup_failed = True
            if schema_is_out_of_date(exc):
                log_failure(
                    "DB lookup failed, proceeding without cache "
                    f"({SCHEMA_OUT_OF_DATE_REMEDIATION})",
                    logging.WARNING,
                )
            else:
                log_failure(
                    "DB lookup failed, proceeding without cache", logging.WARNING
                )
            hits = {}
        # Opportunistic stale-row cleanup -- non-fatal, errors swallowed inside.
        await cleanup_stale_metadata(self._conn)
        return hits

    async def persist(self, albums):
        """Write *albums* (``{key: AlbumMetadata}``) in one upsert.

        A no-op when the cache is disabled or *albums* is empty. A failure is
        logged, flagged in ``persist_failed`` and not raised: it costs the next
        job a lookup, not this one.
        """
        if self._conn is None or not albums:
            return
        try:
            await batch_persist_metadata(self._conn, albums)
        # Fail open: a failed persist costs the next job a lookup, not this one.
        except Exception:  # noqa: BLE001
            self.persist_failed = True
            log_failure("DB persist failed (non-fatal)", logging.WARNING)

    async def lookup_original_releases(self, keys):
        """Return cached MusicBrainz findings for *keys*, or {} without raising.

        A missing correction only skips the display upgrade; it must never
        block a job the way a metadata-fetch failure would.
        """
        if self._conn is None:
            return {}
        try:
            return await batch_lookup_original_release(self._conn, keys)
        # Fail open: a missing correction only skips the display upgrade.
        except Exception:  # noqa: BLE001
            log_failure(
                "Original-release cache lookup failed (non-fatal)", logging.WARNING
            )
            return {}

    async def close(self):
        """Close the connection at most once; a failed close is logged only.

        The cache is optional, so closing it must not take down a job whose
        results are already built.
        """
        conn, self._conn = self._conn, None
        if conn is None:
            return
        try:
            await conn.close()
        # A failed close must not mask the job's own outcome.
        except Exception:  # noqa: BLE001
            log_failure("Closing the cache DB connection failed", logging.WARNING)


@asynccontextmanager
async def open_album_cache():
    """Open the shared album cache for one job and close it when the block ends.

    Connects through ``get_db_connection`` (``DATABASE_URL``, the retry
    backoff and the connect timeout are its, unchanged) and yields an
    ``AlbumCache``, disabled when no connection could be had. The connection is
    closed when the block ends, whether it ends normally or with an exception.
    """
    album_cache = AlbumCache(await get_db_connection())
    try:
        yield album_cache
    finally:
        await album_cache.close()
```

- [ ] **Step 4: Run the cache tests; they pass**

Run: `"$PY" -m pytest tests/services/test_cache.py tests/services/test_failure_logging.py -q -p no:cacheprovider`
Expected: all pass except `tests/test_module_boundaries.py::test_only_the_cache_module_reads_or_writes_the_metadata_table` and the process-level close test, which wait for Step 5.

- [ ] **Step 5: Switch the orchestrator to the cache's operation**

`scrobblescope/orchestrator/_cache.py`: replace the whole file with

```python
"""The job-facing side of the DB metadata cache in ``process_albums``.

``scrobblescope.cache.AlbumCache`` owns the connection and decides what a
database error means: it never raises into a job and says what failed through
``lookup_failed`` and ``persist_failed``. These two functions are Phase 1 (DB
Batch Lookup) and Phase 4 (DB Batch Persist) of ``process_albums`` as far as
the job is concerned: they turn the cache's answers into the job's stats and
log lines. The original-release lookup (Phase 4b) needs no job message and
calls ``AlbumCache.lookup_original_releases`` directly.
"""

import logging

from scrobblescope import jobs


async def _lookup_cached_metadata(album_cache, job_id, album_keys):
    """DB Batch Lookup. Returns ``{key: AlbumMetadata}``, ``{}`` if the cache is
    off or the read failed, and records which on the job."""
    cached_metadata = await album_cache.lookup(album_keys)
    if not album_cache.enabled:
        jobs.record_stat(
            job_id,
            "db_cache_warning",
            "DB cache unavailable; using Spotify fallback.",
        )
    elif album_cache.lookup_failed:
        jobs.record_stat(
            job_id, "db_cache_warning", "DB lookup failed; cache bypassed."
        )
    else:
        jobs.record_stat(job_id, "db_cache_lookup_hits", len(cached_metadata))
        logging.info(
            f"DB cache: {len(cached_metadata)} hits / {len(album_keys)} total albums"
        )
    return cached_metadata


async def _persist_new_metadata(album_cache, job_id, new_metadata):
    """DB Batch Persist. Non-fatal on failure; records the outcome on the job."""
    if not (album_cache.enabled and new_metadata):
        return
    await album_cache.persist(new_metadata)
    if album_cache.persist_failed:
        jobs.record_stat(job_id, "db_cache_warning", "DB persist failed.")
    else:
        jobs.record_stat(job_id, "db_cache_persisted", len(new_metadata))
        logging.info(f"Persisted {len(new_metadata)} new metadata rows to DB cache")
```

`scrobblescope/orchestrator/__init__.py`:
- Replace the `from scrobblescope.cache import (...)` block with `from scrobblescope.cache import open_album_cache`.
- In the import block at the bottom, delete `_lookup_cached_original_release,` from the `from scrobblescope.orchestrator._cache import (...)` list.
- In `__all__` delete the entries `"batch_lookup_metadata"`, `"batch_lookup_original_release"`, `"batch_persist_metadata"`, `"cleanup_stale_metadata"`, `"get_db_connection"` and `"_lookup_cached_original_release"`, and add `"open_album_cache",` between `"merge_unmatched_rows"` and `"process_albums"`.
- In the module docstring, append: "The cache is the exception: its operations are patched at ``scrobblescope.cache.<name>``, because ``open_album_cache`` is the only door to it."
- Replace the body of `process_albums` after its first `logging.info(...)` call with:

```python
    async with open_album_cache() as album_cache:
        # =============================================================
        # Phase 1: DB Batch Lookup
        # =============================================================
        jobs.record_stat(job_id, "db_cache_enabled", album_cache.enabled)
        cached_metadata = await _lookup_cached_metadata(
            album_cache, job_id, list(filtered_albums.keys())
        )

        # =============================================================
        # Phase 2: Partition into cache hits and misses
        # =============================================================
        cache_hits = {}  # key -> {"cached": AlbumMetadata, "original": original_data}
        cache_misses = {}  # key -> original_data

        for key, original_data in filtered_albums.items():
            if key in cached_metadata:
                cache_hits[key] = {
                    "cached": cached_metadata[key],
                    "original": original_data,
                }
            else:
                cache_misses[key] = original_data

        db_hit_count = len(cache_hits)
        jobs.record_stat(job_id, "cache_hits", db_hit_count)
        logging.info(
            f"Cache partition: {db_hit_count} hits, {len(cache_misses)} misses"
        )

        # =============================================================
        # Phase 3: Spotify fetch for misses only
        # =============================================================
        new_metadata = await _fetch_spotify_misses(job_id, cache_misses, cache_hits)

        # =============================================================
        # Phase 4: DB Batch Persist
        # =============================================================
        await _persist_new_metadata(album_cache, job_id, new_metadata)

        # =============================================================
        # Phase 4b: Original-release correction lookup (Task 8, Batch 22
        # WP-3). Applies findings already in original_release_cache --
        # the live MusicBrainz worker (Task 9) is what populates new ones.
        # =============================================================
        original_release_hits = await album_cache.lookup_original_releases(
            list(cache_hits.keys())
        )

    # =================================================================
    # Phase 5: Build results from unified cache_hits
    # =================================================================
    total_matched = len(cache_hits)
    jobs.record_stat(job_id, "spotify_matched", total_matched)
    jobs.record_stat(
        job_id,
        "spotify_unmatched",
        len(filtered_albums) - total_matched,
    )

    return _build_results(
        cache_hits,
        job_id,
        year,
        sort_mode,
        release_scope,
        decade,
        release_year,
        original_release_hits,
    )
```

(The connection is closed when the `async with` ends, before Phase 5, as the old `finally` did, and also while `SpotifyUnavailableError` unwinds.)

- [ ] **Step 6: Re-point the existing tests**

Do the re-point with a byte-safe script, not `sed -i` (`constraints.md` R9: GNU `sed -i` has mangled backslash escapes and CRLF files on this branch set). `SCRATCH` is a private directory named for this PR and task, for example `C:/ssw/mee-t4-scratch`, removed afterwards:

```bash
NAMES='get_db_connection|batch_lookup_metadata|batch_persist_metadata|batch_lookup_original_release|cleanup_stale_metadata'
mkdir -p "$SCRATCH"
git grep -lE "scrobblescope\.orchestrator\.($NAMES)|o \+ \"($NAMES)\"" -- tests scripts > "$SCRATCH/repoint.txt"
"$PY" -I - "$SCRATCH/repoint.txt" <<'PYEOF'
import re
import sys

names = "get_db_connection|batch_lookup_metadata|batch_persist_metadata|batch_lookup_original_release|cleanup_stale_metadata"
dotted = re.compile(rb"scrobblescope\.orchestrator\.(" + names.encode() + rb")")
concat = re.compile(rb'o \+ "(get_db_connection|batch_lookup_metadata|batch_persist_metadata)"')
for path in open(sys.argv[1]).read().split():
    data = open(path, "rb").read()
    new, n_dotted = dotted.subn(rb"scrobblescope.cache.\1", data)
    n_concat = 0
    if path.endswith("test_pipeline_integration.py"):
        new, n_concat = concat.subn(rb'"scrobblescope.cache.\1"', new)
    if new != data:
        open(path, "wb").write(new)
    print(path, n_dotted + n_concat)
PYEOF
git grep -nE "orchestrator\.(get_db_connection|batch_|cleanup_stale)|o \+ \"(get_db_connection|batch_|cleanup_stale)" -- tests scripts
```

The script prints the replacement count per file; it must read 46 for `test_orchestrator_process_albums.py`, 2 for `test_orchestrator_helpers.py`, 2 for `test_orchestrator_fetch_spotify.py` and 3 for `test_pipeline_integration.py` (the checklist from the plan's assumptions). Keep each file's line endings (the script reads and writes bytes). Expected: the last command prints nothing. `git diff --stat` shows `test_orchestrator_process_albums.py`, `test_orchestrator_fetch_spotify.py`, `test_orchestrator_helpers.py` (if it patched a name) and `test_pipeline_integration.py`, patch strings only.

Then, by hand:
- `tests/services/test_orchestrator_process_albums.py`: add `from scrobblescope.cache import AlbumCache`; in `test_lookup_reports_a_stale_schema_as_its_own_fault` and `test_lookup_still_reports_a_transient_failure_plainly` change `_lookup_cached_metadata(conn, "job-1", [("a", "b")])` to `_lookup_cached_metadata(AlbumCache(conn), "job-1", [("a", "b")])`.
- `tests/services/test_orchestrator_helpers.py`: delete `test_lookup_cached_original_release_without_connection_skips_query` and `test_lookup_cached_original_release_failure_is_non_fatal` (moved to `tests/services/test_cache.py` as `test_original_release_lookup_without_a_connection_skips_the_query` and `test_original_release_lookup_failure_is_non_fatal`, same assertions through `AlbumCache`) and the `_lookup_cached_original_release` import; remove any import that became unused (`logging`, `AsyncMock`, `patch`) only if ruff reports it.

- [ ] **Step 7: Run everything; Task 1's tests are the proof**

Run: `"$PY" -m pytest -q -p no:cacheprovider`
Expected: all pass. Then:

Run: `git diff $(git log --format=%h -1 -- tests/test_album_cache_parity.py) -- tests/test_album_cache_parity.py tests/fake_postgres.py`
Expected: no output (the commit named is Task 1's; the parity tests ran unchanged through Tasks 3 and 4).

Hosting evidence, read from the diff: `git diff HEAD -- scrobblescope | grep -nE '^\+.*(\.execute\(|\.fetch\(|asyncpg\.connect\()'`
Expected: no output. No line this task adds issues a statement or opens a connection itself; `AlbumCache` only calls the functions that already did, once each, as before. `test_a_search_costs_one_connection_and_a_fixed_statement_sequence` and `test_a_failing_cache_statement_never_fails_the_search` (one connection, one close, under every injected failure) are the executable form.

- [ ] **Step 8: Docs follow the code; WP-3 amendment**

`.claude/SESSION_CONTEXT.md`:
- Section 3: replace the `cache.py` line with `  cache.py                  # the shared album cache: AlbumCache / open_album_cache own the connection, the SQL and the failure policy; get_db_connection and the original-release batch functions stay public for release_checks`; replace the `orchestrator/_cache.py` line's comment with `# job stats and log lines for the cache lookup and persist steps (scrobblescope/cache.py does the work)`.
- Section 4: `orchestrator/_cache.py    <- jobs`.
- Section 5 (the `process_albums` flow): change "phases 1/4 in orchestrator/_cache.py," to "phases 1/4 report to the job in orchestrator/_cache.py; scrobblescope/cache.py (AlbumCache) does the work,"; "1: DB connect + batch lookup (30-day TTL)" to "1: open_album_cache (connect) + batch lookup (30-day TTL)"; "4: DB batch persist + conn.close() in finally" to "4: DB batch persist; the async with closes the connection (a failed close is logged, never raised)".

`docs/architecture/runtime-system.md`: change the node `Cache[cache.py]` to `Cache[cache.py<br/>AlbumCache]`. In the "How an album gets its release date" bullet replace "`_persist_new_metadata` writes the enriched rows back to the cache, so a" with "`AlbumCache.persist` (reported to the job by `_persist_new_metadata`) writes the enriched albums back to the cache, so a", and append to step (1)'s sentence: "The cache is optional at runtime: when the database is missing or does not answer, `open_album_cache` yields a disabled cache and every album is a miss." Validate the edited Mermaid block with the Mermaid validator tool.

`docs/architecture/top-albums-sequence.md` (sequence diagram; keep the surrounding indentation):
- `Orch->>Cache: Open connection (None when DB disabled)` becomes `Orch->>Cache: open_album_cache (a disabled cache when the DB is missing or does not answer)`.
- `Orch->>Cache: Batch lookup all album keys` becomes `Orch->>Cache: lookup (AlbumMetadata by album key)`.
- `Orch->>Cache: Persist fresh metadata` becomes `Orch->>Cache: persist (AlbumMetadata by album key, one upsert)`.
- `Orch->>Cache: Close connection` becomes `Orch->>Cache: Leave the async with (close)`, and its note becomes `Note over Orch,Cache: Closed when the block ends, so it also closes while SpotifyUnavailableError unwinds; a failed close is logged and never raised`.
Validate the edited diagram. In the prose below it, "Persistence happens in the caller (Phase 4)" stays true.

`BATCH23_DEFINITION.md` (amendment, spec rule for PR #5: WP-3's metadata shape). Two edits, with the date of the commit:
1. In "Data handling", append to the last bullet (the one that begins "WP-3/WP-4 verification must exercise the full export-to-enrichment path"): " The shared metadata table has one write path (amended <commit date>, PR #5): `AlbumCache.persist` takes `AlbumMetadata` records, which hold only provider-returned album facts (provider, album id, link, release date, cover, track durations), so no listening fact has an argument to travel in. `tests/fake_postgres.py` stores what the SQL would store; inspect that, not a positional tuple."
2. In WP-3, after the bullet "**The include-unmatched choice reaches the export path**", add:
   "- [ ] **The export job reaches the cache only through `process_albums`** (amended <commit date>, PR #5). `process_albums` opens and closes the cache itself (`open_album_cache`); `export_album_task` passes no connection and imports nothing from `scrobblescope.cache`. Enrichment reaches the job as `AlbumMetadata` records, so an export row carries the same `provider`, `spotify_id`, `album_url` and `album_image` fields as a Last.fm row. Acceptance adds: with the cache database missing, an export job completes from provider calls and records `db_cache_warning`."

`docs/agents/FINDINGS.md`, F-B23-3: replace the sentence beginning "Status: open (P2). F-B22-7 and F-B22-8 have both landed" up to "No performance gain is claimed." with "Status: resolved <commit date> by refactor(cache): Let the cache own its connection and failures -- `cache.AlbumCache` and `open_album_cache` own the connection lifetime and what a database error means (including a failing `close()`, which no longer fails a job); `process_albums` manages no connection and `orchestrator/_cache.py` only reports to the job; the correction worker keeps its own policy, as the finding asked. No performance gain is claimed." Keep the "Source:" sentence.

Sweep: `git grep -nE "_lookup_cached_original_release|conn\.close\(\) in finally|_persist_new_metadata writes" -- . ':!docs/history' ':!docs/logarchive' ':!docs/superpowers/plans' ':!docs/superpowers/handoffs' ':!docs/agents/PLAYBOOK.md'`
Expected: no hits (dated plans and handoffs stay as history; `docs/agents/PLAYBOOK.md` is excluded because this task's own Section 4 entry names `_lookup_cached_original_release`, and a dated entry is a point-in-time record).

- [ ] **Step 9: Mutation evidence**

Plant each defect in a scratch copy of the tree, or copy the file aside first and copy it back after each row (`constraints.md` R9: never `git checkout -- <file>`; `cache.py`, `_cache.py` and `__init__.py` hold this task's uncommitted work). Run the named tests, confirm failure, restore, confirm they pass.

| # | Planted defect | File | Test that must fail |
|---|---|---|---|
| 1 | in `AlbumCache.close`, remove the `try`/`except` (keep `await conn.close()`) | `scrobblescope/cache.py` | `test_a_failing_close_is_logged_by_class_and_never_raised`, `test_process_albums_survives_a_connection_that_fails_to_close` |
| 2 | in `open_album_cache`, remove the `try`/`finally` (close after the `yield` only) | `scrobblescope/cache.py` | `test_the_connection_closes_once_however_the_block_ends[True]`, `test_the_connection_is_closed_once_when_no_provider_can_answer` |
| 3 | in `AlbumCache.persist`, drop `self._conn is None or` from the guard | `scrobblescope/cache.py` | `test_a_cache_with_no_database_does_nothing_and_fails_nothing` |
| 4 | in `AlbumCache.lookup`, remove the `try`/`except` | `scrobblescope/cache.py` | `test_a_failing_cache_statement_never_fails_the_search[read]` |
| 5 | in `AlbumCache.lookup`'s `except` block add `self._conn = await get_db_connection()` | `scrobblescope/cache.py` | `test_a_failing_cache_statement_never_fails_the_search[read]` (two connection attempts, the hosting-cost row) |
| 6 | add `from scrobblescope.cache import batch_persist_metadata` to `release_checks.py` | `scrobblescope/release_checks.py` | `test_only_the_cache_module_reads_or_writes_the_metadata_table` |
| 7 | in `_persist_new_metadata`, record `db_cache_persisted` even when `persist_failed` | `scrobblescope/orchestrator/_cache.py` | `test_a_failing_cache_statement_never_fails_the_search[write]` |
| 8 | in `AlbumCache.persist`, remove the `try`/`except` so the write is bare | `scrobblescope/cache.py` | `test_a_failed_read_is_a_miss_and_a_failed_write_is_not_an_error` (the write half), `test_a_failing_cache_statement_never_fails_the_search[write]` |
| 9 | in `AlbumCache.lookup`, `return {}` in place of `return hits` | `scrobblescope/cache.py` | `test_what_persist_writes_lookup_reads_back` (all three albums) |

`test_a_stored_row_naming_no_provider_album_is_a_miss_not_an_album` is covered by Task 3's row 3 (delete `if metadata is not None:` in `batch_lookup_metadata`): `AlbumCache.lookup` then returns `{KEY: None}` where the test expects `{}`. Re-run that plant once Task 4 is in place, since the test is new here. The read half of `test_a_failed_read_is_a_miss_and_a_failed_write_is_not_an_error` is covered by row 4.

- [ ] **Step 10: Section 4 entry, gates, commit**

Entry heading: `### <commit date> - The cache owns its connection and its failures`. Body: scope (`AlbumCache`, `open_album_cache`, `process_albums`, `_cache.py`, the facade's imports); why (F-B23-3; understanding "the cache is optional" took two modules; a failing `close()` failed a job); owner intent (the spec's hosting ceiling: "a missing or sleeping database degrades to provider calls, never fails a job"); what changed; deviations (a failing `close()` is now logged and swallowed, which is the one behaviour change; `_lookup_cached_original_release` is gone, its tests moved to `test_cache.py`); hosting evidence (Task 1's tests run unchanged, no added statement or connect in the diff); the nine mutation rows; the Validation line (R4 form).
Commit body names every edited existing test: `tests/services/test_orchestrator_process_albums.py` (patch strings; two direct calls now wrap `AlbumCache`), `tests/services/test_orchestrator_fetch_spotify.py`, `tests/test_pipeline_integration.py` (patch strings only), `tests/services/test_orchestrator_helpers.py` (two tests moved), `tests/services/test_failure_logging.py` (four sites re-pointed).
Subject: `refactor(cache): Let the cache own its connection and failures` (62 characters).

---

### Task 5: Point Section 3 at the plan, push, PR (controller)

**Touches:** `docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`.
**After:** Task 4 accepted.

- [ ] **Step 1:** `git fetch origin` and `git merge --no-ff origin/main` into `refactor/metadata-encoding` if `main` moved (PR #6 may have merged); resolve bookkeeping conflicts by keeping every dated entry from both sides, then `--fix --test-count N`. If PR #6 merged and edited `orchestrator/_results.py`, apply the rule in "Dependence on PRs #3, #4 and #6" and re-run Task 1's tests.
- [ ] **Step 2:** In PLAYBOOK Section 3's "Before WP-1" bullet, name this plan by path (`docs/superpowers/plans/2026-10-20-metadata-encoding.md`) and say the album-metadata seam (review card B-5) is under way (the state at that commit: the PR has not merged). One Section 4 entry. Commit: `docs(playbook): Point Section 3 at the metadata-encoding plan` (61 characters).
- [ ] **Step 3:** Gate-runner on the final head (all gates), grep every log, then push, open the PR against `main` (body: the four commits, the one behaviour change in Task 4's deviations, and the hosting evidence), and dispatch the CI watcher for the pushed head. The spec's review policy asks for no whole-PR review of a small PR; Task 4 adds one behaviour (the swallowed `close()`), which its own code review covers.

---

## Self-Review

**1. Spec coverage** (spec "PR #5" row; master plan P5 "Must cover"):

| Requirement | Where |
|---|---|
| The cache takes and returns `AlbumMetadata` | Task 3 (`batch_lookup_metadata`, `batch_persist_metadata`), Task 4 (`AlbumCache.lookup`, `persist`) |
| The cache owns its connection lifetime and failure policy | Task 4 (`open_album_cache`, `AlbumCache`) |
| `_album_provider` / `_album_url` go; the six-tuple branch goes | Tasks 2 and 3 (rule moved to `from_row`, functions and branch deleted; the pinning test replaced and named) |
| "Shared cache rows hold no listening facts" has one write path | Task 3 (one statement, a type with no listening field, `test_album_metadata_holds_album_facts_only`), Task 4 (boundary test), Task 1 (`test_a_stored_row_carries_no_listening_fact`) |
| No new database traffic (hosting cost ceiling) | Task 1 (`test_a_search_costs_one_connection_and_a_fixed_statement_sequence`, one connection under every failure), re-run unchanged in Tasks 3 and 4; Task 4 Step 7 diff check |
| The cache stays optional at runtime, tested with planted defects | Task 1 (no database, asleep, failing read, write and correction read, with mutation rows 6-8, 13 and 14), Task 4 (failing `close()`, row 1) |
| Parity first; identical rows written and read, identical results JSON | Task 1 (round trip for Spotify and Deezer, MusicBrainz correction, exclusion records, result key set) |
| The WP-3 amendment | Task 4 Step 8 (exact text, two edits) |
| Each task has `Touches:` and `After:`; one atomic commit with its own Section 4 entry (heading and subject, measured) | every task |
| Docs follow the code: `docs/architecture/*.md`, SESSION_CONTEXT Sections 3-5 | Tasks 2, 3, 4 |
| Assumptions checked, which held | "Assumptions checked" |
| How #5 and #6 order on `_results.py` and which rebuilds on which | "Dependence on PRs #3, #4 and #6" |

**2. Placeholder scan:** the only deferred values are things that exist only when the work is done: the commit date in each Section 4 heading and in the amendments, and N (the measured test count). Every test and every changed function is shown; the mechanical test edits give their search command and the exact replacement.

**3. Type consistency:** `AlbumMetadata(provider, album_id, url, release_date, image_url, track_durations)`, `AlbumMetadata.from_row(row) -> AlbumMetadata | None`, `AlbumMetadata.spotify_id` (Task 2) are used with the same names in `cache.py`, `_results.py`, `_details.py`, `_deezer_fallback.py` and every test. `batch_lookup_metadata(conn, keys) -> {key: AlbumMetadata}` and `batch_persist_metadata(conn, albums)` (Task 3) are the functions `AlbumCache.lookup` and `persist` call (Task 4). `FakePostgres` / `fake_postgres` / `METADATA_FIELDS` (Task 1) are imported by name in Tasks 3 and 4's tests. `spotify_metadata` / `deezer_metadata` (Task 3) are used in Task 4's tests with the same positional order `(album_id, release_date, image_url, track_durations)` (for `deezer_metadata` the third and fourth are likewise `image_url`, `track_durations`; the Task 4 calls pass only `album_id` and `release_date`). `_lookup_cached_metadata(album_cache, job_id, album_keys)` and `_persist_new_metadata(album_cache, job_id, new_metadata)` have the same parameter names in `_cache.py`, `process_albums` and the tests. The phases return `{key: AlbumMetadata}` in Task 3 and `process_albums` passes that dict to `_persist_new_metadata` unchanged in Task 4.

## Decisions made in this plan (engineering calls, not owner questions)

1. **Shape of the cache's operation.** One class, `AlbumCache`, behind one async context manager, `open_album_cache()`. Job messages (`db_cache_warning`, `db_cache_lookup_hits`, `db_cache_persisted`) stay in `orchestrator/_cache.py`, fed by two flags on the cache, because the finding asks that "job messages and enrichment decisions stay with the caller" and the cache module imports no `jobs`.
2. **Connection lifetime is unchanged.** One connection per job, opened before the lookup, held across Spotify and Deezer work, closed before results are built; the correction worker keeps its own connection for its run (at most `MUSICBRAINZ_CHECKS_PER_JOB`, 60, lookups at one per second). Opening per phase would add connects, which the hosting ceiling forbids; whether a held connection delays the database's idle stop is not measured here and is not changed by this PR.
3. **`release_checks.py` is not touched.** F-B23-3: "Metadata and release-check cache policy stay separate." The three original-release names and `get_db_connection` stay public for it; the three metadata functions get one caller and a boundary test.
4. **Test seam.** The existing `process_albums` tests keep proving behaviour through the change: a byte-safe script re-points their patches from `scrobblescope.orchestrator.<name>` to `scrobblescope.cache.<name>`, rather than rewriting sixteen tests around a new fake. The end-to-end proof is Task 1's, which names no `cache.py` function.
5. **`as_cache_row` is deleted, not kept as a wrapper.** Its only job was to build the tuple the persist function unpacked; the persist function now reads the record.
6. **A live Spotify result's link** comes from `album_metadata_from_details` (`external_urls.spotify`, with the classic page as the fallback), exactly as a later cache hit already showed it. Before, the live path rebuilt the classic link. Spotify's field is that link, so users see no difference; Task 1 pins live-equals-cached.
7. **A stored row that names no provider album is a miss**, not an album with a `None` provider. No write path produces one; the migration's backfill cannot either (`spotify_id` was `NOT NULL` until the provider columns arrived).
8. **A failing `close()` no longer fails a job.** The one deliberate behaviour change; the spec's constraint ("never fails a job") requires it and Task 4 tests it with a planted defect.
9. **`cache_hits[key]["cached"]` keeps its key name** though it now holds live fetches too: renaming it touches every `_build_results` test fixture for no behaviour. A follow-up may rename it with the typed hit that PR #4's selection work points toward.
10. **The stale-row cleanup still runs after a failed read**, as today; removing it would be a statement-count change to argue separately.

## Owner questions

None. Every call above is an engineering decision inside the spec's constraints (hosting cost ceiling, optional cache, F-B23-3's separation of the correction worker); none needs the owner's intent.
