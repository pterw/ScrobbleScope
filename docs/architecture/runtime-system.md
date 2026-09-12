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
        Theme[data-theme on html<br/>plus .dark-mode on body]
        BrowserState[Form, polling, tables,<br/>heatmap, and spotlight state]
        Templates --> JS
        Templates --> CSS
        JS --> Theme
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
        Spotlight[spotlight.py<br/>artist sampling]
        Unmatched[unmatched.py<br/>reason codes,<br/>threshold partition]
    end

    App --> Routes
    Routes --> Repo
    Routes --> Worker
    Routes --> Album
    Routes --> Heatmap
    Routes --> LastFMClient
    Routes --> Utils
    Routes --> Spotlight
    Routes --> Unmatched
    Album --> Worker
    Album --> LastFMClient
    Album --> SpotifyClient
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
    LastFMClient --> Utils
    SpotifyClient --> Utils

    Worker -.->|runs injected callable| Album
    Worker -.->|runs injected callable| Heatmap
    Routes -.->|JSON or HTML response| Browser
    Routes -.->|canonical pages| Pages["/ , /results, /heatmap,<br/>/unmatched, /loading"]
    Routes -.->|JSON APIs| APIs["/progress, /api/unmatched,<br/>/api/artist_spotlight, /validate_user"]

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
    class Templates,JS,CSS,Theme,BrowserState browser
    class App,Routes,Worker,Repo,Album,Heatmap,Spotlight,Unmatched,LastFMClient,SpotifyClient,Cache,Utils,Domain,Errors runtime
    class Pages,APIs runtime
    class Jobs,RequestCache state
    class LastFMAPI,SpotifyAPI,Postgres external
    class Gunicorn,Release deploy
```

Solid module-to-module arrows are imports. The dotted worker edges are runtime
dispatch through callables injected by `routes.py`; `worker.py` imports neither
pipeline. `config.py` is not drawn: eight of the nodes shown here import it
(`worker.py`, `repositories.py`, `orchestrator.py`, `lastfm.py`, `spotify.py`,
`cache.py`, and `utils.py` at module level, plus `app.py` inside its `__main__`
block), and those edges would cross and hide the flow. The complete import
graph lives in SESSION_CONTEXT Section 4.

Three things this view deliberately makes visible, because breaking them is
silent:

- **One framework stylesheet per page.** `base.html` used to default Bootstrap
  on and every migrated page opted out. The migration finished: no page loads
  Bootstrap or `global.css` any more, and the gate asserts stylesheet isolation
  per page. `global.css` is now dead code awaiting WP-8.
- **The theme is written twice.** `theme.js` sets `data-theme` on `<html>` for
  daisyUI and `shell.css`, and `.dark-mode` on `<body>`. The second write is
  load-bearing even though no stylesheet reads it: `heatmap.js` observes
  `document.body` for `class` so its zero-count cells can be repainted on a
  theme change. An SVG presentation attribute does not resolve a custom
  property, which is why the repaint is JavaScript at all. WP-8 must move that
  observer to `data-theme` in the same change that retires the class.
- **The Spotify cost boundary.** `_MAX_ALBUM_CAP = 500` caps every sort mode
  before any Spotify call, and `partition_albums_by_threshold` splits the
  aggregated albums before enrichment, so albums that miss a play or track
  minimum are written straight to the unmatched repository and cost no Spotify
  quota. `unmatched.py` owns that partition and the stable reason codes;
  `spotlight.py` owns artist sampling for `/api/artist_spotlight`.
