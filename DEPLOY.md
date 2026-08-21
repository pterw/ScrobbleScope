# Deploying to Fly.io

Use the following commands to deploy the application:

```
fly auth signup # or: fly auth login
fly launch --internal-port 8080
fly secrets set LASTFM_API_KEY=... SPOTIFY_CLIENT_ID=... SPOTIFY_CLIENT_SECRET=... SECRET_KEY=...
fly deploy
fly status
fly logs
fly apps open
```

## Where the config lives

`fly.toml` and the `Dockerfile` stay at the repository root. Fly resolves the
Dockerfile by co-location with `fly.toml`, which is why `[build]` is empty.
Moving either file breaks that pairing and needs an explicit `[build]` entry
to restore it. `.dockerignore` also resolves from the root. Do not move them
to tidy the root.
