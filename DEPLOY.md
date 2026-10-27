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
credential.** MusicBrainz's API policy requires a contact -- an email address
or a URL -- in the `User-Agent` of every request, and a client that ignores it
risks being throttled or blocked. The value is a plain string that travels in
an HTTP header. Nothing authenticates with it and no key is
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

## Idle exit

`IDLE_EXIT_MINUTES` makes the app machine stop itself. `fly.toml` sets it to
`"20"`: when no request has arrived and no job or release check has been
active for 20 minutes, a watchdog thread (`scrobblescope/idle_exit.py`) sends
SIGTERM to the gunicorn master, which exits with code 0. The machine's restart
policy is `on-failure`, so code 0 leaves it stopped, and the next request
starts it (`auto_start_machines = true`) after a cold start of a few seconds.

Fly's own autostop is off on purpose (`auto_stop_machines = 'off'`). A job runs
in a background thread with no inbound connection, and Fly's docs do not say
whether that counts as load, so autostop could stop a machine mid-job. The app
knows when it is idle; Fly does not.

What an exit costs: jobs and results live in memory, so they are lost on exit
(the database cache stays). The results lifetime therefore changes from
`JOB_TTL_SECONDS` (2 hours) to the 20 idle minutes before the machine stops.
A revisit after that shows the existing "Your results have expired, run a new
search" page. The in-memory request cache and the Spotify token state clear
too.

`IDLE_EXIT_MINUTES` is production-only: it signals the gunicorn master, so do
not set it for `python app.py`. `scrobblescope-db` is a separate app and is not
affected.

To turn the feature off, unset `IDLE_EXIT_MINUTES` or set it to `0`; nothing
starts. Restore `auto_stop_machines = 'stop'` only if you want Fly's autostop
back.

Rollback: revert the `fly.toml` change (restore `auto_stop_machines = 'stop'`
and `min_machines_running = 1`, delete the `[env]` `IDLE_EXIT_MINUTES` line),
then `fly deploy -a scrobblescope`. The Python code can stay: with the variable
unset nothing starts. No secret and no database change is involved.

## Where the config lives

`fly.toml` and the `Dockerfile` stay at the repository root. Fly resolves the
Dockerfile by co-location with `fly.toml`, which is why `[build]` is empty.
Moving either file breaks that pairing and needs an explicit `[build]` entry
to restore it. `.dockerignore` also resolves from the root. Do not move them
to tidy the root.
