<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0018

### 2026-09-20 - PR #234 advisory verification

Side task, no batch tag. PRs #233 and #234 merged with their review threads
deliberately unaddressed, so adjudicating them was the other half of the
pre-integration task. The question was not "are they open" but "are they
true".

**Method.** Read all threads from the GitHub API (35 review comments on #233,
22 on #234, plus issue comments and reviews), then checked each substantive
claim against on-disk code by grepping the tree, reading the cited function,
or running the cited gate. Nothing was accepted on the strength of a bot's own
summary.

**Result: four refuted, one partly true, one by design, one out of scope.**
Refuted: the DOC023 negation false positive (already handled by
`_NEGATED_OUTCOME_RE`); the `_TERMINAL_SUFFIXES` escaping gap (`re.escape` is
already there, line 354); the `newest == 0` blank-line nitpick (the guard is
deliberate, and `495e9c2` already fixed the real case); and the claim that
DOC023 is documented as both blocking and non-blocking (the catalogue states
the blocking and grandfathered-warning roles as two populations, and the code
implements exactly that). By design: hard-failing a stale archive index
(`DOC020`) is Rule 7's refusal to guess which side of a disagreement is the
history worth keeping. Out of scope by owner ruling: complexity and coupling
advisories, recorded in the report so nobody re-adjudicates them.

**One refuted claim surfaced a real defect.** Graphify rated
"`AlbumMetadata` cache-row method renamed and now requires extra arguments" as
high risk. Nothing calls the method, so nothing broke -- but a repo-wide search
found `as_cache_row` at its definition and in its own test only, while both
production sites build the row tuple inline (`_details.py:137` as six elements,
`_deezer_fallback.py:83` as nine). The persistence order therefore has two
owners, and a test asserts the copy nothing writes. Filed as F-B22-7 rather
than fixed: retiring the method or rerouting a builder is a choice between two
working shapes with a Batch 22 test contract around one of them.

**A vacuity guard earned its place.** The first run of the DOC023 probe used an
`##` heading, which `FINDING_HEADING_RE` does not match, so no finding parsed
and every case read "blocks = False". The output looked like a clean refutation
of the whole claim. Adding a guard that reports `VACUOUS PROBE` when no case
parses caught it; the corrected run is live on 6 of 14 cases with every
expectation met. Recorded because "the gate stayed silent" and "the gate was
never reached" are the same output and different facts.

**Deviations: none.** No production behaviour changed. The two findings are
records, not repairs, and the report is
`docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`.

**Validation:** `pytest -q` -- **1532 passed**, unchanged (no runtime code
touched). `doc_state_sync.py --check` exit 0.

**Forward guidance:** the residual DOC023 false positive ("No action needed
yet." blocks) is deliberate and filed as F-DOCSYNC-14; widening the negation
window would buy silence on two phrases and pay for it by missing real
completion claims, which is the failure the gate exists to prevent. Do not
"fix" it without reading that entry.

### 2026-09-20 - Outbound request identity and the MusicBrainz contact

Side task, no batch tag. Scope was the pre-integration task for `test` into
`main`: API endpoint-fetching compliance, the MusicBrainz HTTP contact, and
agent access to the key documents. PR #236 was opened for the branch.

**Three findings, each verified before repair.** First, no provider request
carried a User-Agent at all: the string `User-Agent` appeared in exactly one
file under `scrobblescope/` (`musicbrainz.py`), and `create_optimized_session`
passed no headers, so every Last.fm, Spotify and Deezer request went out as
aiohttp's default `Python/3.13 aiohttp/3.14.3`. Last.fm's API introduction
asks for "an identifiable User-Agent header on all requests" and warns an
account "may be suspended if your application is continuously making several
calls per second", so this was a compliance gap rather than a style one.
Second, `_musicbrainz_headers` interpolated an unset contact as the literal
string `None`, producing `ScrobbleScope/1.0 ( None )`; the guard in
`lookup_original_release` kept it off the wire, but the helper is reachable
directly and the header's whole purpose is to name a client that can be
contacted. Third, `MUSICBRAINZ_CONTACT` is absent from this worktree's `.env`,
so the correction pass is inert here: a read-only probe returned `(None, None)`
with zero HTTP calls.

**Plan vs implementation: matched.** `APP_VERSION` and `APP_USER_AGENT` moved
into `config.py` as the single owner of the application's own name, and
`create_optimized_session` now sends that User-Agent as a session default.
`musicbrainz.py` dropped its private `_APP_VERSION` copy and composes its
contact-bearing header on the shared identity, so the application cannot name
itself two different ways. Before adding the session default, aiohttp's merge
semantics were measured against the pinned 3.14.3, because the change rests on
them: a per-request `headers=` dict merges with the session default rather than
replacing the header set, so MusicBrainz's own User-Agent still wins and is not
clobbered. `_musicbrainz_headers` now raises when no contact is configured
instead of rendering `None`.

**Deviations: none.** No new dependency, no new module, and no new import edge:
the graph stays `utils.py <- config` and `musicbrainz.py <- config, domain,
utils`, so SESSION_CONTEXT Section 4 needed no change, and `.docsync.toml`
declares nothing about environment variables or User-Agent.

**Agent access to the key documents verified**: all 15 documents in the
bootstrap and orientation set resolve and are readable, including both optional
ones (`docs/AGENT_DOC_MAP.md`, `docs/architecture/documentation-tooling.md`)
and the handoff report. The worktree guard also exits 0 on this branch; its
`WARNING WT010` and `INFO WT000` are the expected states for a development
branch in a linked worktree, not failures.

**Validation:** `pytest -q` -- **1532 passed**, three more than the previous
1529: `test_create_optimized_session_sends_shared_user_agent`,
`test_musicbrainz_headers_refuses_a_missing_contact`, and
`test_musicbrainz_headers_is_derived_from_the_shared_identity`. `ruff check`
and `ruff format --check` are clean on all five touched files.

**Forward guidance:** the code defect is closed, and `MUSICBRAINZ_CONTACT` is
not a secret -- it is a contact string that travels in the User-Agent header,
so setting it is a config change rather than a credential decision. It is
unset here and was absent from DEPLOY.md's own instructions, which is why the
deployed app runs the correction pass off; DEPLOY.md now documents it. The
`main` branch was deliberately not touched -- `test` is the integration branch
and `main` is the stable Fly.io deployment.

### 2026-09-20 - Session close-out and handoff

Side task, no batch tag. The session closed under a token budget, so this
entry records the state rather than the reasoning; the entries below carry
the reasoning.

**Pushed.** Seven commits are on `origin/feat/batch22-enrichment`, from
`3707d6a` to `e57e894`: the work-package tag repair, Batch 22 WP-4 (the
release-check endpoint and its live disclosure), the colour-serialization
class fix, the Batch 22 close-out, the Batch 23 definition with six
corroborated proposals, and the cache repair with the findings rotation. The
branch is **not merged** into `test`; opening a pull request is an owner
decision and has not been taken.

**Handoff written for a new agent**, deliberately assuming no familiarity
with this repository and no particular tooling:
`docs/history/reports/HANDOFF_2026-09-20.md`. It carries the reading order,
the environment, the five ways this repository will refuse a commit and why,
the database-migration fact that hid a dead cache for a whole batch, what
Batch 23 is, and the open items with their findings.

**The owner's inline questions in `FINDINGS.md` are resolved** and have been
removed. They were written after Batch 21 closed, asking why nothing had
rotated; the answer was that no finding carried the lifecycle record rotation
requires, and the rotation in the entry below is the answer in effect. Two of
the removed lines were not questions and were restored: an owner ruling that
the GitHub-to-findings sync must run in both directions, now recorded inside
F-B21-9, and a wrapped line of F-LOAD-2's own prose that a regex mistook for
an annotation because it began with a slash.

Validation: `pytest -q` -- **1529 passed**. `doc_state_sync.py --check` exit
0, its only warning the root definition waiting for Batch 23 to open.

Next action for whoever arrives: read the handoff, then decide the pull
request and whether to open Batch 23.

### 2026-09-20 - The cache was inert, and the findings backlog now rotates

Side task, no batch tag, on the owner's instruction to close Batch 22's
remaining cache and findings work now rather than carry it into Batch 23.
Investigated through `superpowers:systematic-debugging`.

**The metadata cache had been inert since Batch 22 shipped.** The owner's
local database still held the pre-Batch-22 schema: `spotify_cache` had no
`provider`, `provider_album_id` or `provider_url` columns, `spotify_id` was
still `NOT NULL`, and `original_release_cache` did not exist at all. Read
against it, `_batch_lookup_metadata` raised `UndefinedColumnError` and
`_batch_lookup_original_release` raised `UndefinedTableError` -- measured, not
inferred.

The consequence was not an outage, which is why nobody caught it. Both reads
are wrapped, so every job degraded to a cache-less run and carried on: 3,628
usable rows went unread on every search, every album was re-fetched from
Spotify or Deezer, and every MusicBrainz correction was paid for at one
request per second and then discarded. The owner's 2026-09-20 run reads
exactly that way -- `Cache partition: 0 hits, 366 misses` -- and the database
being down at the time hid the second fault behind the first.

`init_db.py` is idempotent and is what fixes it. Run against the live
database: the three columns exist, `spotify_id` is nullable,
`original_release_cache` exists, and all **3,628** existing rows were
backfilled to `provider = 'spotify'` with `provider_album_id = spotify_id`.
Then, against that live database rather than a mock, Batch 22's cache
acceptance criteria were exercised for the first time: a Deezer-only row with
no Spotify id round-trips; a legacy six-tuple caller still writes a row that
reads back as Spotify; a pre-existing row is readable through the cache API
after the backfill; and both a correction and a "checked, nothing found" row
round-trip through `original_release_cache`. The probe rows were deleted
afterwards.

**The class fix, because the instance was a one-line command.** A missing
column is not a transient failure: it never heals, and every read until
someone notices misses a cache that is sitting right there. The code reported
it in the same words as a dropped connection. `scrobblescope/cache.py` gains
`schema_is_out_of_date`, matching PostgreSQL SQLSTATEs 42703 and 42P01 --
matched on the SQLSTATE rather than the asyncpg exception class, because
asyncpg is an optional import here and a SQLSTATE is the stable half of the
contract -- and a single remediation string naming `init_db.py`. Both cache
readers and the correction worker's persist path now say which kind of
failure they hit. Seven tests cover it, including that a transient failure
must **not** tell the reader to run a migration.

This is the same shape as the DOC013-DOC018 gate that had never fired once:
a subsystem reporting success while doing nothing. It is worth naming as a
class -- a failure that degrades silently needs a diagnostic that
distinguishes "will heal" from "will never heal", or it is indistinguishable
from working.

**The findings backlog rotates again.** 85 findings, 83 with no lifecycle
record, so nothing had rotated at either batch close-out -- the owner's
question in `FINDINGS.md` had the right instinct. The owner ruled on
2026-09-20 that a prior session's record may be transcribed, since the
authors are earlier agent sessions and the standing warning confuses a reader
more than an archived finding would.

Each of the 23 grandfathered findings was given the record its own author's
words support, and the distinctions were kept:

- **16 were terminal** and are now in `docs/history/findings/FINDINGS_ARCHIVE.md`
  under their original ids with the `-- RESOLVED` suffix. Where the author
  wrote a date it is theirs; where they wrote none, the completion date is
  the day of the evidence they cite, which is an inference and is recorded
  here as one.
- **5 say "resolved locally, deploy before the next production release"** and
  are NOT checked. The lifecycle gate treats a pending deploy as not-yet
  terminal and it is right to: the fix is in the tree, not in front of a
  user. They keep an unchecked record and stay active.
- **2 were never resolved at all** -- F-B21-9 was deferred by owner decision
  and F-B21-53 is open for the general card token. Reading either as finished
  because the word "resolved" appears in its prose is exactly the mistake
  DOC023 exists to prevent.
- **F-B21-1 was verified in source rather than taken on trust**: loop
  construction now sits inside the `try` in both `background_task` and
  `heatmap_task`, with `release_job_slot()` in the `finally`.

`[findings] grandfathered` in `.docsync.toml` is now `[]`, and **DOC023's
standing warning is gone**. The list stays declared so a repository adopting
this gate starts strict with somewhere to put its own history. Active
findings: 72, down from 85.

Validation: `pytest -q` -- **1529 passed** (was 1522; +7 for the schema
diagnostic). `pre-commit run --all-files` -- all hooks pass.
`doc_state_sync.py --check` exit 0, and its only remaining warning is the
root definition for Batch 23, which is expected while that file waits at the
root. `.docsync.toml` is control-plane, so this commit uses the sanctioned
`SKIP=doc-state-sync-check`, with `--check` run directly first.

Forward guidance: the five "pending deploy" findings resolve themselves the
next time production ships, and their records are the checklist. Nothing
about this change requires a deploy of its own -- but the schema migration
does need running wherever else this app has a database, which on Fly.io
happens automatically, since `init_db.py` is the release command.

### 2026-09-20 - Batch 23 defined, and six owner proposals corroborated

Side task, no batch tag: the owner proposed a different MusicBrainz lookup
strategy, a move from threads to `asyncio` inside Flask, server-sent events
in place of polling, a narrowed Lucene query, and a test-count fix, and asked
for each to be corroborated rather than taken. Nothing in this entry changes
runtime behaviour. `BATCH23_DEFINITION.md` is written but Batch 23 is **not
open**: its branch is unnamed, and naming it is an owner decision.

**Threads cannot run coroutines -- half right, and the half that is wrong
matters.** Measured directly: `threading.Thread(target=an_async_def)` never
runs the coroutine and raises no error, only a "was never awaited" warning,
which is worse than a crash. A thread that creates its own event loop and
calls `run_until_complete` runs it correctly, and that is what
`scrobblescope/release_checks.py` already does. The proposed remedy --
dropping `threading` for `asyncio.create_task()` inside Flask -- cannot work
here: a probe route asked for a running loop and got "no running event loop".
Flask under a WSGI server has no persistent loop to attach a long-lived task
to, so the thread-owns-a-loop pattern is the remedy, not the problem.

**The Gunicorn race condition does not exist today, by configuration.**
`Dockerfile` runs `--workers 1 --threads 4`. One worker means one `JOBS`
dict, one semaphore and one process-wide MusicBrainz limiter.
`AGENT_NOTES.md` already records that a second worker would break the job
store; it would break the rate limiter too, which is the sharper consequence
since MusicBrainz blocks by IP.

**Server-sent events would take the whole thread pool.** Four threads, and an
SSE response holds its thread for the life of the connection: four readers
with a results page open would leave nothing for the home page. Filed as
F-B22-6.

**The MusicBrainz proposal: the exact path is real, the ISRC path is not.**
Probed live against five albums at one request per second.
`GET /ws/2/url?resource=<spotify album url>&inc=release-rels` returns a "free
streaming" relation to a **release** when an editor has mapped that album;
a second request on the release yields the release group's
`first-release-date`. Two requests, exact, no scoring. It answered two cases
today's search path did not -- one where the top candidate scored 100 with no
date at all. It was unmapped for one of the five. Note for the implementer:
`inc=release-groups` on that endpoint returns nothing, and
`inc=release-group-rels` returned zero relations; the include is
`release-rels`.

The ISRC path costs more and is worth less. `GET /v1/albums/{id}` returns
simplified track objects carrying **no** `external_ids`, confirmed by reading
the keys off a live response, so every ISRC needs an extra Spotify request;
and `/ws/2/isrc/{isrc}` returns recordings, whose earliest release group may
be a single rather than the album. Dating an album by its lead single is a
worse answer than no correction.

Also measured: `AND type:album` would exclude EPs, which this application
ranks alongside albums -- `normalize_name` strips "ep" from titles for
exactly that reason -- and the release-group search field is `primarytype`,
not `type`.

All of it is F-B22-5, with the measurements, and the recommendation is to
keep the one-request search as the primary and spend the second request only
where it buys something: no candidate, or a candidate with no date, and a
Spotify id present. **The correction cache must stay keyed on
`(artist_norm, album_norm)`, never on a Spotify id.** The owner's own
2026-09-20 run had Deezer rescue 9 of the 10 albums Spotify could not enrich,
and those albums have no Spotify id at all.

**That run also settles what Deezer is for.** The log shows 356 of 366 albums
matched on Spotify, then 9 of the remaining 10 matched on Deezer, with the
database cache down and every lookup live. Deezer is not only an outage
fallback; it answers for albums Spotify does not carry. The README's
description was written for the outage case and now says both.

**The test count.** `--fix` cannot publish a measured count and `--check`
refuses a hand-written one, because `latest_test_count_authority` parses the
number out of prose in dated entries and DOC005/DOC006/DOC008 recompute that
parse. Rule 7 is why the tool does not simply run pytest: it may rewrite only
what it can derive from facts a human authored, and measuring the world is
not that. Filed as F-DOCSYNC-13 with a proposed shape -- an authored
measurement passed in, written by `--fix` into all four sites -- for the
owner to rule on.

**Batch 23's definition** is derived from the approved plan, in this
repository's own work-package form: WP-0 behaviour-neutral extractions, WP-1
error codes, WP-2 the pure parser and aggregators, WP-3 the job hand-off,
WP-4 routes and upload handling, WP-5 the interface, WP-6 the new statistics
for both sources, WP-7 documentation, the deferred Batch 21 accessibility
audit and close-out. The audit is inside WP-7 because the owner ruled on
2026-09-13 that this batch cannot close without it.

**A wording trap worth knowing.** Section 3's "Batch 23 is not yet defined"
has to sit on one line: the state parser reads Section 3 line by line, and
wrapping that sentence across two lines made the gate infer an active batch
and demand a definition declaration. The same class of defect, in the other
direction, was fixed during the docsync close-out.

Validation: `pytest -q` -- **1522 passed**, unchanged (no runtime code was
touched). `doc_state_sync.py --check` exit 0, with the expected DOC023
warning and the root-definition warning that is normal for a batch with a
definition at the root. The live probes were read-only: Spotify with the
app's own credentials, MusicBrainz with a contact-bearing User-Agent at one
request per second.

### 2026-09-20 - Batch 22 work-package tags, and the docsync side task closed

Side task, no batch tag: bookkeeping repair found while orienting for WP-4,
plus the close-out of the docsync work the entry below tracks. No code
changed and no batch scope moved. The unrelated in-flight Batch 22 edits in
this worktree (the mutation runner, `graphify_refresh.py`, `AGENT_NOTES.md`,
`requirements-dev.txt`) were neither staged nor reverted.

**PR #234 merged** as `88f6e27` into `test`, so the docsync close-out side
task is finished and `feat/batch22-enrichment` is now fully contained in
`origin/test`. The gitignored `CLAUDE.md` section that tracked it asked to be
deleted on that merge, and was.

**The defect: six current-batch entries carried the wrong work-package tag.**
Every entry from Task 5 onward was headed `(Batch 22 WP-1)`, including the
Task 6 work that belongs to WP-2 and the Tasks 7-8 work that belongs to WP-3.
That tag is not decoration: `ENTRY_BATCH_RE` in `scripts/docsync/parser.py`
parses it, and the managed STATUS block in `.claude/SESSION_CONTEXT.md` is
derived from what it finds. The dashboard therefore read "WP-0, WP-1, WP-3"
and never named WP-2 at all -- a cold-resume reader would have seen the
Deezer fallback as work nobody had done. Retagged against the definition's
own task-to-WP map: Tasks 5-6 and both README passes to WP-2, Tasks 7-8 to
WP-3. Tasks 1-3 were already correct.

**Why this overrides the note that left the tags alone.** The Task 8 entry
above recorded a decision to keep its WP-1 heading as "its historical commit
record". That reasoning treats the tag as prose. It is an index key, and the
scope to fix it across six entries is exactly what that session said it
lacked. The superseding note now sits in that entry. The declines recorded in
F-DOCSYNC-3 are a different case and still stand: they cover content the tool
has already rotated into an archive, not live entries that have not rotated
yet.

**Also repaired:** `BATCH22_DEFINITION.md` still showed Task 9 unchecked while
its own header and Section 3 both said Tasks 7-9 were complete; the WP-3
heading now carries the struck-through DONE form its three siblings use.
F-B21-60 and F-B22-4 cited "Batch 22 WP-1 Task 6" in three places and now cite
WP-2.

**Known remaining instance, recorded rather than fixed:** F-DOCSYNC-12's
`Source:` line reads "Batch 22 WP-1, DB-connect-timeout side task". A side
task has no work package, so the right correction is not a different number,
and inventing one would trade a visible error for an invisible one.

**Two findings filed.** F-SWE-8 records the mutation-test runner's
disposition -- built, never adopted, four defects on first use, uncommitted,
its own future work package. It lived only in the gitignored `CLAUDE.md`, so
deleting that section would have erased it from the corpus entirely.
F-DOCSYNC-3 gains a second instance: Batch 22's Task 4 entry was headed
`(Batch 22 WP-1, Phase 2 begins)`, and the trailing clause inside the
parentheses made the heading unparseable as batch-tagged, so rotation sent it
to the monolith archive instead of a per-batch log. The defect is wider than
the `(Batch N close-out)` suffix the finding first described, and the tool
says nothing when it happens.

Validation: `pytest -q` -- **1497 passed**, unchanged (documentation only).
`doc_state_sync.py --check` exit 0, with the expected DOC023 grandfather
warning and the root `BATCH22_DEFINITION.md` warning. The frontend gate was
not rerun: nothing under `templates/` or `static/` changed, so the last
recorded result stands.

Forward guidance: Batch 22 WP-4 is next -- Task 10, the job-scoped
`GET /api/release_checks` endpoint, then Task 11's live disclosure. Two gaps
between the plan text and the code as built land on Task 10. The plan says
the endpoint reuses `_get_validated_job_context`, which renders `error.html`
and returns HTML; its JSON neighbours return JSON error bodies, so a
JSON-shaped validation path is needed. The plan's payload also carries
`original_release_date` per album, but Task 9's worker writes only
`{"release_check": ...}` through `update_job_result`, so the corrected date
never reaches the result and the worker has to write it.

### 2026-09-20 - Docsync review round, DOC023, and PR #234

Side task, no batch tag: close-out of
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`. Not Batch 22
scope. The unrelated in-flight Batch 22 edits in this worktree were neither
staged nor reverted. Ledger:
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.

The whole-branch review had to be split: `/ultrareview` caps at 500 files and
8,000 lines against the working tree, and this work package was 52 files and
12,403 lines. The engine commit was reviewed alone from a temporary branch.
Every reported finding across ultrareview, Codacy, Graphify and qlty was
reproduced or refuted before being acted on -- roughly twenty reports produced
eight real defects. Refutations included a "high" that was an artifact of
where the review scope was cut and healed by the next commit, and three qlty
correctness items that were analyzer flow-model false positives.

Defects fixed, each with a regression test proven to fail without its fix:
archive pages were packed in reading order while every producer prepends, so
one rotated entry repacked the whole archive and returned cold pages to hot;
`--close-batch` restated the closure date from the clock; findings rotated to
the bottom of an archive whose prologue says newest first; the hook installer
resolved a relative `core.hooksPath` against cwd and wrote through a
pre-existing symlink onto its target; close-out `assert`s guarded a publish
and vanish under `python -O`; the preflight re-encoded a text-mode tar payload
and extracted unfiltered below Python 3.12.

DOC023 closes the finding-rot hole: all 83 findings lacked the canonical
`- [ ] **Status:**` record, so DOC013-DOC018 had never fired once. It blocks a
finding whose prose claims a terminal outcome without that record. The
boundary is an explicit id allowlist in `[findings] grandfathered`, not the
batch number the plan specified -- 32 of 83 ids are source-tagged and carry no
batch to compare, so a boundary would grandfather them by accident and let a
new finding escape by choosing a tag. 23 ids are grandfathered and reported as
one warning carrying a count derived from the file on every run.
`docs/agents/global-rules.md` was also added to Session Bootstrap, which it was
missing from despite being binding.

Validation: `pytest -q` -- **1497 passed**; `doc_state_sync.py --check` exit 0;
`frontend_gate.py` exit 0; `AGENTS.md` 473 lines against its 500 cap. Eighteen
commits on `feat/batch22-enrichment`, nothing unpushed, open as PR #234 into
`test`.
