<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0019

### 2026-09-21 - Production refuses to start without its API keys (F-SWE-4)

Side task, no batch tag, owner-approved on 2026-09-21. F-SWE-4: production
starts through `gunicorn app:app`, which imports `app.py` and never runs its
`__main__` block, so `ensure_api_keys()` there never fired. A deployment
missing a key served pages and reported every search as an upstream outage.

**Plan vs implementation.** The finding called it one line. It was not: an
unconditional call in `create_app()` makes every environment without the
keys fail at import, and three do -- the test suite and the frontend gate both
import `app`, and CI's repository secrets arrive empty when unavailable. A
simulated secret-less CI run confirmed it (whole suite fails at collection).
So the fix follows the precedent beside it: `_validate_api_keys` mirrors
`_validate_secret_key` (refuse in production, warn in dev mode) and is called
from `create_app()`, and `tests/conftest.py` and `scripts/dev/frontend_gate.py`
supply placeholder keys exactly as they already supply `SECRET_KEY`. The
`__main__` checks in `app.py` and `run.py` stay: they fail fast for a local
run, which dev mode would otherwise only warn about.

**Tests.** Four in `tests/test_app_factory.py`, red before the helper existed:
production refuses, dev warns, a complete set passes, and `create_app()`
itself refuses -- the regression the finding describes. The full suite passes
normally and again with `DEBUG_MODE=0` and every key plus `SECRET_KEY`
empty, which is CI without secrets.

**Deviation: two siblings of the previous commit, found here.** The
`runtime-system.md` prose listed `config.py`'s importers by line number, and
the event-loop commit had shifted three of them (`worker.py`,
`release_checks.py`, `orchestrator/__init__.py`). Rewritten to name modules
rather than lines, recomputed with an `ast` walk -- still ten nodes -- per
AGENTS.md anti-pattern 11's rule to cite by name. README's `worker.py` row
also still read as though the module held only the semaphore; it now names
the event loop. F-B22-2 gained a note: the `spotify.py` asserts are now
reachable only in dev mode.

**Validation:** `pytest -q` -- **1540 passed**. `pre-commit run --all-files` --
all hooks pass. `doc_state_sync.py --check` exit 0. Frontend gate passed.

**Forward guidance:** F-B22-2 still wants its six `assert`s replaced; the
startup check narrows one pair, it does not fix them.

### 2026-09-21 - One event-loop helper for every background thread (F-B20-2)

Side task, no batch tag, owner-approved on 2026-09-21 on condition that it
is non-breaking. F-B20-2 asked for the orchestrator split, which Batch 22
WP-0 delivered, and for shared event-loop setup. That setup had since
reached a third copy -- `orchestrator.background_task`, `heatmap.heatmap_task`
and `release_checks._worker_loop` each built a `ProactorEventLoop` on Windows
and a default loop elsewhere -- which is the point `docs/agents/global-rules.md`
Rule 3 says to extract.

**Plan vs implementation.** New `worker.new_thread_event_loop()` creates the
loop, installs it, and returns it; the three call sites now call it. It
lives in `worker.py` because that module already owns background-thread
execution and both job modules import it; `utils.py` was rejected, since
F-SWE-7 records it as already holding five unrelated concerns. The one new
import edge, `release_checks -> worker`, is drawn in
`docs/architecture/runtime-system.md` (re-verified against the `ast` import
graph: no missing or extra edge) and listed in SESSION_CONTEXT Section 4.

**The behaviour worth preserving, and how it was kept.** Before, a failure in
`asyncio.set_event_loop` still closed the loop, because the loop was
assigned before the call and the caller's `finally` closed it. The helper
cannot return a loop it failed to install, so it closes the loop itself
before re-raising. Test-first: three new tests in `tests/test_worker.py`
(default loop off Windows, Proactor on Windows, close-on-install-failure),
red before the helper existed. The existing slot-release parity tests for
both job entry points -- crash, loop-setup failure, loop-close failure --
pass unmodified, as does the whole suite.

**Only part of F-B20-2's list was extracted, deliberately.** Progress mapping
and error guards have two occurrences, album and heatmap, so Rule 3 says
leave them. F-B20-2 is resolved with that reasoning written into it.

**Deviation: Batch 23's definition and plan were amended by one clause.**
`BATCH23_DEFINITION.md` WP-0 plans `_run_coroutine_in_new_loop`, described
as "the Proactor boilerplate". The Proactor choice is now shared, so both
documents describe that item as the run-and-close wrapper built on
`worker.new_thread_event_loop`. Scope is unchanged; the owner should know the
approved definition moved. `AGENT_NOTES.md` and SESSION_CONTEXT Section 7
each restated the Proactor rationale; both now point at the helper's
docstring, which owns it.

**Validation:** `pytest -q` -- **1536 passed**. `pre-commit run --all-files` --
all hooks pass. `doc_state_sync.py --check` exit 0. `ruff check` clean.

**Forward guidance:** F-SWE-7 (`utils.py`) is the sibling split, and wants a
work package of its own. Batch 23 WP-0's export wrapper should call
`new_thread_event_loop` rather than add a fourth platform branch.

### 2026-09-21 - Between-batch verification: findings, MusicBrainz policy, one diagram

Side task, no batch tag. The owner is using the gap before Batch 23 to close
findings and verify earlier agent work against its sources. Scope was three
checks and the fixes they produced.

**Six findings rotated that had been finished for weeks or months.** None
carried a lifecycle record, so rotation could not see them, and DOC023 could
not flag them because their prose still said "open" or "in progress" -- stale
text rather than a missed pattern. Each was verified against git and source
before its box was checked, with the landing date as its completion date:
F-DOCSYNC-1 (`fd39c89`, 2026-02-26 -- seven months), F-B21-8 (`20dfe0d`),
F-B21-13 (`8ed1650`), F-B21-12 (`c7bfaec`), F-B20-4 (`9152fd3`), and F-B21-50
as no action by owner ruling. F-B21-13 is the one real pattern miss: its
prose said "closed", a word DOC023 does not read.

**F-B20-3 gained its record but stays active.** Bootstrap is gone on this
branch (`85e7511`), but `origin/main` is what Fly.io deploys and still loads
it, so it reads "resolved locally, pending deploy" like the five Batch 21
findings in the same state (F-B21-10, -26, -27, -28, -29). DOC014 is right
to hold all six until `main` advances; they are not stuck.

**F-STYLE-2 narrowed, and `.flake8` deleted.** Ruff (`c7bfaec`) settled the
line length at 88; the orphaned `.flake8` still claimed 120 and nothing read
it. What remains open is only the docstring convention.

**MusicBrainz: the code is right and its stated reason was wrong.** Checked
against the upstream API and rate-limiting pages, including the raw wiki
text. `client=` is required only on POST (data submission); this app sends
GET searches, so omitting it is correct. The User-Agent format, the 1 req/s
per IP limit, the 503 on throttling, `fmt=json`, and the `releasegroup` and
`artist` search fields all match. But the code, its docs and its tests said
MusicBrainz "blocks
anonymous clients outright" and that a contact-less request "would only
guarantee a rejected request". Upstream, "anonymous" is a named list of
library defaults (blank, `Java`, `Python-urllib`, ...) that share a throttled
pool; the contact is a policy requirement, and breaking it risks throttling
or a block. The design -- stay disabled without a contact -- is unchanged;
the reason is corrected in `musicbrainz.py`, `release_checks.py`,
`config.py`, `.env.example`, `DEPLOY.md`, `README.md` and four test
docstrings, which also now say an email or a URL is accepted. The Batch 22
plan keeps its wording as a historical record.

**Architecture diagrams, verified mechanically.** `runtime-system.md` was
compared with the module import graph extracted by `ast`: no missing edge, no
extra edge, the three deferred imports drawn dotted, and all ten `config.py`
importers at their cited lines. `heatmap-sequence.md` matches `heatmap_task`
and `/heatmap_data`. `top-albums-sequence.md` had one false paragraph: it said
`background_task`'s `finally` "is not reached if the event-loop setup above it
fails". The setup is inside the `try`, so the release is unconditional -- and
the diagram's own note near its end already said so. Rewritten.

**Deviation: a real test-isolation defect, surfaced by configuring the
contact.** The first full run after the owner set `MUSICBRAINZ_CONTACT` failed
`test_enqueue_release_check_queues_jobs_in_order` intermittently. A probe
plugin showed why: `app.py` loads the developer's `.env`, so every unpatched
happy-path pipeline test now enqueued its job and started the **real**
`release-checks` thread (the first was a test in
`tests/services/test_orchestrator_fetch_and_process.py`), which drained the
shared queue the order test reads and
could reach musicbrainz.org and the local Postgres. No real call went out in
the probed run; nothing stopped one either. CI never saw it because it has no
`.env`. Fixed in `tests/conftest.py` beside the existing `SECRET_KEY` guard:
`MUSICBRAINZ_CONTACT` is forced empty before `app` is imported, which
`load_dotenv` will not override. Re-probed: no worker, no queue residue, no
MusicBrainz attempt. Regression test
`test_session_starts_with_no_musicbrainz_contact` fails with that line removed
on a machine that has a contact configured -- which is the only machine the
defect exists on. Otherwise no runtime behaviour changed; the one string a
test matches (`MUSICBRAINZ_CONTACT`) is still in the error message.

**Validation:** `pytest -q` -- **1533 passed**. `pre-commit run --all-files` --
all hooks pass. `doc_state_sync.py --check` exit 0. Frontend gate: 30 checks
passed in 52 runs across chromium and firefox.

**Forward guidance:** the owner approved four follow-ups in the same session,
each its own commit: the shared event-loop runner F-B20-2 now warrants, the
startup key check F-SWE-4 describes, the F-MAS-4 broad-catch remediation, and
DOC023 reading a legacy status line that opens with "closed".

### 2026-09-20 - Working tree reconciled for the deferred audit

Side task, no batch tag. The SWE audit's charter requires a clean worktree
before grading -- "a SHA cannot reproduce uncommitted content, so a matrix
built over a dirty tree is unfalsifiable however carefully its cells cite
lines" -- and the tree had two modified tracked files and sixteen untracked
paths. Reconciled, one class at a time, and three of the classes turned out to
be defects rather than clutter.

**The graphify refresh tooling is now adopted, and it was broken as written.**
`AGENT_NOTES.md` carries a new section describing a threshold-gated local graph
refresh: two `.githooks` scripts calling `scripts/dev/graphify_refresh.py`,
which rebuilds only after 5 commits or 25 changed files have accumulated. Its
tests pass (20) and it is standard-library only, as its own comment explains
(hooks do not inherit an activated virtualenv). But the section also states the
hook files "must keep LF endings: a CRLF `post-commit` fails under Git for
Windows' `sh`", and **both hook files were CRLF on disk**. `.gitattributes`
had rules for two CSS files and `docs/design/**`, nothing for `.githooks/`.
Committing them as they stood would have shipped a hook that fails for any
clone whose `core.autocrlf` rewrites it, while the document beside it promised
otherwise. Fixed at the root rather than the instance: a `.githooks/* text
eol=lf` rule, so the working copy is correct whatever a clone's autocrlf is,
plus a conversion of both files to LF. This is the same shape as F-B21-61 --
a written claim that nothing enforced.

**And a second half of the same defect, found after the first commit.** Both
hooks were staged as mode `100644`, not `100755`. Git does not run a hook file
that is not executable -- on Linux and macOS it reports "ignored because it's
not set as executable" and continues -- so the feature would have worked on
this Windows checkout, where the exec bit is meaningless, and silently done
nothing on Linux or in CI. `core.fileMode` is `false` in this clone, which is
exactly why git recorded 100644 and could not report the difference. Fixed with
`git update-index --chmod=+x`, which writes the mode into the index directly
rather than relying on a filesystem bit Windows does not have. Both files keep
their original blob SHAs, so only the mode changed. This is the CRLF defect
again in a different register: a repository-level property that a
Windows-only clone cannot notice it is violating.

**`AGENT_NOTES.md` also removed three stale blocks**, which is why it was
modified at all: the "Heatmap Feature Notes (shipped -- Batches 18/19)" and
"Batch 21 Tooling Map" sections both describe work that has since closed (the
tooling map says of itself "Written 2026-08-14, before WP-1 started"), and a
gap item about `skills-lock.json` was removed because that file is gitignored
and so cannot be part of the corpus a reader can check. A new
`HEATMAP_WINDOW_DAYS` constraint was added, pointing at the single source in
`scrobblescope/heatmap.py`.

**`requirements-dev.txt` was reverted, not committed.** It carried a local
addition of `cosmic-ray==8.7.0`, which exists to serve the mutation-test runner
that F-SWE-8 records as unadopted -- "the code stays out of the corpus until
then". Shipping its dependency while its tool stays untracked would be the
inconsistent half of that decision.

**Junk removed and ignored, each for a stated reason:** `nul` deleted (a
Windows reserved device name, so `del` and `Remove-Item` both fail on it and
`Test-Path` reports false while the directory entry is real; removed through
the `\\?\` extended-length prefix). `coverage.xml` ignored as the XML form of
the already-ignored `.coverage`; `/tmp/` ignored as agent probe scratch;
`.codex/` and `.continue/` ignored as per-machine harness config, which
`.codex/hooks.json` proves by naming an absolute path under one user's home.

**Deliberately left untracked:** `scripts/dev/mutation_test.py`,
`scripts/dev/mutation_scope.toml` and `tests/scripts/dev/test_mutation_test.py`,
because F-SWE-8 says not to stage them as part of another task's commit. They
are pending work with their own work package, and gitignoring them would
misdescribe them as not-repository-state. They are not graded modules, so their
presence does not invalidate a grade of `scrobblescope/`.

**Still awaiting an owner decision, not committed or deleted:**
`docs/2026-09-14-open-code-review-audit.md` (315 KB at the `docs/` root),
`docs/history/reports/CONTROL_PLANE_AUDIT_2026-09-15.md` (which cites it as
"the dated code-review advisory at the repository's docs root"),
`docs/history/reports/Architecture Review -- ScrobbleScope Control Plane &
Strangler.html`, `docs/superpowers/plans/plan.md` (a Batch 21 traversal plan)
and `progress_copy.md` (an SDD ledger for the close-out plan, whose own first
line names its source plan). All five are audit or planning evidence rather
than code; four belong under `docs/history/` by AGENTS.md's own archive
convention if they are kept. Moving or deleting 315 KB of someone else's audit
evidence is not a call this side task should make.

**Validation:** `pytest -q` -- **1532 passed**. `pre-commit run --all-files` --
all ten hooks pass. `doc_state_sync.py --check` exit 0. The graphify unit's own
suite: 20 passed.

**One figure worth knowing about, found while measuring the above.** pytest
collects from `tests/` on disk, not from `git ls-files`, so the recorded count
of 1532 includes tests that live in files no clone will ever have: 20 in
`tests/scripts/dev/test_graphify_refresh.py` (now committed, so those become
real) and **46 in `tests/scripts/dev/test_mutation_test.py`**, which F-SWE-8
keeps out of the corpus. A tracked-only checkout therefore measured 1466
before this commit and measures 1532 only because of two untracked files. That
does not make the number wrong as measured, but it does mean it is not
reproducible from the SHA alone -- which is the same objection the audit's
charter raises about grading a dirty tree, applied to the test count. The 46
will keep inflating it until either the runner is adopted or the file is moved
somewhere pytest does not collect.

**Forward guidance:** the audit precondition is now met for the tracked corpus
-- no tracked file is modified. The three untracked mutation files are the
recorded exception, by F-SWE-8's own instruction. The five decision-pending
documents are the last thing between this tree and an empty `git status`, and
until they are resolved the count above keeps its 46-test caveat.

### 2026-09-20 - Architecture diagrams reconciled against the import graph

Side task, no batch tag. Two of the five architecture diagrams were stale, and
verifying them produced a scope problem for the deferred SWE audit that is
worth recording before anyone starts it.

**How the staleness was found.** Not by reading the diagrams against memory,
which is how they went stale, but by extracting the real module-level import
graph with `ast` and comparing edge by edge. That is the check F-B21-61 says
does not exist, and it took one script to demonstrate the need for it.

**`runtime-system.md` had seven missing edges and a wrong count.** Ground truth:
`Routes -> SpotifyClient` (`routes/api.py:22`, `routes/__init__.py:31`),
`Routes -> Domain` (`api.py:15`, `__init__.py:28`), `ReleaseChecks -> Utils`
(`release_checks.py:62`), `Spotlight -> Utils` (`spotlight.py:5`), and
`SpotifyClient -> Domain` (`spotify.py:14`), `DeezerClient -> Domain`
(`deezer.py:17`), `MusicBrainzClient -> Domain` (`musicbrainz.py:23`) were all
real imports absent from the drawing. The prose claimed eight nodes import
`config.py`; the true count is ten, and the list omitted `deezer.py`,
`musicbrainz.py` and `release_checks.py` -- the three modules Batch 22 added.
`App --> Routes` was drawn solid but is deferred inside `create_app`
(`app.py:143`), and the entrypoint's `config` import (`app.py:155`) is deferred
inside `__main__`. Fixed, with import lines cited so the list can be re-checked
rather than trusted.

**A second defect in the same file:** five bullets sat under the heading "Three
things this view deliberately makes visible". Batch 22 added three bullets and
nobody moved the count.

**`top-albums-sequence.md` was materially wrong, not merely incomplete.** A
search for `Deezer|MusicBrainz|release_check|provider|enrich` matched only its
own title: the entire Batch 22 enrichment path was undocumented. Worse, the
existing branch was incorrect independent of that omission -- it drew the
no-cache-hits case as an immediate `raise SpotifyUnavailableError`, while
`_fetch_spotify_misses` (`orchestrator/__init__.py:162`) tries Deezer for every
remaining miss first and raises only on three conditions together: no token,
nothing cached beforehand, and Deezer matching nothing. Persistence was drawn
inside the Spotify branch when it actually happens in the caller after the
Deezer pass returns, which is one row set for both providers rather than one per
provider. The correction worker -- enqueued at
`orchestrator/__init__.py:612`, immediately after `set_job_results` at `:600`
and only on the happy path -- was absent entirely, so it now has its own
lifeline and block.

**Validated structurally, not by eye.** A checker counts `alt`/`opt`/`loop`/
`par`/`subgraph`/`box` against `end` per fence and reports the final depth; all
six mermaid blocks in the repository return to zero, so the edits parse.
`docs/ARCHITECTURE.md`'s "Last verified" date moved to 2026-09-20 and its
section 3 description now names the Deezer fallback and the correction pass.

**Forward guidance, and the reason this matters more than two diagrams.** The
deferred SWE audit's charter (`docs/SWE_AUDIT_CHARTER.md`, retired after its
2026-08-20 execution) is no longer executable as written, because its closed
scope table names thirteen modules that no longer exist in that shape:

- It lists `scrobblescope/orchestrator.py` and `scrobblescope/routes.py`, which
  are packages since Batch 22 WP-0 -- 6 and 5 files respectively.
- It omits `deezer.py`, `enrichment.py`, `musicbrainz.py`, `release_checks.py`,
  `spotlight.py` and `unmatched.py` entirely. `git ls-files 'scrobblescope/*.py'
  app.py` returns **29** files, not the charter's 14.
- Its stated hotspots have moved. It names `_fetch_and_process` (was 151 lines)
  and `results_loading` (was 112). The largest function now is
  **`_render_results_page` at `routes/album_flow.py:126`, 142 lines**, which
  postdates the charter and is in neither list; `_fetch_and_process_heatmap`
  (141) and `_fetch_and_process` (133, now `orchestrator/__init__.py:502`)
  follow it.

The principle count is unchanged at ten (DRY, SoC, SRP, KISS, Dependency
Inversion, Composition over Inheritance, Clean Architecture, Boy Scout Rule,
Law of Demeter, Fail Fast), so the matrix is ten principles against the real
module list -- roughly 280 cells, not the charter's 130. A re-audit therefore
needs its own charter with a current, closed scope table before grading starts;
the retired one is evidence, not a work order. The charter's own Section 2a also
requires a clean worktree, and `AGENT_NOTES.md` plus `requirements-dev.txt` are
currently modified with untracked tooling alongside them, so that is a
precondition rather than a formality.

### 2026-09-20 - README engineering depth and the control-plane narrative

Side task, no batch tag, following the earlier reconciliation in this session.
That pass fixed stale *facts*; this one fixed a missing *argument*. The
architecture's real depth was documented nowhere, and DEVELOPMENT.md had been
stale for weeks about a control plane that is now the largest body of code in
the repository.

**README gained the engineering case, because its audience is developers and
recruiters rather than end users.** Two new pieces:

- **"A search is an ETL pass over an event stream, not a query."** Last.fm
  stores scrobbles -- an unbounded stream of track timestamps -- and has no
  concept of the album a listener played. An album is *produced* by grouping on
  a normalized key and threshold-gating on user criteria, so it is a function
  of the query, not a row. That is why the codebase does not look like CRUD,
  and it is the frame the rest of the architecture reads against.
- **"Owned Interface Components."** The heatmap as a hand-built SVG
  (`createElementNS`, Monday-first via `mondayIndex`, 7 rows against 53 week
  columns, a separate sequential mobile grid because 880px cannot fit a phone
  column), and the log-normalised intensity
  `Math.log10(count + 1) / Math.log10(maxCount + 1)` that keeps a heavy
  listener's mid-range visible on a linear ramp. Plus the theme-resolved
  zero-count cells (an SVG `fill` presentation attribute does not resolve a
  custom property), the 2x cloned-SVG export, the owned pinwheel, the
  deliberately desktop-faithful results export, and the sampled spotlight.

**DEVELOPMENT.md gained two arguments it was missing.** First, *why* the
rotation is a mechanism: it was done by hand three times and failed three
distinct ways -- an entry archived that should have stayed, an entry duplicated
across the boundary, a stale remark left behind -- all silent, because the
document still renders. The parser, renderer and rotation exist because that
task is one an LLM is not reliable at across sessions. Second, the ACID framing
stated honestly: atomicity is real, consistency is real (the invariant checks
are the C), isolation is partial (filesystem-scoped lock, no cross-machine
coordination, readers not serialised), durability is within filesystem
semantics. The precise description is an atomic file-transaction and invariant
enforcement system; the acronym is useful shorthand and stops being useful the
moment it is read as a database guarantee.

**The `.docsync.toml` extraction story is now written down**, which was the
largest gap. The declaration layer exists specifically so a second repository
supplies its own config without touching the mechanism -- and `declarations.py`
carries no ScrobbleScope value at all. What remains tied is enumerated as a
table rather than asserted: document paths, the scanned corpus and its
`allow_files` list, `[retired.allow_after] "PLAYBOOK.md"`, `[closeout]
admit_from_batch = 22`, the design-token `[[value]]` entries, and
`_LIVE_DOCUMENT_PATHS` in `integrity.py` (verified at line 100). The section
also records why finishing it now would cost more than it saves: the remaining
modules are the largest in the package, and making them generic before there is
a second consumer buys indirection rather than reuse.

**Also added:** the three pieces that make the package a workflow rather than
a mechanism -- the commit preflight, the opt-in hook installer (not installed
here), and the CLI surface. README's methodology section now says the tooling
is larger than the application on purpose and points at DEVELOPMENT.md for the
honest extraction state.

**Deviations:** one, self-inflicted and caught. Authoring the console section
introduced a zero-width space (U+200B) into DEVELOPMENT.md, violating the
ASCII-only authoring rule. Found by scanning for non-ASCII code points rather
than by eye, removed with a targeted rewrite, and re-verified clean. No other
document or file carried one.

**Validation:** `pytest -q` -- **1532 passed**. `pre-commit run --all-files` --
all ten hooks pass. `doc_state_sync.py --check` exit 0. Non-ASCII scan of
README.md and DEVELOPMENT.md: none.

**Forward guidance:** DEVELOPMENT.md is still the narrative and
`docs/architecture/documentation-tooling.md` still owns the DOC001-DOC023
catalogue; the split was preserved rather than duplicated. The deferred plans
are unchanged and stay deferred.

### 2026-09-20 - DEVELOPMENT.md and README.md reconciled with the control plane

Side task, no batch tag. Two documents described a repository that no longer
exists, and one gate comment described a migration that had already finished.

**DEVELOPMENT.md was materially stale.** Its docsync section said the package
had "Six focused modules" and listed six test files. It has **twelve** modules
(`declarations`, `closeout`, `archives`, `findings`, `transaction`, `markdown`
were added by Batch 22) and twelve matching test files in `tests/`. The
worktree section named only `check_worktree_alignment.py` and a spec document,
omitting the seven `_worktree_guard_*.py` modules and the `WT000`-`WT014`
codes. The gate section stopped at "starts and stops its own loopback server"
and never named `port 0`, the `finally`, the 44px touch target, the 3:1
composited-contrast check, the viewport profiles or stylesheet isolation. Two
lines were also written in the present tense of a batch that has closed
("Batch 21 uses...", "The active batch definition owns...").

**README lacked four architectural facts** it should carry at product level:
the cache talks to Postgres in arrays via `unnest($1::text[], ...)` rather than
row by row; a stale schema identifies itself by SQLSTATE (`42703`, `42P01`)
instead of being mistaken for network turbulence; Spotify's removed batch
endpoint answers `403`/`404`/`410` and degrades to one request per album; and
the opening prose said the badge "is the live state", which read awkwardly.

**A new DEVELOPMENT.md section records the extraction intent** owner-stated
2026-08-25 and owned by `AGENT_NOTES.md`: this repository is also a template
being extracted, and the three control-plane components are at very different
maturity. The section states that honestly rather than aspirationally -- the
worktree guard is structurally complete, docsync is close, and the frontend
gate is the least extracted, with its decomposition plan deliberately parked.
It also records the standing constraint: do not start the extraction as a side
task; write new tooling so it stays cheap.

**A real defect was found and fixed in the process.**
`frontend_gate.py:209-215` carried a comment describing "the job-backed
Results and Unmatched templates" as still on Bootstrap, directly above an
already-empty `LEGACY_PAGES`. There is no residual Bootstrap: every template
carries an opt-out note, `static/css/` has no Bootstrap file, and README
already said "Bootstrap is gone". The only Bootstrap left is a test fixture
that proves a page *would* collide if it loaded both frameworks. A reader
trusting the comment would have concluded two page families were unmigrated.
This is anti-pattern 15 in miniature -- the comment had drifted from the code
beneath it, and only reading the source surfaced it.

**Deviations: none.** No production behaviour changed beyond the comment fix.
`docs/architecture/documentation-tooling.md` remains the owner of the control
plane; DEVELOPMENT.md links to it rather than restating the DOC catalogue, per
Rule 1.

**Validation:** `pytest -q` -- **1532 passed**. `pre-commit run --all-files` --
all ten hooks pass. `doc_state_sync.py --check` exit 0. `ruff check` clean.

**Forward guidance:** the extraction plans
(`docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`
and `.../2026-09-12-reusable-frontend-ci-verification-components.md`) both
carry "do not execute until" conditions and neither is scheduled. The frontend
plan's stated line count for `frontend_gate.py` (4,008) is now 4,353, so
re-measure before relying on its inventory. PR #235's summary was completed in
the same session and its review threads are adjudicated in
`docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`.
