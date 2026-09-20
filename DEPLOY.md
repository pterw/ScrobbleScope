# Deploying to Fly.io

Use the following commands to deploy the application:

```
fly auth signup # or: fly auth login
fly launch --internal-port 8080
fly secrets set LASTFM_API_KEY=... SPOTIFY_CLIENT_ID=... SPOTIFY_CLIENT_SECRET=... SECRET_KEY=...
fly secrets set MUSICBRAINZ_CONTACT=you@example.com   # optional; see below
fly deploy
fly status
fly logs
fly apps open
```

## MusicBrainz contact

`MUSICBRAINZ_CONTACT` enables original-release-year corrections. **It is not a
credential.** MusicBrainz's API requires a contact address in the `User-Agent`
of every request and blocks anonymous clients, so the value is a plain string
that travels in an HTTP header. Nothing authenticates with it and no key is
issued; there is no secret to rotate or leak.

It is set with `fly secrets set` rather than in `fly.toml`'s `[env]` for one
reason only: the value is a personal email address and `fly.toml` is committed.
Either mechanism works. What matters is that the variable is set at all,
because with no contact `lookup_original_release` returns `(None, None)`
without making a request and the correction pass stays disabled -- the default
on a fresh deployment.

The omission is safe rather than silent: a job whose corrections cannot run is
reported as `skipped` by `/api/release_checks`, so the results page says so
instead of showing a correction that never arrived.

## Where the config lives

`fly.toml` and the `Dockerfile` stay at the repository root. Fly resolves the
Dockerfile by co-location with `fly.toml`, which is why `[build]` is empty.
Moving either file breaks that pairing and needs an explicit `[build]` entry
to restore it. `.dockerignore` also resolves from the root. Do not move them
to tidy the root.
