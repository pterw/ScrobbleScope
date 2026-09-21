# Full-stack application architecture

This diagram is the canonical owner of the runtime system view. ScrobbleScope
is a Flask + Jinja2 monolith with two background pipelines, in-memory job
state, and an optional PostgreSQL metadata cache.

```mermaid
flowchart LR
    User((Last.fm user)) --> Browser

    subgraph Browser[Browser]
        Templates[Jinja pages]
        JS[Page JavaScript]
        CSS[One framework stylesheet<br/>per page]
        Theme[data-theme on html]
        BrowserState[Form, polling, tables,<br/>heatmap, and spotlight state]
        Templates --> JS
        Templates --> CSS
        JS --> Theme
        JS --> BrowserState
    end

    Browser -->|HTTP + CSRF-protected POST| App

    subgraph Runtime[Flask runtime]
        App[app.py<br/>application factory]
        Routes[routes/<br/>Blueprint and handlers]
        Worker[worker.py<br/>bounded semaphore]
        Repo[repositories.py<br/>JOBS + lifecycle CRUD]
        Album[orchestrator/<br/>album pipeline]
        Heatmap[heatmap.py<br/>daily aggregation]
        LastFMClient[lastfm.py]
        SpotifyClient[spotify.py]
        DeezerClient[deezer.py<br/>fallback provider]
        Enrichment[enrichment.py<br/>AlbumMetadata contract]
        ReleaseChecks[release_checks.py<br/>one correction worker,<br/>FIFO job queue]
        MusicBrainzClient[musicbrainz.py]
        Cache[cache.py]
        Utils[utils.py]
        Domain[domain.py]
        Errors[errors.py]
        Spotlight[spotlight.py<br/>artist sampling]
        Unmatched[unmatched.py<br/>reason codes,<br/>threshold partition]
    end

    App -.->|imported inside create_app| Routes
    Routes --> Repo
    Routes --> Worker
    Routes --> Album
    Routes --> Heatmap
    Routes --> LastFMClient
    Routes --> SpotifyClient
    Routes --> Domain
    Routes --> Utils
    Routes --> Spotlight
    Routes --> Unmatched
    Album --> Worker
    Album --> LastFMClient
    Album --> SpotifyClient
    Album --> DeezerClient
    Album --> ReleaseChecks
    Album --> Cache
    Album --> Domain
    Album --> Repo
    Album --> Utils
    Album --> Errors
    Album --> Unmatched
    Heatmap --> Worker
    Heatmap --> LastFMClient
    Heatmap --> Repo
    Heatmap --> Utils
    Repo --> Errors
    Routes --> ReleaseChecks
    ReleaseChecks --> MusicBrainzClient
    ReleaseChecks --> Cache
    ReleaseChecks --> Repo
    ReleaseChecks --> Domain
    ReleaseChecks --> Unmatched
    ReleaseChecks --> Utils
    ReleaseChecks -.->|imported inside a function| Album
    LastFMClient --> Utils
    SpotifyClient --> Utils
    SpotifyClient --> Domain
    SpotifyClient --> Enrichment
    DeezerClient --> Utils
    DeezerClient --> Domain
    DeezerClient --> Enrichment
    MusicBrainzClient --> Utils
    MusicBrainzClient --> Domain
    Spotlight --> Utils

    Worker -.->|runs injected callable| Album
    Worker -.->|runs injected callable| Heatmap
    Routes -.->|JSON or HTML response| Browser
    Routes -.->|canonical pages| Pages["/ , /results, /heatmap,<br/>/unmatched, /loading"]
    Routes -.->|JSON APIs| APIs["/progress, /api/unmatched,<br/>/api/artist_spotlight, /api/release_checks,<br/>/validate_user"]

    Repo --> Jobs[(In-memory JOBS<br/>2-hour expiry)]
    Utils --> RequestCache[(REQUEST_CACHE)]
    LastFMClient -->|HTTPS| LastFMAPI[(Last.fm API)]
    SpotifyClient -->|HTTPS| SpotifyAPI[(Spotify API)]
    DeezerClient -->|HTTPS| DeezerAPI[(Deezer API)]
    MusicBrainzClient -->|HTTPS, 1 req/s| MusicBrainzAPI[(MusicBrainz API)]
    Cache -->|asyncpg| Postgres[(PostgreSQL<br/>spotify_cache,<br/>original_release_cache)]

    subgraph Deploy[Fly.io deployment]
        Gunicorn[Gunicorn<br/>1 worker x 4 threads]
        Release[Schema initialization]
    end
    App -. deployed in .-> Gunicorn
    Release -. initializes .-> Postgres

    classDef browser fill:#f5efe2,stroke:#6a4baf,color:#1a1820
    classDef runtime fill:#eee7fb,stroke:#6a4baf,color:#1a1820
    classDef state fill:#e5f1e8,stroke:#4d7a5a,color:#1a1820
    classDef external fill:#f9e5dd,stroke:#a64b39,color:#1a1820
    classDef deploy fill:#e4eef7,stroke:#46739b,color:#1a1820
    class Templates,JS,CSS,Theme,BrowserState browser
    class App,Routes,Worker,Repo,Album,Heatmap,Spotlight,Unmatched,LastFMClient,SpotifyClient,DeezerClient,Enrichment,ReleaseChecks,MusicBrainzClient,Cache,Utils,Domain,Errors runtime
    class Pages,APIs runtime
    class Jobs,RequestCache state
    class LastFMAPI,SpotifyAPI,DeezerAPI,MusicBrainzAPI,Postgres external
    class Gunicorn,Release deploy
```

Solid module-to-module arrows are imports. The dotted worker edges are runtime
dispatch through callables injected by `routes/`; `worker.py` imports neither
pipeline. The dotted `App` edges are imports deferred into a function, which is
what the factory pattern requires: `create_app` imports the blueprint at
`app.py:143` and the entrypoint imports `ensure_api_keys` at `app.py:155`, so
neither is a module-level edge.

`config.py` is not drawn: **ten** of the nodes shown here import it at module
level, and those edges would cross and hide the flow. Named with their import
lines so the list can be re-checked rather than trusted -- `worker.py:4`,
`repositories.py:6`, `cache.py:11`, `utils.py:12`, `lastfm.py:8`,
`spotify.py:6`, `deezer.py:16`, `musicbrainz.py:17`, `release_checks.py:49`,
and `orchestrator/` (three of its five files: `__init__.py:35`, `_search.py:17`,
`_details.py:16`). An eleventh node, `app.py`, imports it too, but deferred
inside the `__main__` block.
`routes/` and `orchestrator/` are each a package as of Batch 22 WP-0 (split
by concern and by phase respectively); this view stays at the package level
rather than drawing every submodule. The complete import graph, submodules
included, lives in SESSION_CONTEXT Section 4.

Five things this view deliberately makes visible, because breaking them is
silent:

- **One framework stylesheet per page.** `base.html` used to default Bootstrap
  on and every migrated page opted out. WP-8 removed the default, the per-page
  opt-outs and `global.css` itself. The gate still asserts stylesheet isolation
  per page, and `tests/test_template_shell.py` holds every page to exactly one
  framework stylesheet.
- **The theme is written once, and one repaint follows it.** `theme.js` sets
  `data-theme` on `<html>`, which daisyUI and `shell.css` key on. WP-8 retired
  the second write, `.dark-mode` on `<body>`, and moved `heatmap.js`'s observer
  to `data-theme` in the same change. That observer is load-bearing: a heatmap
  cell carries its colour as an SVG `fill` attribute, a presentation attribute
  does not resolve a custom property, so zero-count cells are repainted in
  JavaScript. The gate's "heatmap zero cells follow theme" check owns it;
  before the check existed, the whole gate stayed green while the cells kept
  their light colour on a dark page.
- **A displayed release year is not always the provider's.** Spotify and
  Deezer both date a remaster by its reissue, and the year filters mean the
  year the album first came out, so `release_checks.py` corrects the date
  from MusicBrainz's release group. The provider's own date is kept beside it
  as `provider_release_date` rather than overwritten, because it is still the
  right date for the provider's page a row links to. The correction runs
  after `set_job_results`, never before: MusicBrainz allows one request per
  second per IP, so waiting for it would hold a whole result set behind a
  minute of lookups. `docs/design/RECONCILIATION.md` records the same fact
  for the design system, since the year a reader sees is now sourced from
  two places.
- **The correction worker is one thread for the whole process.** It owns its
  own event loop and a FIFO queue of job ids. More threads would only queue
  behind the same process-wide limiter while multiplying database connections
  and the ways one job's state can be raced. It imports
  `_matches_release_criteria` from `orchestrator/` inside a function: the
  orchestrator imports this module at module level to enqueue a finished job,
  and a module-level import back would close that cycle.
- **The Spotify cost boundary.** `_MAX_ALBUM_CAP = 500` caps every sort mode
  before any Spotify call, and `partition_albums_by_threshold` splits the
  aggregated albums before enrichment, so albums that miss a play or track
  minimum are written straight to the unmatched repository and cost no Spotify
  quota. `unmatched.py` owns that partition and the stable reason codes;
  `spotlight.py` owns artist sampling for `/api/artist_spotlight`.
