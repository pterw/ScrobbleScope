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
        CSS[Stylesheets and inline SVG]
        BrowserState[Form, theme, polling,<br/>tables, and heatmap state]
        Templates --> JS
        Templates --> CSS
        JS --> BrowserState
    end

    Browser -->|HTTP + CSRF-protected POST| App

    subgraph Runtime[Flask runtime]
        App[app.py<br/>application factory]
        Routes[routes.py<br/>Blueprint and handlers]
        Worker[worker.py<br/>bounded semaphore]
        Repo[repositories.py<br/>JOBS + lifecycle CRUD]
        Album[orchestrator.py<br/>album pipeline]
        Heatmap[heatmap.py<br/>daily aggregation]
        LastFMClient[lastfm.py]
        SpotifyClient[spotify.py]
        Cache[cache.py]
        Utils[utils.py]
        Domain[domain.py]
        Errors[errors.py]
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

    Worker -.->|runs injected callable| Album
    Worker -.->|runs injected callable| Heatmap
    Routes -.->|JSON or HTML response| Browser

    Repo --> Jobs[(In-memory JOBS<br/>2-hour expiry)]
    Utils --> RequestCache[(REQUEST_CACHE)]
    LastFMClient -->|HTTPS| LastFMAPI[(Last.fm API)]
    SpotifyClient -->|HTTPS| SpotifyAPI[(Spotify API)]
    Cache -->|asyncpg| Postgres[(PostgreSQL<br/>spotify_cache)]

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
    class Templates,JS,CSS,BrowserState browser
    class App,Routes,Worker,Repo,Album,Heatmap,LastFMClient,SpotifyClient,Cache,Utils,Domain,Errors runtime
    class Jobs,RequestCache state
    class LastFMAPI,SpotifyAPI,Postgres external
    class Gunicorn,Release deploy
```

Solid module-to-module arrows are imports. The dotted worker edges are runtime
dispatch through callables injected by `routes.py`; `worker.py` imports neither
pipeline. The complete import graph lives in SESSION_CONTEXT Section 4.
