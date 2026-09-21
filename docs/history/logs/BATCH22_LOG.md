# Batch 22 Execution Log

Archived entries for Batch 22 work packages.

### 2026-09-20 - The release-check JSON endpoint (Batch 22 WP-4)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 10, the first task of WP-4. `GET /api/release_checks?job_id=` serves the
correction worker's findings to a results page that is already open. Task 11
consumes it; nothing renders these yet.

`scrobblescope/routes/api.py`: the endpoint returns `{status, checked, total,
moved_in, albums}`, where each album carries `key`, `state` and
`original_release_date`. It lists only results the worker has ruled on --
a result still `unchecked` is omitted, because the page has already rendered
every row and the only thing it needs back is what changed.

`scrobblescope/domain.py`: `format_album_key` returns the `artist|album` wire
form of a normalized key. The endpoint and Task 11's `data-album-key` must
name an album identically, so the join lives in one function rather than
being spelled the same way in two places. The separator is safe by
construction: `normalize_name` replaces every ASCII punctuation character
with a space, so neither half can contain a pipe.

**Deviation 1 -- the plan says the endpoint "reuses
`_get_validated_job_context` for ownership and mode checks". It does not.**
That helper renders `error.html` and returns HTML on both its failure paths,
which a polling client cannot read. The endpoint does the same two checks
(unknown job, wrong mode) and answers in JSON, as `/progress` and
`/api/unmatched` beside it already do. Ownership is unchanged from every
other job endpoint: the 128-bit job ID is the capability and there is no
session check. F-B22-3 holds that open question for the owner; this task
did not decide it one way or the other.

**Deviation 2 -- an error body carries `"status": "error"`.** The plan
specifies no error shape. The word is deliberately not one of the worker's
own four, so Task 11's poller stops on it by the same rule that stops it on
any status it does not recognise.

**`pending` is the fifth status, and the worker never writes it.**
`BATCH22_DEFINITION.md` WP-3 lists `pending` among the states to expose, but
the worker publishes `running`, `done` or `skipped` and publishes nothing at
all before it starts. `pending` is what the endpoint reports while
`progress.stats.release_check` is absent -- the gap between a job publishing
results and the worker first reporting on them. `STATUS_PENDING` is declared
in `scrobblescope/release_checks.py` with the other three so the vocabulary
stays in one module.

**Task 9 extended, under this task.** The worker wrote only
`{"release_check": outcome}`, so no corrected date ever reached the result
and the endpoint had nothing to serve: a moved-out row would have shown the
provider's reissue date while claiming to be a correction of it. Both
settling paths in `scrobblescope/release_checks.py` now write
`original_release_date` alongside the outcome -- the live one in
`_check_candidate`, the cached one in `_resolve_cached` -- and an
`unavailable` result records None rather than keeping a value the new
outcome contradicts. Seven lines, inside WP-4's own dependency, so it is an
in-WP deviation under AGENTS.md Proposal and Design Rules item 2 rather than
a new work package.

Tests (+9): seven in `tests/test_routes.py` covering the missing-ID 400, the
unknown-job and heatmap-job 404s in JSON rather than HTML, the `pending`
default, the filtering of unchecked results, the normalized key on an album
whose title is all punctuation and metadata words, and a result with no
`_normalized_key` being skipped instead of crashing the endpoint. Two in
`tests/services/test_release_checks.py` assert the date behind each of the
three outcomes and the same field written from a cache hit without spending
a request.

Validation: `pytest -q` -- **1506 passed** (was 1497; +9 new). The managed
STATUS block and the three hand-written count fields still read 1497, and
that is not drift: the untagged side-task entry below the end marker is also
dated 2026-09-20 and claims 1497, and on a same-date tie source precedence
ranks a side-task entry above any current-batch entry regardless of which
was written later. This is **F-DOCSYNC-11** (open, P1), not a new defect,
and its own stated remedy is to publish the superseded number and let the
entry carry the true one -- the Task 8 entry above did the same thing on the
same mechanism. DOC005/DOC006/DOC008 recompute that authority and reject a
hand-written 1506. `ruff check` and `ruff format` clean. The frontend gate was not rerun: nothing under
`templates/` or `static/` changed, so Task 11 is where it next earns its
run. `doc_state_sync.py --check` exit 0 (the root `BATCH22_DEFINITION.md`
warning is expected while the batch is active).

Forward guidance: Task 11 renders this. It needs `data-album-key` on each
results row carrying `format_album_key`'s output, a status line reading
"Checking original release years: N of M" from `checked`/`total`, per-row
markers that do not move a row, and the moved-in announcement from
`moved_in` with a reload action. Polling stops on `done`, on `skipped`, on
any unrecognised status, and on a failed request.

### 2026-09-20 - Live release-year disclosure (Batch 22 WP-4)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 11, which closes WP-4. The results page now polls Task 10's endpoint and
discloses corrections as they land, under the owner's progressive-disclosure
ruling: results render at once, a corrected row stays exactly where it is,
and the list re-sorts only on reload.

`static/js/results-release-checks.js` (new, split from `results.js` the way
`results-spotlight.js` already is): polls `GET /api/release_checks` every two
seconds, pauses while the tab is hidden, and stops on any status that is not
`pending` or `running`. Stopping on the *absence* of a live state rather than
on a list of terminal ones is why Task 10 answers `error` for a missing job:
a word this script has never heard of has to stop it, not slip through.

`templates/results.html`: each row carries `data-album-key`, rendered through
a new `album_key` Jinja filter so the row and the endpoint name an album by
one function (`scrobblescope.domain.format_album_key`) rather than two
spellings of the same join. The status line is rendered **with the page**,
from the job's own `release_check` state, not created when the first reply
arrives: it sits above the table, so injecting it later would push every row
down, which is the one movement the ruling forbids. It is absent entirely
when the pass is `skipped` or already `done`, and `results.js` removes it if
the pass ends with nothing to report.

The marker goes inside the release cell, under the date. That cell is shorter
than the row's artwork, so a corrected row gains a line without gaining
height, and the gate measures every row's top before and after to prove it.
A `moved_out` row shows its original year in place of the provider's reissue
date, with a muted mono kicker linking to the unmatched report and an
`aria-label` carrying the full sentence. `confirmed` and `unavailable` rows
are marked in the DOM but show nothing: neither tells a reader anything the
row does not already say. Moved-in albums are announced as a count plus a
reload action, never inserted.

**A gate finding that was the gate's own defect.** The new contrast check
reported the note at 3.78:1 against the table surface, then 3.22:1 after a
recolour, then 1.19:1 against the page's own ink -- a figure no theme could
produce. `_parse_rgb_string` reads the first three numbers out of a computed
colour and treats them as 0-255 channels, but the results surface is a
`color-mix()`, which a browser serializes as `color(srgb 0.96 0.94 0.91)`
with channels in 0-1. Every such surface collapsed to near black.
`scripts/dev/_frontend_gate_colour.py` now scales that form, with a unit test
pinning both serializations. The real ratios clear the 4.5:1 text floor in
both themes -- muted 4.90:1 light and 5.59:1 dark -- so the note kept the
muted treatment the design called for, and two changes made to satisfy a
false measurement were reverted. The defect was not new: any check measuring
a `color-mix()` surface was reading a different colour than the one on screen.

**Filed, not fixed:** F-B21-62. `docs/design/README.md` names `--ss-warn`,
`--ss-good` and `--ss-bad` and says a mono kicker is exactly what they are
for, but no stylesheet defines them, and a page may not read a token its own
sheets do not define. The first attempt to use the documented treatment had
to pick another token.

Tests (+6): five in `tests/test_template_shell.py` -- the row key matching
`format_album_key`, an unkeyed result rendering an empty attribute rather
than breaking the page, the status line being in flow from first paint with
its `role="status"` and `aria-live`, its absence when there is nothing to
check, and the poller continuing on the live states only with no
`setInterval` (F-B21-33). One in
`tests/scripts/dev/test_frontend_gate_colour.py` for the `color(srgb ...)`
serialization.

Gate: `check_release_check_disclosure` scripts two replies and proves WP-4's
acceptance conditions -- no row moves when a marker lands, the corrected
row shows its original year and links to the unmatched report, the note
clears the text-contrast floor, moved-in albums get a reload action, polling
makes no further request after a terminal status, and nothing overflows at
390px or 1280px.

Validation: `pytest -q` -- **1512 passed** (was 1506; +6). The frontend gate
-- **30 checks passed in 52 runs** across chromium and firefox (was 29 in 50;
this task adds one check, and the run count follows).
`ruff check` and `ruff format` clean. `doc_state_sync.py --check` exit 0 with
the expected root-definition and DOC023 warnings. The count the managed block
and the three hand-written fields carry is still the superseded 1497, for the
F-DOCSYNC-11 reason the Task 10 entry above records.

Forward guidance: WP-5 is next -- README for the new environment variables
and the MusicBrainz contact, the Deezer non-commercial constraint,
`docs/architecture/runtime-system.md` for the release-year source, then the
standard close-out. Two items belong in that pass: neither the worker nor
this endpoint appears in SESSION_CONTEXT Section 5's architecture overview,
and `docs/design/RECONCILIATION.md` still needs the plan's note that a
displayed release year may now come from MusicBrainz rather than the
provider.

### 2026-09-20 - The colour-serialization audit and its class fix (Batch 22 WP-4)

Scope: the owner asked whether any existing check was failing the same way
Task 11's contrast check did, and for the class to be remediated rather than
the instance. Investigated through `superpowers:systematic-debugging`:
evidence first, then one hypothesis, then the fix.

**Evidence.** A probe drove both engines the gate runs, in both themes, and
printed the exact string `getComputedStyle` returns for every colour any
check reads. Both Chromium and Firefox serialize a computed
`color-mix(in srgb, ...)` as `color(srgb 0.960784 0.945098 0.909804)`, with
channels in 0-1. Every other measured value -- `--shell-border`,
`--shell-bg`, `--shell-surface`, `--color-base-100`, `--ss-surface-sunken`,
`--color-primary`, `--color-base-content`, `--ss-text-muted`, and
`.index-form`'s rendered border -- came back as `rgb()` or `rgba()` in both
engines and both themes.

**Finding: no existing check was wrong.** `_parse_rgb_string` has exactly two
callers, `check_divider_contrast` (through `_worst_divider_contrast`) and
Task 11's new contrast check. The divider check reads only tokens that
serialize as `rgb()`/`rgba()`, so its measurements were correct. The defect
was latent, and Task 11's check was the first to measure a `color-mix()`
surface -- `--results-surface` is one. Two other colour tokens are built from
`color-mix()` (`--color-base-300`, and the accent hover on `.results-action`)
and no check measures them.

**The class fix, in two parts.** The parser now recognises `color(srgb ...)`
and **refuses** any serialization it does not understand -- `oklch()`,
`lab()`, `hsl()`, `color()` in a wider gamut -- with a message naming the
value and saying to teach it the form. All of those lead with three numbers
that are not sRGB channels, so the previous behaviour was to return a
plausible ratio for a colour nobody painted, and a contrast gate reporting a
wrong ratio is the wrong green `docs/agents/global-rules.md` ranks above
every other rule. The generated stylesheet carries 46 `oklch`/`oklab`
occurrences, so the form is one theme change away from being measured.

Second, the forbidden-surface scan compared strings. It reads every element
on a page for the cool-greys the warm themes replaced, so the same grey
arriving through a `color-mix()` would have serialized as `color(srgb ...)`
and passed the scan with the surface on screen. It now compares colours
through `_is_forbidden_surface`, which normalises both sides and falls back
to an exact string match for anything the parser refuses -- a scan over every
element cannot raise, which is the opposite trade from a measurement, and
both are stated where they are made.

Tests (+10 net): `TestColourSerializations` pins both readable forms and
parametrises the four refusals; `TestForbiddenSurfaceDetection` pins the
cross-serialization match, the plain match, a non-match, and the tolerated
unparseable value. The standalone test written during Task 11 was folded into
the first class rather than left beside it.

Also in this entry: the two findings this session filed (F-SWE-8, F-B21-62)
now carry the canonical `- [ ] **Status:**` lifecycle record from
`docs/agents/issue-tracker.md`, so they are rotation-eligible when they close
and the backlog DOC023 counts does not grow. F-DOCSYNC-3 keeps its prose
status line: it is another author's record, and converting one is not this
session's to do (Rule 7).

Validation: `pytest -q` -- **1522 passed** (was 1512; +10). The frontend gate
-- **30 checks passed in 52 runs** across chromium and firefox, green with
the strict parser, which is itself the proof that no check feeds it a
serialization it refuses. `ruff check` and `ruff format` clean.
`doc_state_sync.py --check` exit 0.

### 2026-09-20 - Documentation for the providers and the correction pass (Batch 22 WP-5)

Scope: Phase 4 of
`docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md` -- the new
environment variables, the MusicBrainz contact requirement, the Deezer
constraint, and the runtime and design records of where a release year now
comes from. No code changed.

`.env.example` gains `MUSICBRAINZ_CONTACT` (empty, with the reason it must be
a real address: it travels in the User-Agent, and MusicBrainz blocks
anonymous clients) and `MUSICBRAINZ_ENABLED`. The rate limits, retry counts,
per-job cap and cache TTLs are named as environment-readable and pointed at
`scrobblescope/config.py`, which owns each default -- listing the values here
would be a second copy of a fact the code already owns.

`docs/architecture/runtime-system.md`, the canonical runtime view, drew none
of Batch 22. It now carries `deezer.py`, `musicbrainz.py`, `enrichment.py`
and `release_checks.py`, the two new external APIs, `original_release_cache`,
`/api/release_checks`, and the function-scoped import back into the
orchestrator that keeps that cycle open. Two new notes say why a displayed
year may not be the provider's and why the correction worker is one thread.
Its Browser node also still described `.dark-mode on body`, which the same
file's own bullet says WP-8 retired -- the node was the stale half of that
contradiction and is now `data-theme on html`. The diagram was validated as
a diagram, not just edited as text.

`docs/design/RECONCILIATION.md` section 17 records the same fact for the
design system: the Release column now has two possible sources, a corrected
row carries a mono kicker following the page's quiet-link treatment, and the
kicker is not a status colour because no stylesheet defines one (F-B21-62).

`.claude/SESSION_CONTEXT.md` Section 5's overview named neither the Deezer
fallback, the correction worker nor either polling loop; all four are now in
it.

**README, and a deviation recorded.** The owner ruled mid-session that
`README.md` is a human-read document and must describe the system rather than
delegate to other files. That overrides its previous habit of pointing at
PLAYBOOK and FINDINGS for status, and it is a deliberate exception to the
anti-duplication rule for this one file, made by the owner who owns that
rule. The rewrite adds: what each module owns; how a search runs end to end,
in eight steps from the typed username to the corrections landing on an open
page; what `utils.py` actually provides, since the two-level rate limiter is
the reason the pipelines survive a bad provider day and it was described
nowhere; a fuller request-lifecycle diagram; and a roadmap that describes
Batch 23's Spotify export import -- no login, parsed in memory, nothing
stored -- along with the statistics it adds and five honest known
limitations. Badges now show the stack and the deployment as well as CI, and
deliberately carry no hand-maintained test or coverage number: the README
says so, because the previous file said the same thing and it is still the
right call.

Validation: `pytest -q` -- **1522 passed**, unchanged (documentation only).
`pre-commit run --all-files` -- all hooks pass. `doc_state_sync.py --check`
exit 0. Both Mermaid diagrams validated through the Mermaid Chart renderer,
and every one of the README's 24 internal anchors resolves to a heading in
the file.

Deviations: the plan's Phase 4 also lists renaming the Batch 23 plan file and
repointing its references. That was done when the plan was written; the file
is already at its Batch 23 name and PLAYBOOK Section 3, F-B21-59 and F-B21-60
already cite it there, so there was nothing to rename.

Forward guidance: close-out is the last step of this batch. Two live
verifications from the plan need the owner rather than the gate: a run with
`MUSICBRAINZ_CONTACT` set, to watch corrections land against the real
service, and restoring Spotify credentials after the Deezer-fallback test.
Neither blocks the close-out -- every acceptance criterion that can be
checked mechanically is checked -- but both are named here so they are not
lost.

### 2026-09-20 - Batch 22 close-out (Batch 22 WP-5)

Batch 22 is complete. Six work packages: the behaviour-neutral module split,
the provider contract, the Deezer fallback, the original-release backend, the
live disclosure, and the documentation pass. The definition is archived at
`docs/history/definitions/BATCH22_DEFINITION.md`, and PLAYBOOK Section 2 now
carries a row pointing at it and at the batch log.

Against the definition's own batch-acceptance list, item by item and where
each is proven. Spotify success does not call Deezer, and a Spotify failure
produces a fully attributed Deezer result: service tests, plus the owner's
live run on 2026-09-20 with the Spotify credentials disabled, which worked.
Cache reads and writes round-trip either provider without a Spotify id, and
existing rows stay valid: cache and schema tests. A cached 1977 original
against a 2011 provider date drives both the filter decision and the
displayed date, with the provider's date retained separately: orchestrator
tests. MusicBrainz stays disabled without a contact, respects one request per
second when enabled, and never blocks the first render: client, worker and
limiter tests. Live corrections are job-scoped, stop at a terminal state,
stay accessible and never reorder the open list: route tests, template tests,
and the browser gate measuring every row's top before and after a marker
lands. The full suite, the two-browser gate, pre-commit and
`doc_state_sync.py --check` all pass on this state.

**Two verifications are owner-facing and remain open**, named here rather
than left implied. Neither blocks the close-out; both are live-service checks
no gate can make. First, a run with `MUSICBRAINZ_CONTACT` configured, to
watch corrections land against the real service and confirm the pacing in the
logs -- `.env` carries no contact today, so the pass has only ever run
against scripted replies and cached rows. Second, restoring the Spotify
credentials that were disabled to test the Deezer fallback.

**Deviations carried out of this batch**, each recorded in its own entry: the
release-check endpoint validates in JSON rather than through
`_get_validated_job_context`, which renders HTML; the correction worker
writes the corrected date onto the result, which Task 9 did not; the status
line renders with the page rather than on the first reply, because it sits
above the table; and provider attribution ships as text rather than each
provider's official logo asset, an owner-accepted interim recorded as
F-B22-4.

**Filed during the batch and still open:** F-B22-4 (the provider logo
assets), F-B21-62 (the design system's status colours are documented but
undefined), F-SWE-8 (the mutation-test runner, built and unadopted), and a
second instance on F-DOCSYNC-3 -- any extra text inside a heading's
parentheses defeats the batch tag, not only the close-out suffix. This
entry's own heading carries `(Batch 22 WP-5)` for that reason, so rotation
routes it to the batch log rather than the monolith.

Validation: `pytest -q` -- **1522 passed**. The frontend gate -- **30 checks
passed in 52 runs** across chromium and firefox. `pre-commit run --all-files`
-- all hooks pass. `doc_state_sync.py --check` exit 0.

### 2026-09-15 - The correction worker (Batch 22 WP-3)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 9, which closes the loop Task 7 and Task 8 left open. Task 7 built the
MusicBrainz client and Task 8 applied findings that were already cached;
until now nothing wrote a new one, so `lookup_original_release`,
`_batch_lookup_original_release` and `_batch_persist_original_release` had no
production caller at all.

`scrobblescope/release_checks.py` (new): one process-wide daemon thread with
its own event loop (`ProactorEventLoop` on Windows, for the reason
`orchestrator.background_task` already documents) draining a FIFO
`queue.Queue` of job ids. One thread, not a pool: MusicBrainz allows one
request per second per IP and `utils.get_musicbrainz_limiter()` enforces that
process-wide, so extra threads would queue behind the same limiter while
multiplying DB connections and the ways a job's state can be raced. The
thread starts lazily, on the first job that can use it, so a process that
never runs one -- a test session, a CLI script -- never grows it.

Candidates per job, in the plan's order: the results in rank order (a
correction can move one out), then the release-scope exclusions whose
provider year is **later** than the target window's last year (a correction
can move one in). Nothing else can change, because an original release date
is never later than the provider's own. `_select_candidates`, `_window_end`
and `_release_year` are pure and tested directly. Each result gains a
`release_check` field -- `unchecked`, `confirmed`, `moved_out` or
`unavailable` -- and `progress.stats.release_check` holds `{status, checked,
total, moved_out, moved_in}` with `status` one of `running`, `done`,
`skipped`. A move-out marks the result in place and is counted; a move-in is
counted only, never inserted, so a results list somebody is reading is not
reordered underneath them.

Three design points the plan left open, decided here. **Cache hits cost no
request and still settle the result:** a cached row carrying an original date
is why the album passed the filter at all (Task 8 filtered on it), so the
result is `confirmed`; a cached null row is a recorded "checked, nothing
found", so it is `unavailable`. The cap therefore applies to what is left
after the cache short-circuit, because the cap exists to bound requests.
**Findings are persisted one row per check, not batched at the end:** the
worker spends about a second per candidate and a job lives two hours, so a
finding held in memory until the end is a request nobody gets back if the
process restarts. **No cache DB means no run:** the pass is marked `skipped`
without requesting anything, since a finding that cannot be persisted buys
one job's display and nothing for the next, at the shared budget's expense.
The worker also re-reads the job before every candidate and stops when it is
gone (`JOB_TTL_SECONDS`), and returns without raising in every failure mode:
a correction pass is an enhancement over results the user can already read.

`scrobblescope/repositories.py`: `set_job_release_check(job_id, state)`
replaces the whole stats payload rather than merging (the worker owns the key
and always knows the full state, so a merge could only preserve a stale
count) and copies on write; `update_job_result(job_id, album_key, fields)`
merges into the one result whose `normalize_name(artist, album)` matches
`album_key`, returning False when the job is gone, has no results list yet,
or holds no such album. Result dicts carry no pre-normalized key, which is
why the key is derived per entry rather than looked up.

`scrobblescope/orchestrator/__init__.py`: `_fetch_and_process` calls
`enqueue_release_check(job_id)` immediately after `set_job_results` on the
happy path only. The worker picks its candidates out of the stored results,
so an earlier hand-off would find nothing, and the error paths publish an
empty list, which has nothing to correct. `enqueue_release_check` is imported
at the top of the facade, and `release_checks` reaches
`_matches_release_criteria` through a function-local import: the two modules
would otherwise form an import cycle whose behaviour depends on which one is
imported first.

`scrobblescope/orchestrator/_results.py`: `provider_release_date` is now
attached to every release-scope unmatched entry, not only a corrected one. It
was half-wired in Task 8 (corrected entries only); the worker reads it back
off the unmatched entry to decide which exclusions a lookup could still move
in, and an *uncorrected* exclusion is exactly the case it exists to resolve,
so without this it could not build that candidate list at all.

Tests (31 new): `tests/services/test_release_checks.py` (22) covers the
candidate list and its order, the four exclusion rules that make an unmatched
album unmovable, the cap, the cache short-circuit including a null row,
`moved_out` marking a result without removing it from the list, the full
stats shape with a counted-not-inserted move-in, a job deleted mid-run
stopping the worker, `MUSICBRAINZ_ENABLED=False` and an unreachable DB both
marking `skipped` with no request, a "nothing found" row still being
persisted, connection close on a raising lookup, and the queue/thread
lifecycle. `tests/test_repositories.py` (+6) and
`tests/services/test_orchestrator_fetch_and_process.py` (+2, including the
error path *not* queueing) assert on the shared `JOBS` state rather than mock
calls. `tests/services/test_orchestrator_process_albums.py` (+1) covers the
uncorrected `provider_release_date`. The cap and the job-gone guard were each
disconnected in turn and the matching test failed, then passed again on
restoration.

Validation: `pytest -q` -- **1298 passed**. That figure is measured in a
worktree that also carries a concurrent, uncommitted docsync work package
from another session, so it is not comparable to the 1088 the entry above
records. Task 9's own contribution is +31 (22 + 6 + 2 + 1, per the file list
above). No frontend change, so the frontend gate is unaffected and its last
29/29 measurement stands.

Deviation, logged rather than swept: `pre-commit run --all-files` reports
`ruff` failures in `scripts/docsync/`, files this task does not touch and
does not stage. They belong to that concurrent docsync work package. The
staged-path hook run for this commit passes.

### 2026-09-14 - MusicBrainz client (Batch 22 WP-3)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 7, the first task of Phase 3. New module, no caller wired yet (Task 8
consumes it).

`scrobblescope/musicbrainz.py` (new): `lookup_original_release(session,
artist, album)` returns `(mb_release_group_id, "YYYY-MM-DD")` on a trusted
match or `(None, None)` -- both cacheable, matching
`original_release_cache`'s null-`mb_release_group` "checked, nothing
found" row from Task 2. A candidate is accepted only when its MusicBrainz
`score` is at least 90 **and** its normalized artist-credit/title match the
searched key (`scrobblescope.domain.normalize_name`, already used by
`deezer.py`); score alone is rejected because it ranks text similarity, not
identity -- a high-scoring tribute act or same-titled album by a different
artist must not silently mis-date a real one. The Lucene release-group
query (`releasegroup:"..." AND artist:"..."`) escapes quotes and Lucene
operators in both fields rather than passing them through raw. With no
`MUSICBRAINZ_CONTACT` configured, or `MUSICBRAINZ_ENABLED=False`, the
client returns `(None, None)` without making a request: MusicBrainz blocks
anonymous clients, so an unconfigured contact would only guarantee a
rejected request against the shared 1-request/second budget. A 503 waits
and retries via the existing `retry_with_semaphore`, asking the limiter
again on every attempt.

`scrobblescope/utils.py`: `get_musicbrainz_limiter()`, same
`_ThrottledLimiter` pattern as `get_deezer_limiter` (a global cross-thread
throttle plus a per-loop `AsyncLimiter`) -- this is what makes the 1
request/second limit process-wide rather than per-loop, ahead of Task 9's
dedicated worker thread. `scrobblescope/config.py`: `MUSICBRAINZ_CONTACT`,
`MUSICBRAINZ_ENABLED` (default True), `MUSICBRAINZ_REQUESTS_PER_SECOND`
(default 1), `MUSICBRAINZ_SEARCH_RETRIES` (default 3, mirrors
`DEEZER_SEARCH_RETRIES`), and `MUSICBRAINZ_CHECKS_PER_JOB` (default 60,
unused until Task 9). `MUSICBRAINZ_REQUESTS_PER_SECOND` and
`MUSICBRAINZ_SEARCH_RETRIES` are not in the plan's own file list for this
task but follow the existing per-provider rate/retry constant pattern
(`DEEZER_REQUESTS_PER_SECOND`, `DEEZER_SEARCH_RETRIES`) rather than a
magic number inside `utils.py`/`musicbrainz.py`.

`tests/services/test_musicbrainz_service.py` (new, 10 tests): query
building and Lucene escaping, the score-floor-and-name-match rule
(including a high-scoring wrong-artist rejection), the return shape on a
match and on no candidates, a 503-then-success retry asserting the limiter
is entered on every attempt, the User-Agent contents, and the two
no-contact/disabled-by-flag paths asserting zero requests.

Validation: `pytest -q` -- **1079 passed** (was 1069; +10 new). No frontend
change, so the frontend gate is unaffected; its last measurement (29/29)
still stands. `doc_state_sync.py --check` passes clean (the root
`BATCH22_DEFINITION.md` warning is expected while the batch is active).

### 2026-09-14 - README architecture, tech stack, and diagram refresh (Batch 22 WP-2)

Scope: owner follow-up to the README pass below, given mid-session
(2026-09-14) -- overrides that entry's "deliberately not touched" call.
The owner wants the Mermaid diagram redrawn now (it named modules that
predate WP-0's split -- `routes.py`, `orchestrator.py` -- and never
mentioned Deezer), the Architecture prose and Tech Stack row enhanced, and
new writing to avoid pointers to actual code in favour of self-contained
prose. This still does not duplicate WP-5's own pass: WP-5 owns the
dependency graph and pipeline-sequence detail in
`docs/architecture/runtime-system.md`, which this diagram does not
attempt -- the owner's brief was "keep it simple," a conceptual diagram
(Browser, Flask, background job, Last.fm, Spotify, Deezer, PostgreSQL
cache) rather than a module map.

Changed: the Architecture section's prose and Mermaid diagram (no
filenames, Spotify-then-Deezer fallback shown as a dotted edge), the
`docs/ARCHITECTURE.md` pointer sentence removed (the section is now
self-contained), the APIs tech-stack row reworded to state the fallback
inline, a Deezer clause added to the Prerequisites line ("needs no key"),
and the two Key Implementation Highlights bullets that still said
"Spotify metadata" corrected to name both providers -- left stale by the
entry below, they would have directly contradicted the rewritten
Architecture section above them.

Validation: doc-only; `doc_state_sync.py --check` passes clean. No code
changed, so the Task 6 entry's **1069 passed**, 29/29 still stands.

### 2026-09-14 - README pass for the Deezer fallback (Batch 22 WP-2)

Scope: owner-requested, after Task 6 landed and before a `/handoff`
close-out -- not one of Task 6's own files, but small (under 20 lines) and
directly tied to WP-2's own work, so treated as an in-WP deviation rather
than a separate side-task entry (AGENTS.md Proposal and Design Rules,
item 2). `README.md`'s Unmatched-report paragraph named `no_spotify_match`
as "albums Spotify could not identify" -- true before Task 5, false after
it (the reason now fires only when neither provider matches); fixed as a
stale-claim correction, not new scope. Also added: one Features bullet on
the Deezer fallback and per-row provider attribution, a Deezer clause on
the APIs tech-stack row, a one-line pointer from the Roadmap section to
PLAYBOOK's Section 3 for the fallback and the original-release-year work
that follows it, and a Deezer line in Acknowledgements.

Deliberately not touched: the architecture Mermaid diagram and the fuller
provider data-flow prose. PLAYBOOK Section 3's WP-0 entry already commits
those to WP-5's own README/`docs/architecture/runtime-system.md` pass, so
redoing them here would be exactly the double effort that entry ruled out.

Also fixed `CLAUDE.md`'s graphify section, which restated
`.claude/CLAUDE.md`'s rules inline instead of pointing to
`.claude/skills/graphify/SKILL.md` -- a duplication against the file's own
stated "holds no project facts of its own" rule. `CLAUDE.md` is
git-ignored (confirmed via `git check-ignore`), so this has no commit of
its own.

Validation: no code changed, so `pytest -q` and the frontend gate are
unaffected -- Task 6's own entry above has the current measurement,
**1069 passed**, 29/29; confirmed `doc_state_sync.py --check` still
passes clean.

### 2026-09-14 - Apply cached original-release corrections (Batch 22 WP-3)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 8, the second task of Phase 3. Applies a MusicBrainz finding already
sitting in `original_release_cache` -- populated by Task 9's worker, not
yet built -- so this task is display-only wiring with no live MusicBrainz
call of its own.

Plan drift, expected: the plan's file list still names
`scrobblescope/orchestrator.py`, which the WP-0 module split above turned
into a package before this task ran. The real targets are
`scrobblescope/orchestrator/_results.py` (`_build_results`,
`_get_user_friendly_reason`), `scrobblescope/orchestrator/_cache.py` (new
`_lookup_cached_original_release`), and `scrobblescope/orchestrator/__init__.py`
(`process_albums` wiring). The owner flagged this drift before the task
started; no separate deviation write-up needed beyond this note.

`scrobblescope/orchestrator/_cache.py`: `_lookup_cached_original_release(conn,
keys)` mirrors `_lookup_cached_metadata` -- returns `{}` without raising if
`conn` is falsy or the query fails, since a missing correction must only
skip the display upgrade, never block a job. `scrobblescope/orchestrator/__init__.py`:
`process_albums` calls it inside the same try block that already holds
`conn` open for Phase 1-4 (right after `_persist_new_metadata`, before the
`finally: conn.close()`), keyed on `list(cache_hits.keys())` -- these are
already `(artist_norm, album_norm)` tuples, the same shape
`original_release_cache`'s primary key uses, so no new key derivation was
needed. The result feeds into `_build_results` as a new trailing
`original_release_hits` parameter.

`scrobblescope/orchestrator/_results.py`: `_build_results` now looks up
each album's key in `original_release_hits`; a finding with a non-null
`original_release` becomes the `release_date` used for both
`_matches_release_criteria` and the displayed date, and the provider's own
date survives as a new `provider_release_date` field on the result (or the
unmatched entry, if the correction excludes the album). No finding, or a
cached "checked, nothing found" row (both fields null), leaves the result
shape identical to before this task -- `provider_release_date` is only
added when a correction actually applied. `_get_user_friendly_reason`
gained a `corrected` flag: when true, the wording changes from "Released
X instead of Y" to "First released in X, not Y" (and the decade/custom
equivalents) so a MusicBrainz-corrected exclusion reads as "this is the
true original year," not "the app misread the provider's date."

`tests/services/test_orchestrator_helpers.py` (4 new tests): a correction
that excludes an album from its filter year (reason text asserted
verbatim), the same correction under the original year keeping the album
with `provider_release_date` preserved, the no-correction/nothing-found
case proving behaviour is unchanged (both the omitted-kwarg case and the
explicit-null-row case), and an adversarial sweep of `_get_user_friendly_reason`'s
`corrected=True` wording across all four scopes (same/previous/decade/custom),
not just the one scope the plan's own example uses -- per AGENTS.md Test
Quality Rules, a new branch needs its own test, not just integration
coverage through `_build_results`.

Audit reconciliation, 2026-09-14: commit `f971991` implements Task 8's
runtime behavior once, at the intended seams; no duplicate implementation or
non-working path was found. Its tests did not prove that the normal
`process_albums` run forwarded cached corrections into `_build_results`, and
the new cache wrapper lacked direct no-connection and failure coverage. Three
focused tests now close those gaps. The process seam test was also run with
the forwarding argument temporarily disconnected and failed on the expected
2011-vs-1977 result, then passed again after restoration. The root definition,
plan Progress section, Section 3 and SESSION_CONTEXT now agree that WP-0
through WP-2 are complete, WP-3 owns Tasks 7-9, and Task 9 is next. This
entry's heading was left tagged WP-1 at the time, as a historical commit
record rather than the canonical work-package mapping. **Superseded
2026-09-20:** the untagged side-task entry below the end marker retags this
heading and five others, because `ENTRY_BATCH_RE` parses that tag into the
managed STATUS block, so a wrong tag is a wrong dashboard rather than a
harmless label.

**Docsync gotcha found while landing this entry -- two layers, one
already filed:** (1) this section of Section 4 is append-ordered (oldest
entry on top, new entries added at the bottom, then the tool reverses the
list internally) -- `scripts/docsync/logic.py`'s `_monotonic_dates` says
so explicitly ("current-batch entries are appended and then
reversed... position, not the heading date, is the authority on
recency"). Every current-batch entry so far, including the MusicBrainz
entry above and this task's own first draft, was inserted at the *top*
instead -- the untagged side-task convention, not this section's. Moved
here, to the true bottom, to follow the tool's actual model; the
pre-existing MusicBrainz/README entries above are left as written rather
than reordered, since that is a multi-entry change outside this task's
scope. (2) Fixing the position was not enough: `latest_test_count_authority`
still resolves to 1081, not this entry's 1085, because the DB-connect-timeout
side-task entry below the end marker is *also* dated 2026-09-14 and
explicitly claims 1081 -- on a same-date tie, source precedence ranks a
side-task entry above any current-batch entry regardless of which was
actually written later that day. This is **F-DOCSYNC-11** (open, P1,
filed 2026-09-12, same mechanism, different day), not a new finding.
Tried publishing 1085 into SESSION_CONTEXT/FINDINGS by hand to match
reality; `--check` rejected it (DOC005/DOC006/DOC008), because those
checks independently recompute the same stuck-at-1081 authority and
compare against it, rather than trusting a hand-written number -- the
prior session's F-DOCSYNC-12 fix (a genuinely unmanaged, never-recomputed
field) does not generalize to this one (a managed field recomputed every
run). Reverted to 1081 everywhere docsync validates it, per F-DOCSYNC-11's
own stated remedy ("publish a superseded number"); this entry's own
Validation line below is the accurate record of the true count until
F-DOCSYNC-11 is fixed.

Validation: `pytest -q` -- **1085 passed** (was 1081; +4 new). Frontend
gate -- 29/29, unaffected (backend-only change). `doc_state_sync.py
--check` passes clean (SESSION_CONTEXT/FINDINGS test-count fields read
1081, the tool's current authoritative-but-superseded figure, per
F-DOCSYNC-11 above; the root `BATCH22_DEFINITION.md` warning is expected
while the batch is active).

Audit validation: `pytest -q` -- **1088 passed** (was 1085; +3 focused
tests). The frontend gate was not rerun because the audit changed tests and
documentation only; Task 8's prior backend-only 29/29 result remains the
latest frontend evidence.

### 2026-09-13 - Show the album's own provider in the UI (Batch 22 WP-2)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Task 6, the last task of Phase 2. Real behaviour change: results and
unmatched rows now link to the album's own provider instead of always
building a Spotify URL.

Read the task's hard blocker first: `developers.deezer.com/guidelines`
(plus its linked `/guidelines/logo` page; `deezerbrand.com`, where the
detailed logo spec lives, did not render -- JS-only page, no image-fetch
tool available this session). Two facts recorded here per the task's own
instruction to write them "next to the artwork and the link":
"Local Storage/Offline Storage of audio data is strictly forbidden" is
scoped to audio only, and says nothing about metadata or artwork --
confirms the owner's own reading and means nothing here changes about
caching Deezer's release dates, cover art, or track durations in
`spotify_cache`. Separately, "Each application using Deezer API/SDKs must
have to include a clearly visible Deezer Logo" is a real, unmet
requirement: no tool available could fetch either provider's actual logo
asset (no image-fetch tool; hotlinking a guessed brand-CDN URL was ruled
out as unsafe). Put to the owner directly (F-B21-60 already made the same
call for Spotify -- "Use Spotify's asset as supplied, not a redrawn
glyph"), the ruling was to ship a text attribution badge now and swap in
each provider's real logo later, filed as F-B22-4. F-B21-60 itself gets a
short addendum recording this partial progress; its own scope (the artist
spotlight card's crop/overlay/animation) is unchanged and still open --
Task 6's file list never named the spotlight card.

Plan vs implementation: `orchestrator/_results.py`'s release-scope-miss
branch (in `_build_results`) did not carry `provider`/`album_url` even
though the matched-result branch has since Task 5 -- an album Deezer
matched but the release filter then excluded would have shown no
attribution and no link on `/unmatched`. Added `_album_provider(cached)`/
`_album_url(cached)` (the same Task 5 helpers) to that dict; not in the
plan's own Task 6 file list, but a direct consequence of wiring
`album_url` through the one place it was still missing.

`templates/results.html` and `templates/unmatched.html`: both album-rank
and album-title links switch from `https://open.spotify.com/album/{{
spotify_id }}` to `{{ album_url }}` (guarded on truthiness, so a row with
neither renders plain text as before); a new `.provider-badge` text link
sits beside the artist name, guarded on `provider and album_url` together
so it never appears without something to link to. Both templates carry an
inline comment citing the two Deezer facts above, next to the badge markup
itself. `static/js/results.js`'s CSV export reads a new `data-provider`
attribute and appends a `"Provider"` column.

`scripts/dev/_frontend_gate_results.py` gains
`check_results_provider_attribution`: one Spotify-sourced and one
Deezer-sourced row, asserting each links to its own host
(`open.spotify.com` / `deezer.com`), each shows a visible provider badge
naming its provider and linking to the same URL, and the CSV export
carries both provider values. Switching the link source from `spotify_id`
to `album_url` broke two existing fixtures that set `spotify_id` directly
without `album_url`: `check_unmatched_report`'s release-scope rows (fixed
by adding matching `provider`/`album_url` fields) and
`check_results_interactions`'s pinned CSV row string (fixed by appending
the new column's empty value, since that fixture sets neither field).
`tests/test_routes.py` gains two tests: a results-page row-by-provider
link/badge check, and an unmatched-page release-scope-miss check for the
same thing.

Validation: `pytest -q` from the worktree cwd -- **1069 passed** (1067 +
2). Frontend gate: **29 checks passed in 51 runs** (28/50 + the new
check). Task 7 (MusicBrainz client, Phase 3) is next.

### 2026-09-13 - Deezer fallback wired into the orchestrator (Batch 22 WP-2)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 2 Task 5. Real behaviour change: album enrichment no longer depends
on Spotify alone.

Plan vs implementation: kept the phase order (Spotify search, Spotify
details, then one Deezer pass over what is left), but the plan's "does not
rewrite them" line from Task 3 applied only to Task 3 -- Task 5 had to
touch `orchestrator/_search.py` itself, because deferring the
unmatched-or-not decision to after Deezer's turn means a search miss can
no longer be written to job unmatched immediately. `_run_spotify_search_phase`
now returns a third value, `search_miss_keys`, instead of calling
`add_job_unmatched`; its own two tests (`test_run_spotify_search_phase_all_misses_returns_empty_maps`,
`test_run_spotify_batch_detail_phase_empty_id_list_skips_api_call`) are
updated to match, and a new `orchestrator/_deezer_fallback.py` phase file
(mirroring `_search.py`/`_details.py`'s per-phase convention) owns the
Deezer pass and the now-deferred unmatched write, with reason text "No
match on Spotify or Deezer" (`reason_code` unchanged: `no_spotify_match`).
"Still missing after Spotify" is computed as `cache_misses.keys() -
cache_hits.keys()` post-detail-phase, which uniformly catches both a
search miss and a detail-fetch failure (the latter was already silently
dropped before this task, not newly introduced).

`_detect_spotify_total_failure` is renamed `_detect_enrichment_total_failure`
(swept: tests/services/test_orchestrator_helpers.py's four tests and their
own names). `_fetch_spotify_misses` snapshots `cache_hits` emptiness before
any mutation (`had_cache_hits`) so the post-Deezer `SpotifyUnavailableError`
check reads the pre-run state, not cache_hits after Deezer has already
promoted its own matches into it -- item 4's "Deezer enriches everything
and the job succeeds" only holds if that snapshot is taken first.

`orchestrator/_results.py`'s `_build_results` gains `provider` and
`album_url` per result (`_album_provider`/`_album_url` helpers), reading
the provider columns Task 2 added with a fallback to the classic
`open.spotify.com` URL built from `spotify_id` for rows or live fetches
that predate the provider columns -- Task 6 wires these two fields into
templates/CSV, but the plan's own Task 5 test list asks for them at the
`process_albums` output, so they land here. `unmatched.py`'s
`CATEGORY_METADATA` for `REASON_NO_SPOTIFY_MATCH` is reworded ("No Match
Found" / "Not Found" / mentions Deezer) to match; its one pinned test
(`tests/test_unmatched.py`) is updated in the same commit.

Job progress: the Deezer phase reports 60-75%; the two fixed
post-`process_albums` markers ("Adding album art...", "Compiling...")
move from 60/80 to 80/85 so progress never runs backward when Deezer's
phase ran up to 75%. No test pinned the old 60/80 values.

Validation: `pytest -q` from the worktree cwd -- **1067 passed** (1061 +
6 new integration tests in `tests/services/test_orchestrator_process_albums.py`,
covering the plan's five Step 1 scenarios: Spotify-matches-everything
skips Deezer, a Spotify miss falls through to a Deezer match with
`provider`/`album_url` set, neither provider matching registers one
unmatched entry with the new reason text, a Deezer-only run with no
Spotify token succeeds, that same no-token run raises
`SpotifyUnavailableError` only when Deezer also fails, and a Deezer match's
persisted row carries `provider`/`provider_album_id`/`provider_url` with
`spotify_id` left `None`). Fixed two pre-existing tests
(`test_process_albums_partial_cache_token_failure_uses_cached_results`,
`test_process_albums_all_misses_token_failure_raises`) that would
otherwise have made real, unmocked network calls to Deezer once this task
landed -- both now mock `search_deezer_album` explicitly. Frontend gate:
28 checks passed in 50 runs (unchanged from WP-0's baseline; `unmatched.py`'s
reworded copy did not regress the gate's rendered-page assertions). Task 6
(show the album's own provider in the UI) is next; note its own blocker:
read Deezer's attribution guidelines before shipping any Deezer-sourced
result.

### 2026-09-13 - Spotify calls behind spotify.enrich_albums (Batch 22 WP-1)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 1 Task 3. No behaviour change to any running job -- `enrich_albums`
is a new, additional entry point; `process_albums`'s real path still calls
`_run_spotify_search_phase` and `_run_spotify_batch_detail_phase` directly,
unchanged, per Phase 2's Task 5 owning the wiring.

Plan vs implementation, one deliberate reading: `scrobblescope/orchestrator.py`
is a package since WP-0, so "Modify: scrobblescope/orchestrator.py" is read as
"expose the new seam on the facade" rather than touching the phase functions
the plan explicitly says to leave alone ("this task adds a seam, it does not
rewrite them"). `scrobblescope/spotify.py` adds `enrich_albums(session,
misses, token)`: concurrent per-key search via `search_for_spotify_album_id`,
then one `fetch_spotify_album_details_batch` call for every match, returning
`({key: AlbumMetadata}, unmatched_keys)`. `misses` reads the same
`{key: original_data}` shape `process_albums`'s `cache_misses` already uses
(only the keys matter here), so Task 5 can pass it through unchanged.
`scrobblescope/orchestrator/__init__.py` imports `enrich_albums` into the
facade and `__all__`, alongside the other `spotify.py` dependencies, so
`mock.patch("scrobblescope.orchestrator.enrich_albums")` reaches it once a
later task wires it in.

**Fix folded in, caught by Pylance during this task (owner):**
`AlbumMetadata.image_url` (`scrobblescope/enrichment.py`, Task 1) was typed
`str`, but a Spotify album can have no cover art -- `images[0].get("url")`
returns `str | None`, so the type was wrong from Task 1's commit, not
something Task 3 introduced. Widened to `str | None`; behaviour was already
correct at every call site (`image_url or None`-shaped fallbacks exist
elsewhere), only the declared type was too narrow. Added a boundary test
(`test_enrich_albums_handles_missing_cover_art`) pinning the no-images case.

Validation: `pytest -q` from the worktree cwd -- **1054 passed** (1049 + 5
new: 4 `enrich_albums` tests in `tests/services/test_spotify_service.py`,
1 facade-exposure test in `tests/services/test_orchestrator_fetch_spotify.py`).
The frontend gate -- 28 checks passed in 50 runs, matching WP-0's baseline
exactly, confirming the facade import didn't disturb `process_albums`'s real
path. Phase 1 (the provider contract) is now complete; Phase 2 Task 4
(Deezer client) is next.

### 2026-09-13 - Cache columns for any provider (Batch 22 WP-1)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 1 Task 2. No behaviour change -- the new columns and table are unused
until Task 3+ wires a caller to them.

Plan vs implementation: matched. `init_db.py` adds
`ALTER TABLE spotify_cache ADD COLUMN IF NOT EXISTS provider/provider_album_id/
provider_url` plus `ALTER COLUMN spotify_id DROP NOT NULL` (a Deezer-only row
cannot satisfy the old constraint), backfills `provider='spotify'`,
`provider_album_id=spotify_id` for existing rows, and creates
`original_release_cache` (`artist_norm`, `album_norm`, `mb_release_group`,
`original_release`, `checked_at`, PK on the norm pair) exactly as specified.

`scrobblescope/cache.py`: `_batch_lookup_metadata` and `_batch_persist_metadata`
now read/write the three new columns. **Deviation, deliberate:**
`_batch_persist_metadata`'s row tuple grows from 6 to up to 9 elements
(`+provider, provider_album_id, provider_url`), but the extra three are
optional -- a 6-element row (today's only caller,
`orchestrator/_details.py:137`, unchanged in this task) defaults to
`provider="spotify"`, `provider_album_id=spotify_id`, `provider_url=None`.
This keeps Phase 1's "no behaviour change" for that caller while still
tagging its writes correctly, so jobs run after this commit don't need the
one-time backfill to be re-run. Added
`_batch_lookup_original_release`/`_batch_persist_original_release` against
the new table, TTL'd on `ORIGINAL_RELEASE_TTL_DAYS` (`config.py`, default
365 -- an original release date does not change, so the TTL only guards a
bad match). A cached row with a null `mb_release_group` is a valid "checked,
nothing found" cache hit, distinct from no row (uncached).

Validation: `pytest -q` from the worktree cwd -- **1049 passed** (1037 +
12 new: 4 schema tests in `tests/test_cache_schema.py`, 8 cache-layer tests
in `tests/services/test_cache.py`). The 6-tuple-legacy-default behaviour and
the pre-existing `tests/test_repositories.py` cache tests are covered
without modification, confirming the defaulting path preserves today's
persisted rows.

**Owner-verified against real Postgres, 2026-09-13:** owner ran the app on
localhost against the Docker `ss-postgres` container (mirrors the deploy
target, not a mock), which re-runs `init_db.py`'s migration on startup.
No regressions observed. This is real evidence the `ALTER TABLE` statements
apply cleanly to a live database, beyond the unit tests' string assertions
on `init_db.py`'s source -- partial coverage of the plan's own Verification
item 5 ("run `init_db.py` against a copy of the production schema"); the
Deezer-round-trip half of that item waits on Phase 2. Task 3 (Spotify calls
behind `spotify.enrich_albums`) is next.

### 2026-09-13 - Provider contract, AlbumMetadata value object (Batch 22 WP-1)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 1 Task 1. No behaviour change yet -- `AlbumMetadata` is not wired into
any caller.

Plan vs implementation: matched exactly. `scrobblescope/enrichment.py` adds
`AlbumMetadata`, a frozen dataclass (`provider`, `album_id`, `url`,
`release_date`, `image_url`, `track_durations`) with `as_cache_row_fields()`
returning the six fields as a tuple in cache-column order.
`track_durations` holds seconds keyed by `normalize_track_name`, the shape
`_build_results` already reads -- documented on the class rather than
duplicated at each call site.

Validation: `pytest -q` from the worktree cwd (not the primary checkout,
which collects its own stale tree and undercounts) -- **1037 passed**
(1036 baseline + 1 new). Task 2 (cache columns) and Task 3 (Spotify calls
behind `spotify.enrich_albums`) are next; see
`docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md` for
progress notes per task.

### 2026-09-13 - Module split, behaviour-neutral (Batch 22 WP-0)

Scope: split `scrobblescope/routes.py` (985 lines) into a `routes/` package
and `scrobblescope/orchestrator.py` (1035 lines) into an `orchestrator/`
package, per `BATCH22_DEFINITION.md` WP-0. No behaviour change; the
acceptance criterion was every existing test passing unmodified.

Plan vs implementation: matched the definition's four named phases for
`orchestrator/` (`_search`, `_details`, `_cache`, `_results`) and the four
named concerns for `routes/` (`pages`, `album_flow`, `heatmap_flow`, `api`),
each behind a facade `__init__.py` that keeps the pipeline glue
(`process_albums`, `_fetch_and_process`, `background_task`,
`fetch_top_albums_async`) or shared job-context helpers respectively. One
`Blueprint` (`bp`, name `"main"`) is still shared across the four route
files, so every endpoint name and `url_for()` call is byte-identical --
`routes/` is a package of route files sharing one blueprint, not four
separate blueprints, which is the narrower reading of "package of
blueprints" that kept templates and endpoint names untouched.

The load-bearing discovery: roughly 24 names across both modules are
`mock.patch`/`monkeypatch.setattr` targets in the existing test suite,
addressed as `scrobblescope.orchestrator.<name>` or
`scrobblescope.routes.<name>`. A name imported directly into a phase
submodule stops being reachable by that patch once the code that calls it
moves out of the facade file, because the patch only replaces the
attribute on the facade module's own namespace. Every submodule therefore
imports its parent package (`from scrobblescope import orchestrator as
_orchestrator` / `... routes as _routes`) and reads cross-cutting
dependencies through that live reference at call time, not through its own
`from x import y`. The facade files keep every original top-level import
unchanged, even where their own code no longer calls it directly, so the
attribute still exists for a submodule or a test to reach. Both `__init__.py`
files carry an explicit `__all__` documenting that contract and satisfying
ruff's unused-import check (`ruff-check --fix` would otherwise delete an
import kept only for re-export).

Deviation: `docs/architecture/*.md`, `README.md` and `AGENT_NOTES.md` still
cite a few pre-split `orchestrator.py`/`routes.py` paths. The two
load-bearing ones in `AGENT_NOTES.md` (the Windows-asyncio ProactorEventLoop
note, cited from two places) are fixed in this commit; the rest are left for
WP-5's already-scoped README and `docs/architecture/runtime-system.md` pass
rather than swept twice. `docs/superpowers/plans/` citations are dated
plan documents and are not touched, per the dated-entry exemption.

Validation: `pytest -q` -- **1034 passed**, unmodified from every test file
in the suite. `scripts/dev/frontend_gate.py` -- 28 checks passed in 50 runs
across chromium and firefox, matching the batch-open baseline. `ruff check`
and `ruff format` clean on both new packages. `scripts/doc_state_sync.py
--check` passes (the root `BATCH22_DEFINITION.md` warning is expected while
the batch is active).

Forward guidance: WP-1 (the provider contract) adds `scrobblescope/
enrichment.py` and moves the Spotify calls behind `spotify.enrich_albums`,
which lands inside `orchestrator/_search.py`'s and `_details.py`'s existing
phase boundaries rather than requiring another restructure.
