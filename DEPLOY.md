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
A revisit after that shows the existing "We couldn't find your results. The
processing may have expired. Please try again." page (or, for a saved session
job, "Your previous results have expired. Run an album search to build a new
ranking."), not a crash. The in-memory request cache and the Spotify token state clear
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

## Deezer blocks the machine's egress address

Symptom: the Results page says "Deezer could not be reached for some albums"
on every run, local runs are fine, and the log summary shows
`Deezer: N calls ... Nx403`. Deezer's CDN (Akamai) refuses requests from the
machine's outbound IPv4 address. Fly's default egress is the host's address,
which can change, so the block follows the address, not the code. A Deezer
403 is sent once and reported as unavailable, never retried and never read as
"no match".

To confirm, probe from the machine (Git Bash quoting):

```bash
fly ssh console -a scrobblescope -C "python -c \"import urllib.request as u,urllib.error as e
ip=u.urlopen('https://api.ipify.org',timeout=10).read().decode()
try:
  s=u.urlopen(u.Request('https://api.deezer.com/search/album?q=radiohead&limit=1',headers={'User-Agent':'ScrobbleScope/probe'}),timeout=10).status
except e.HTTPError as x:
  s=x.code
print('PROBE',ip,s)\""
```

It prints `PROBE <egress-ip> <status>`. `200` is healthy; `403` means Deezer
blocks this machine's address. Add `--machine <id>` to probe one specific
machine.

Free fix: clone the machine onto another host, check the clone, then destroy
the blocked machine. The clone keeps the machine's config (env, restart
policy, autostop).

```bash
fly machine clone <blocked-id> --region yyz -a scrobblescope
```

Probe the clone with the probe above plus `--machine <new-id>`. If it prints
`200`, destroy the blocked machine:

```bash
fly machine destroy <blocked-id> --force -a scrobblescope
fly machine list -a scrobblescope
```

The list must show one machine, and it must still carry `IDLE_EXIT_MINUTES`.
If the clone's address is also blocked, destroy the clone and clone again. In
the incident the clone landed on the next address of the same /24 and Deezer
answered 200, so Akamai had blocked one address, not the range.

Paid fix: a static egress IP, which costs $3.60 a month at the time of
writing (the owner's ceiling is machine plus cache under $5 a month).

```bash
fly ips allocate-egress -r yyz -a scrobblescope
fly ips list -a scrobblescope
fly ips release-egress <ip> -a scrobblescope
```

The first command allocates it, the second reads it, the third drops it. In
the incident it did make Deezer answer 200. It was released on the owner's
word to test whether a machine restart would clear the block, and it did not
(a restart and a redeploy kept the same blocked address).

A deploy or a restart does not change the egress IP: `fly deploy` updates the
machine in place (same id, host and IP). Only a new machine on another host
does, and the idle exit makes the machine stop and start often, so a block
can come back.

Possible issue: this can happen again. A new machine on another host gets a
new egress address that Akamai may block, and closing the incident finding
does not remove that risk. If Deezer starts returning 403 on every run, use
the recipe above before looking at the code.

The incident record is finding `F-OPS-1` in
`docs/history/findings/FINDINGS_ARCHIVE.md`; this section is the recipe only.

## Where the config lives

`fly.toml` and the `Dockerfile` stay at the repository root. Fly resolves the
Dockerfile by co-location with `fly.toml`, which is why `[build]` is empty.
Moving either file breaks that pairing and needs an explicit `[build]` entry
to restore it. `.dockerignore` also resolves from the root. Do not move them
to tidy the root.
