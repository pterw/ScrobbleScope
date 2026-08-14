# ScrobbleScope: development cycle and runtime architecture

Mermaid reference for the agent-assisted development loop and the runtime
system. This is a living document, not a dated snapshot: correct it when the
code changes rather than adding a second copy elsewhere.

**Every edge here was verified against source.** When a diagram and the code
disagree, the code wins and the diagram is a defect -- diagrams are read by
agents that will change code to match them.

Last verified against the tree on 2026-08-14.

**Arrow semantics.** These differ by diagram, so each is stated where it
applies rather than once globally -- a single table claiming "solid means
import" would be false the moment a diagram also shows an HTTP call, and an
undeclared arrow is the defect that let earlier copies of these diagrams draw a
dependency and a dispatch identically.

| Arrow | Meaning |
|---|---|
| `-->` solid | **between two Python modules**, the source imports the target. Between anything else (browser, datastore, external service, document), a request, call, or containment relationship |
| `-.->` dotted | a runtime edge that is *not* an import: a response, a poll, or a dispatch through an injected callable |
| `->>` / `-->>` | in sequence diagrams, a call and its return |

Module-to-module solid arrows are the load-bearing ones. Where a diagram omits
a real import edge for legibility, it says so directly beneath.

---

## 1. AI-driven development cycle

Canonical context establishes scope, bounded work packages drive
implementation, and tests, documentation, CI, review and owner validation
provide feedback before the next iteration.

```mermaid
flowchart TD
    Request([Owner request, issue, or review finding]) --> Context[Read canonical context<br/>AGENTS.md, PLAYBOOK.md, batch definition,<br/>SESSION_CONTEXT.md, AGENT_NOTES.md]
    Context --> Align[Refresh origin and run<br/>check_worktree_alignment.py]
    Align --> Baseline[Confirm baseline gates<br/>pytest -q<br/>pre-commit run --all-files<br/>doc_state_sync.py --check]
    Baseline --> Scope[Select the active batch and bounded WP<br/>acceptance criteria + explicit out-of-scope items]
    Scope --> Explore[AI-assisted exploration<br/>trace code, tests, docs, dependencies,<br/>and linked findings]
    Explore --> Design[Design the smallest coherent change<br/>preserve SoC, DRY, acyclic dependencies,<br/>and real state-based test coverage]
    Design --> Implement[Implement one work package<br/>production code, tests, and required docs]
    Implement --> Targeted[Run targeted tests and adversarial checks]
    Targeted --> Docs[Update the source-of-truth documents<br/>PLAYBOOK Section 3 + dated Section 4 log<br/>SESSION_CONTEXT / README when affected]
    Docs --> Sync[Run doc_state_sync.py --fix<br/>refresh managed status and rotate logs]
    Sync --> Gates[Run validation gates<br/>full pytest + pre-commit + doc_state_sync --check]
    Gates --> SelfReview[Read changed files whole<br/>blast-radius grep for renamed claims,<br/>citations, ranges, and sibling copies]
    SelfReview --> Commit[Conventional commit for the WP<br/>specific paths only; no bulk staging]
    Commit --> PR[Open or update pull request]
    PR --> CI[GitHub Actions Quality Gate<br/>pre-commit, pytest + coverage,<br/>pip-audit advisory]
    CI --> Decision{CI or review outcome}
    Decision -->|Failure or actionable feedback| Diagnose[Diagnose the concrete failure<br/>reproduce, identify root cause,<br/>repair the class of issue]
    Diagnose --> Implement
    Decision -->|Green| OwnerReview[Owner review<br/>Firefox + responsive E2E where UI changes;<br/>inspect exports and both themes]
    OwnerReview -->|Issue found| Diagnose
    OwnerReview -->|Approved| Close[Merge or close the WP<br/>update handoff state and continue]
    Close --> Realign[Realign the source branch<br/>rebase-merge leaves it diverged<br/>with an identical tree]
    Realign --> Context

    Current[Current Batch 21 order<br/>F-SWE-1 audit, then WP-1] -.-> Scope

    classDef source fill:#f5efe2,stroke:#6a4baf,color:#1a1820
    classDef gate fill:#eee7fb,stroke:#6a4baf,color:#1a1820
    classDef feedback fill:#f9e5dd,stroke:#a64b39,color:#1a1820
    classDef current fill:#e5f1e8,stroke:#4d7a5a,color:#1a1820
    class Context,Scope,Docs,Sync source
    class Align,Baseline,Targeted,Gates,SelfReview,CI gate
    class Decision,Diagnose feedback
    class Current current
```

The `Realign` step is not incidental. `main` requires linear history and
accepts only squash and rebase merges, so merging rewrites the branch's
commits and leaves the source branch diverged from `origin/main` with a
byte-identical tree. The guard reports `WT004`; see AGENTS.md for the
tree-equality precondition that separates this from a real divergence.

---

## 2. Full-stack application architecture

A Flask + Jinja2 monolith with two asynchronous background pipelines. The web
process owns in-memory job state, so deployment intentionally uses one Gunicorn
worker with multiple threads. PostgreSQL is optional and stores persistent
Spotify metadata, not job state.

```mermaid
flowchart LR
    User((Last.fm user)) --> Browser

    subgraph Browser[Browser]
        Templates[Rendered Jinja pages<br/>base / index / loading / results / unmatched / error]
        JS[Page JavaScript<br/>index, loading, results, unmatched,<br/>error, heatmap, theme]
        CSS[Stylesheets and inline SVG assets<br/>current Bootstrap stack;<br/>Batch 21 Tailwind + daisyUI target]
        BrowserState[Form state, theme state,<br/>poll timers, rendered tables and SVG]
        Templates --> JS
        Templates --> CSS
        JS --> BrowserState
    end

    Browser -->|HTTP GET + CSRF-protected POST| App

    subgraph Runtime[Flask runtime]
        App[app.py<br/>create_app factory]
        Routes[routes.py<br/>Blueprint, validation, polling,<br/>result/error handlers]
        Worker[worker.py<br/>BoundedSemaphore<br/>MAX_ACTIVE_JOBS]
        Repo[repositories.py<br/>JOBS + jobs_lock<br/>job lifecycle and state CRUD]
        Album[orchestrator.py<br/>album aggregation, filtering,<br/>Spotify enrichment, result building]
        Heatmap[heatmap.py<br/>365-day fetch and daily aggregation]
        LastFMClient[lastfm.py<br/>pure async Last.fm client]
        SpotifyClient[spotify.py<br/>token, search, album details]
        Cache[cache.py<br/>asyncpg lookup, TTL cleanup,<br/>batch persist]
        Utils[utils.py<br/>REQUEST_CACHE, locks,<br/>HTTP sessions, global throttles]
        Domain[domain.py<br/>normalization and matching helpers]
        Errors[errors.py<br/>typed error codes and<br/>SpotifyUnavailableError]
    end

    App --> Routes
    Routes --> Repo
    Routes --> Worker
    Routes --> Album
    Routes --> Heatmap
    Routes --> LastFMClient
    Routes --> Utils
    Album --> Worker
    Album --> LastFMClient
    Album --> SpotifyClient
    Album --> Cache
    Album --> Domain
    Album --> Repo
    Album --> Utils
    Album --> Errors
    Heatmap --> Worker
    Heatmap --> LastFMClient
    Heatmap --> Repo
    Heatmap --> Utils
    Repo --> Errors
    LastFMClient --> Utils
    SpotifyClient --> Utils

    Worker -.->|runs an injected callable<br/>in a daemon thread| Album
    Worker -.->|runs an injected callable<br/>in a daemon thread| Heatmap
    Routes -.->|JSON progress / HTML transitions| Browser

    Repo --> Jobs[(In-memory JOBS<br/>UUID-keyed state<br/>2-hour expiry)]
    Utils --> RequestCache[(REQUEST_CACHE<br/>short-lived Last.fm/API reuse)]

    subgraph External[External services]
        LastFMAPI[(Last.fm API<br/>user.getinfo<br/>user.getrecenttracks)]
        SpotifyAPI[(Spotify Web API<br/>search + album details)]
        Postgres[(PostgreSQL<br/>spotify_cache<br/>30-day metadata TTL)]
    end

    LastFMClient -->|HTTPS + throttling/retry| LastFMAPI
    SpotifyClient -->|HTTPS + throttling/retry| SpotifyAPI
    Cache -->|asyncpg| Postgres

    subgraph Deploy[Fly.io deployment]
        Gunicorn[Gunicorn<br/>1 worker x 4 threads]
        Release[Release command<br/>schema initialization]
    end
    App -. deployed in .-> Gunicorn
    Release -. initializes .-> Postgres

    classDef browser fill:#f5efe2,stroke:#6a4baf,color:#1a1820
    classDef runtime fill:#eee7fb,stroke:#6a4baf,color:#1a1820
    classDef state fill:#e5f1e8,stroke:#4d7a5a,color:#1a1820
    classDef external fill:#f9e5dd,stroke:#a64b39,color:#1a1820
    classDef deploy fill:#e4eef7,stroke:#46739b,color:#1a1820
    class Templates,JS,CSS,BrowserState browser
    class App,Routes,Worker,Repo,Album,Heatmap,LastFMClient,SpotifyClient,Cache,Utils,Domain,Errors runtime
    class Jobs,RequestCache state
    class LastFMAPI,SpotifyAPI,Postgres external
    class Gunicorn,Release deploy
```

Two things this diagram is careful about, because both were previously drawn
backwards:

- **`worker.py` is a leaf, not a dispatcher.** `orchestrator.py` and
  `heatmap.py` import `worker` for `release_job_slot`; `worker.py` imports
  neither and never names them. The dispatch edge is real but runtime-only:
  `routes.py` imports the task callables and passes one as the `target`
  argument of `start_job_thread`, so the callee is opaque to `worker.py`.
  It is drawn dotted for that reason.
- **`cache.py` does not import `utils.py`.** It imports `asyncio`, `json`,
  `logging`, `os`, optionally `asyncpg`, and `config`. Nothing else.

Omitted for legibility: `config.py`, a leaf imported by `app` (under
`__main__` only), `cache`, `lastfm`, `orchestrator`, `repositories`,
`spotify`, `utils` and `worker`. The complete module graph, including every
`config` edge, is in `.claude/SESSION_CONTEXT.md` Section 4 -- that file is its
single source of truth, and this diagram is a view of it.

---

## 3. Top Albums request and enrichment sequence

Why the browser receives a job ID and polls: Last.fm and Spotify work happens
in a daemon thread, while the Flask request handlers only create and read job
state and render the next UI state.

**The concurrency slot is acquired before the job is created.** That ordering
is deliberate and load-bearing: reversing it would allocate a `JOBS` entry and
then reject the request, leaking an orphan job on every throttled call until
TTL expiry.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Browser
    participant Routes as "routes.py"
    participant Worker as "worker.py"
    participant Repo as "repositories.py / JOBS"
    participant Orch as "orchestrator.py"
    participant LastFM as "Last.fm API"
    participant Cache as "cache.py / PostgreSQL"
    participant Spotify as "Spotify API"

    User->>Browser: Enter username, year, thresholds, and sort
    Browser->>Routes: GET /validate_user?username=...
    Routes->>LastFM: user.getinfo
    LastFM-->>Routes: Valid user + registered year
    Routes-->>Browser: Validation result and minimum year

    User->>Browser: Submit album search
    Browser->>Routes: POST /results_loading + CSRF token
    Routes->>LastFM: _check_user_exists (registration-year guard)
    opt User invalid or year below registration
        Routes-->>Browser: index.html + error, before any slot is taken
    end
    Routes->>Repo: cleanup_expired_jobs()
    Routes->>Worker: acquire_job_slot()

    alt Slot exhausted (MAX_ACTIVE_JOBS reached)
        Worker-->>Routes: False
        Routes-->>Browser: index.html + "Too many requests in progress"
        Note over Routes,Repo: No job is created on this path
    else Slot acquired
        Worker-->>Routes: True
        Routes->>Repo: create_job(params)
        Repo-->>Routes: UUID job_id
        Routes->>Worker: start_job_thread(background_task, args=(job_id, ...))
        alt Thread start fails
            Routes->>Repo: delete_job(job_id)
            Routes-->>Browser: index.html + "Failed to start processing"
        else Daemon thread started
            Routes-->>Browser: loading.html(job_id)
        end
    end

    Worker->>Orch: background_task(job_id, ...)
    Orch->>Repo: Initialize progress at 0%
    Orch->>LastFM: Fetch paginated recent tracks
    loop Each page, with retry and global throttling
        LastFM-->>Orch: Scrobbles + page progress callback
        Orch->>Repo: set_job_progress(5%-20%, stats)
    end
    Orch->>Orch: Group albums, normalize names,<br/>apply thresholds and pre-slice
    Orch->>Repo: set_job_progress(20%)

    Orch->>Cache: _get_db_connection()
    Orch->>Cache: _batch_lookup_metadata(conn, all album keys)
    Cache-->>Orch: Matching in-TTL rows only
    Orch->>Cache: _cleanup_stale_metadata(conn)
    Orch->>Orch: Partition hits and misses

    alt Spotify cache misses exist
        Orch->>Spotify: Fetch access token
        loop Each album search, bounded concurrency
            Orch->>Spotify: Search artist + album
            Spotify-->>Orch: Spotify ID or no match
            Orch->>Repo: Progress 20%-40%, record unmatched reason
        end
        Orch->>Spotify: Batch-fetch album details for matched IDs
        Spotify-->>Orch: Release dates, art, track durations
        Orch->>Repo: Progress 40%-60%
        Orch->>Cache: _batch_persist_metadata (INSERT ON CONFLICT UPDATE)
        Cache-->>Orch: Persist complete
    else All metadata is cached
        Note over Orch,Spotify: No Spotify call and no repository write
    end

    Orch->>Orch: Merge cached + fresh metadata<br/>compute playtime and ranking
    Orch->>Repo: Store results and remaining unmatched entries,<br/>stats, and progress 60%-100%
    Orch->>Worker: release_job_slot()

    loop Poll until terminal state
        Browser->>Routes: GET /progress?job_id=...
        Routes->>Repo: get_job_progress(job_id)
        Repo-->>Routes: Progress, stats, errors, retry metadata
        Routes-->>Browser: JSON progress payload
    end

    alt Complete
        Browser->>Routes: POST /results_complete + job_id
        Routes->>Repo: get_job_context(job_id)
        Repo-->>Routes: Results + unmatched data
        Routes-->>Browser: results.html
        Browser->>Browser: Render semantic table, CSV/JPEG export,<br/>and optional unmatched view
    else Retryable upstream failure
        Routes-->>Browser: Error state + retry affordance
    else Fatal or invalid request
        Routes-->>Browser: error.html with stable error code
    end
```

The cache lookup returns **hits only** -- its `SELECT` returns just the
matching, in-TTL rows (`cache.py:83-96`). The orchestrator does pass the full
candidate set (`orchestrator.py:538-540`), so the partition could in principle
live either side; it lives in `orchestrator.py:564-574`, after the lookup
returns. Unmatched entries are recorded as they are found, during the 20-40%
band and again while results are built, not only at the end.

---

## 4. Heatmap request and rendering sequence

A separate background pipeline. It shares job storage, worker capacity,
Last.fm transport and progress polling with album search, but calls neither
Spotify nor PostgreSQL. Timestamps are decoded as UTC before daily aggregation
so a local development time zone cannot shift a scrobble to another day.

The same acquire-then-create ordering applies; here the rejection path is a
JSON 429 rather than a rendered page.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Browser
    participant Routes as routes.py
    participant Worker as worker.py
    participant Repo as repositories.py / JOBS
    participant Heatmap as heatmap.py
    participant LastFM as Last.fm API
    participant UI as heatmap.js

    User->>Browser: Select Heatmap tab and enter username
    Browser->>Routes: POST /heatmap_loading + CSRF token
    Routes->>Repo: cleanup_expired_jobs()
    Routes->>Worker: acquire_job_slot()

    alt Slot exhausted
        Worker-->>Routes: False
        Routes-->>Browser: JSON 429, retryable true
    else Slot acquired
        Worker-->>Routes: True
        Routes->>Repo: create_job({username, mode: heatmap})
        Repo-->>Routes: UUID job_id
        Routes->>Worker: start_job_thread(heatmap_task, args=(job_id, username))
        alt Thread start fails
            Routes->>Repo: delete_job(job_id)
            Routes-->>Browser: JSON 500
        else Daemon thread started
            Routes-->>Browser: JSON 202 with job_id
        end
    end

    Worker->>Heatmap: heatmap_task(job_id, username)
    Heatmap->>Repo: Initialize progress at 0%
    Heatmap->>LastFM: Fetch recent tracks for last 365 days
    loop Paginated pages, 5%-80% progress
        LastFM-->>Heatmap: Raw scrobble page
        Heatmap->>Repo: set_job_progress(page progress)
    end
    Heatmap->>Heatmap: Decode timestamps as UTC
    Heatmap->>Heatmap: Skip now-playing tracks
    Heatmap->>Heatmap: Drop out-of-range boundary entries
    Heatmap->>Heatmap: Aggregate daily_counts,<br/>total, max_count, and date range
    Heatmap->>Repo: Store daily_counts and progress 100%
    Heatmap->>Worker: release_job_slot()

    loop Poll until progress reaches 100
        UI->>Routes: GET /progress?job_id=...
        Routes->>Repo: get_job_progress(job_id)
        Repo-->>Routes: Progress, message, error state
        Routes-->>UI: JSON progress payload
    end

    UI->>Routes: GET /heatmap_data?job_id=... (one-shot, after 100%)
    Routes->>Repo: get_job_context(job_id)
    Repo-->>Routes: Daily counts and aggregate statistics

    alt Complete
        Routes-->>UI: JSON 200 with daily_counts, total, max_count, range
        UI->>UI: Render SVG GitHub-style 7x52 grid on desktop
        UI->>UI: Render sequential activity strip on narrow viewports
        UI->>UI: Apply rocket_r intensity palette, KPIs,<br/>tooltips, theme state, and responsive layout
    else Still processing
        Routes-->>UI: JSON 202, ready false
    else No scrobbles in range
        Heatmap->>Repo: set_job_error(no_scrobbles_in_range), not retryable
        Routes-->>UI: JSON 200 with error true
    else Last.fm unavailable or partial page failure
        Heatmap->>Repo: Persist stable error or partial-data warning
        Routes-->>UI: JSON 200 with error true and retryability
    end
```

---

## 5. Documentation and tooling architecture

How the canonical documents, the docsync integrity gate and the worktree guard
fit together. Solid arrows are imports; the document edges show which file is
the source of truth for which.

```mermaid
flowchart TD
    A[AGENTS.md<br/>the only ruleset] --> H[HANDOFF_PROMPT.md]
    A --> P[PLAYBOOK.md<br/>sequencing + execution log]
    P --> B[BATCH21_DEFINITION.md<br/>scope + acceptance criteria]
    P --> S[SESSION_CONTEXT.md<br/>current-state dashboard]
    P --> LA[docs/logarchive/<br/>rotated dated entries]

    D[doc_state_sync.py] --> CLI[docsync.cli]
    CLI --> Integrity[docsync.integrity]
    CLI --> Logic[docsync.logic]
    CLI --> Models[docsync.models]
    Integrity --> Logic
    Integrity --> Models
    Integrity --> Parser[docsync.parser]
    Integrity --> Render[docsync.renderer]
    Logic --> Models
    Logic --> Parser
    Logic --> Render
    Render --> Models
    Render --> Parser
    Parser --> Models

    D -. reads and rewrites .-> P
    D -. refreshes managed blocks .-> S
    D -. rotates entries into .-> LA

    G[check_worktree_alignment.py] --> Guard[dev/worktree_guard<br/>public re-export facade]
    Guard --> Diag
    Guard --> Inspect
    Guard --> Lineage
    Guard --> Runner
    Guard --> Types
    Guard --> Venv
    Inspect[_worktree_guard_inspection] --> Diag
    Inspect --> Lineage[_worktree_guard_lineage]
    Inspect --> Runner[_worktree_guard_runner]
    Inspect --> Types
    Inspect --> Venv[_worktree_guard_venv]
    Lineage --> Diag
    Lineage --> Types
    Venv --> Diag
    Venv --> Types
    Runner --> Types
    Diag[_worktree_guard_diagnostics<br/>display-safety rule<br/>constructs WT002/007/013/014] --> Types[_worktree_guard_types<br/>leaf, stdlib only]
    Guard -. parses the Branch value from .-> P

    PC[pre-commit] -. runs .-> D
    CI[GitHub Actions Quality Gate] -. runs .-> PC

    classDef doc fill:#f5efe2,stroke:#6a4baf,color:#1a1820
    classDef tool fill:#eee7fb,stroke:#6a4baf,color:#1a1820
    classDef gate fill:#e5f1e8,stroke:#4d7a5a,color:#1a1820
    class A,H,P,B,S,LA doc
    class D,CLI,Integrity,Logic,Models,Parser,Render,G,Guard,Inspect,Lineage,Runner,Venv,Diag,Types tool
    class PC,CI gate
```

Every import edge among these modules is drawn -- nothing is omitted here. The
facade re-exports from all six guard modules, which is why it has six outbound
edges rather than one; the remaining WT codes are raised in `_lineage`,
`_inspection`, `_venv` and the CLI, not in `_diagnostics`.

- `scripts/docsync`: keeps PLAYBOOK, SESSION_CONTEXT and archive state
  deterministic. `doc_state_sync.py` imports only `docsync.cli`; everything
  below that is internal to the package.
- `scripts/dev/_worktree_guard_*`: protects linked-worktree bootstrap and
  primary-environment selection. Read-only -- it reports and never repairs.
- Pre-commit enforces formatting, hygiene, private-key detection and docsync.
  Its top-level `exclude` lists thirteen entries, `docs/` among them, so
  `doc-state-sync-check` (`always_run: true`, the only hook that sets it) is
  the only hook that inspects anything under `docs/`.
- CI runs pre-commit, a coverage gate, and an advisory pip-audit.
- Deployment runs one Gunicorn worker with four threads; the shared in-memory
  job state depends on that single-process design.

---

## Source references

- Development rules and bootstrap order: `AGENTS.md`
- Active batch and handoff state: `PLAYBOOK.md`, Section 3 and Section 4
- Batch 21 scope and acceptance criteria: `BATCH21_DEFINITION.md`
- Module inventory and the authoritative dependency graph:
  `.claude/SESSION_CONTEXT.md`, Sections 3 and 4
- Product-level architecture overview: `README.md`, Architecture section
- CI quality gate: `.github/workflows/test.yml`
- Diagram authoring workflow: `.github/instructions/mermaid.instructions.md`
