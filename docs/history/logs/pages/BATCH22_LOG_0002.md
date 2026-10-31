<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# BATCH22_LOG -- page 0002

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
