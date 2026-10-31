<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# FINDINGS_ARCHIVE -- page 0004

### F-B22-7: `AlbumMetadata.as_cache_row` is unreachable from application code -- RESOLVED

`scrobblescope/enrichment.py:19` builds the nine-element provider-aware cache
row that `cache._batch_persist_metadata` unpacks. Both production sites that
persist metadata build that tuple themselves instead:
`orchestrator/_details.py:137` inline as six elements (the Spotify shape) and
`orchestrator/_deezer_fallback.py:83` inline as nine. A repo-wide search finds
the method at its definition and in its own test
(`tests/services/test_enrichment.py:14,42`) and nowhere else, so no
application code path calls it.

Consequences worth naming. The persistence row order already has one owner,
`cache._batch_persist_metadata`'s docstring, so this method is a second copy
of that fact and a place for the two to drift. Its test asserts an order that
nothing writes, which reads as coverage of the persist path without exercising
it -- the false-confidence shape AGENTS.md's test-quality rules exist to
catch. `AlbumMetadata` is still genuinely used: `spotify.py:273` and
`deezer.py:144` construct it and read its fields. Only this method is unread.

Filed rather than fixed because removing a method and its test, or routing one
builder through it and deleting the other, is a choice between two working
shapes with a Batch 22 test contract around one of them. Owner call.

- [x] **Status:** resolved
**Completed:** 2026-09-23
the Spotify payload is translated only in `spotify.album_metadata_from_details`; every metadata row
is built by `AlbumMetadata.as_cache_row`, whose Deezer rows no longer carry an id in `spotify_id`;
the unused `enrich_albums` and its tests are removed.

### F-SWE-6: reading a job renews its TTL, so a polled job never expires -- RESOLVED

`get_job_progress`, `get_job_unmatched` and `get_job_context` each write
`updated_at` (`repositories.py:163`, `:175`, `:199`) while their docstrings
promise only to return a copy. `cleanup_expired_jobs` reaps on that same
field, so every `/progress` poll renews the lease.

Verified: a job backdated to three hours old, against a two-hour
`JOB_TTL_SECONDS`, survives `cleanup_expired_jobs` after a single read,
while an identical job that was never read is reaped. A browser sitting on
the loading page therefore keeps its `JOBS` entry alive indefinitely, which
matters most for a job whose thread died without setting a terminal state
(F-SWE-5).

Touch-on-access may well be intended -- results should not vanish while a
user is reading them. Nothing says so. Either document the side effect in
the three docstrings and in the `JOB_TTL_SECONDS` comment, or stop writing
from a getter and refresh the lease explicitly where it is wanted.
- [x] **Status:** resolved
**Completed:** 2026-09-23
Getters no longer write `updated_at`; `repositories.cleanup_expired_jobs` reaps on the last write only.
Source: SWE_PRINCIPLES_AUDIT.

### F-B21-26: the Tailwind index dropped its page-entry motion -- RESOLVED

The WP-3 index migration stopped loading `global.css` and removed the
existing entrance motion without giving that behaviour a Tailwind-owned
replacement.

`templates/index.html` empties the `legacy_css` block. The old index therefore
lost the `.card` opacity entrance and the slower `#logo-wrapper svg` fade that
still live in `static/css/global.css`. Neither the deployed `origin/main` tree
at `1bf888f` nor the current PR #220 Tailwind source defines an equivalent
page-entry animation.

The PR #220 mode-copy transition is a different interaction. It cross-fades
the Top Albums and Heatmap copy after a mode change; it does not animate the
composition when the page first appears. Merging that PR would restore the
mode-copy transition but would not close this finding.

Restore a Tailwind-owned, opacity-only entrance for the index composition and
leave its final state visible under `prefers-reduced-motion`. Add a browser
check against computed animation state so a stylesheet opt-out cannot remove
the behaviour silently again.

The deployed Adobe font faces loaded during the same browser comparison. The
visible type-scale difference is the older production calibration already
owned by F-B21-24 and corrected in the undeployed PR #220, not evidence of a
new font-loading defect.

- [x] **Status:** resolved
**Completed:** 2026-09-10
Fixed by `b1fdb121` and deployed with it; confirmed an ancestor of `origin/main` on 2026-09-23.
Was recorded as: resolved locally; deploy before the next production release.
Source: owner report and production/browser differential, 2026-08-28.

---

### F-B21-28: cached heatmap completion snaps from loading to a fully drawn result -- RESOLVED

When a saved heatmap job is already complete, the client sees 100 percent,
builds the complete result, hides the loading stage, and starts three nested
result fades in the same turn. The reader receives no painted handoff and the
whole screen appears at once. The loading phase also duplicates the `Pages
fetched` stat's page count, and its later detail claims "Building one day at a
time" after aggregation has already happened.

Keep the determinate hairline driven by the backend percentage, make the
stat the only page-count presentation, and crossfade exactly one prepared
result root with the loading stage. Use opacity and transforms only; retain a
motion-free direct result for reduced-motion readers. Replace the normal
loading route's `Back home` link with an honest `Cancel and return home`
control on both workflows. It returns home and does not cancel the background
job.

- [x] **Status:** resolved
**Completed:** 2026-09-10
Fixed by `47321b23`, completed by `b1fdb121`, and deployed with it; confirmed an ancestor of
`origin/main` on 2026-09-23.
Was recorded as: resolved locally; deploy before the next production release.
F-B21-43 supersedes the cached-ready part of this transition: the one-root
crossfade remains for an active job whose loader has painted, while an
already-complete saved job keeps that obsolete loader hidden and fades the
prepared result in directly.
Source: owner visual review and Impeccable performance finding, 2026-08-28.

---

### F-B21-29: wide-index form ignores the shared composition cap -- RESOLVED

At the wide-desktop breakpoint, `.index-form__inner` resets its 23.75rem cap
to `none` while the hero remains constrained. The form then fills the entire
right well instead of scaling as one composition, producing the owner-reported
oversized card and unstable side gutters. The shared header uses 44px page
links inside a 68px bar with narrow inter-link gaps, making the desktop
navigation feel cramped at browser zoom.

Restore the scaled form cap and centre it in symmetric inline padding. Give
the desktop header links and theme control a 48px target inside a taller bar
with one consistent sibling gap. Do not apply the hero scale to the header or
change the compact mobile shell.

- [x] **Status:** resolved
**Completed:** 2026-09-07
Fixed by `df28c06d`, completed by `8b37566a`, and deployed with it; confirmed an ancestor of
`origin/main` on 2026-09-23.
Was recorded as: resolved locally; deploy before the next production release.
Source: owner browser review, 2026-08-29.

---

### F-B21-27: private Last.fm profiles start jobs they cannot complete -- RESOLVED

The index validates only `user.getinfo`, which may confirm that a Last.fm
account exists while its recent listening remains private. The later
`user.getrecenttracks` call returns Last.fm error `17` with HTTP `403` for
that privacy setting. The heatmap then presents a misleading zero-scrobble
state after it has already started work.

Preflight `user.getrecenttracks` with `limit=1` during username validation.
Classify exactly error `17` / `403` as a private profile, tell the reader to
make recent listening public, and prevent submission. Enforce the same result
in both start routes; other failed responses remain service failures rather
than privacy claims. Do not reject a public profile simply because it has no
listening history.

- [x] **Status:** resolved
**Completed:** 2026-09-07
Fixed by `ee5ee4eb` and deployed with it; confirmed an ancestor of `origin/main` on 2026-09-23.
Was recorded as: resolved locally; deploy before the next production release.
Source: owner report and Last.fm API response classification, 2026-08-28.

---

### F-B21-10: error-page fallback can report 400 for other statuses -- RESOLVED

`templates/error.html` still defaults a missing `status_code` to 400.
The WP-2 audit found that callers did not supply their actual status, so
404 and 500 pages displayed a misleading badge.

PR #227 review remediation on 2026-09-07 supplied explicit 404 and 500 values
in the registered error handlers. The 2026-09-09 priority pass completed the
remaining routes.py call-site fix in F-B21-49: those callers now supply their
actual status or explicitly hide the badge for a normal empty state. The
template fallback remains for compatibility; app.py's CSRF handler uses that
400 default and also returns HTTP 400, so its badge already agrees.

- [x] **Status:** resolved
**Completed:** 2026-09-10
Fixed by `079c2b0c` and deployed with it; confirmed an ancestor of `origin/main` on 2026-09-23.
Was recorded as: resolved locally. F-B21-49 closes the remaining call sites; its
priority-fix commit and publication are pending.
Source: WP-2 template migration, 2026-08-23; PR #227 review, 2026-09-07;
call-site measurement, 2026-09-09.

### F-B20-3: Bootstrap loads from two CDN providers -- RESOLVED

`base.html` loads Bootstrap CSS from cdnjs while `index.html` loads the
JS bundle from jsdelivr; other pages use cdnjs. The original remedy
(consolidate to one provider before a Bootstrap 5.1 -> 5.3 upgrade) is
dead: Batch 21 removes Bootstrap entirely and resolves the split by
elimination (`docs/history/definitions/BATCH21_DEFINITION.md` WP-8 "closes F-B20-3").
WP-8 did so in `85e7511` on 2026-09-13: no template loads Bootstrap, and
`static/css/global.css` is gone. `origin/main`, which Fly.io deploys, predates
that commit and still loads both, so this stays active until `main` advances.
- [x] **Status:** resolved
**Completed:** 2026-09-19
Bootstrap and both CDN providers were retired by `85e7511` (Batch 21 WP-8); confirmed an ancestor of
`origin/main` on 2026-09-23.
Source: F-B19-4 owner review.

### F-B21-51: frontend_gate.py is nine times its largest sibling -- RESOLVED

`scripts/dev/frontend_gate.py` is 4,361 lines (2026-09-21). The largest other
module in `scripts/dev/` is `_frontend_gate_results.py` at 497, and the
largest unrelated one is `tailwind_build.py` at 404. AGENTS.md "Proposal and
Design Rules" item 3 compares against the largest peer rather than a line
threshold, and this is roughly ten times it. One module owns the import
bootstrap, the server fixture, CDN route policy, browser lifecycle, 27 check
implementations, their measurement helpers, the registry and the CLI.

- [x] **Status:** resolved
**Completed:** 2026-09-21

Rescoped 2026-09-21 from a batch work package to an owner-approved side
task, because pairing it with the routes and orchestrator split made that
batch far larger than planned. Plan of record:
`docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md`, one
commit per slice.

**Design, agreed 2026-09-11 and amended 2026-09-21.** `frontend_gate.py`
stays the only entry point and a stable facade, following `worktree_guard.py`,
with the `_frontend_gate_*` sibling convention `_frontend_gate_results.py`
set. Slice order: shared, assets, unmatched, forms, theme, layout, pipeline,
runtime.

| Module | Owns |
| --- | --- |
| `frontend_gate.py` | Facade: `sys.path` and environment bootstrap, viewports, `CHECKS`, groups, runner, CLI, re-exports |
| `_frontend_gate_shared.py` | Page inventories, `GATE_JOB_IDS`, `TOGGLE_TIMEOUT_MS`, `_reach_state` |
| `_frontend_gate_assets.py` | Stylesheet isolation |
| `_frontend_gate_unmatched.py` | The unmatched report check and its width sweep |
| `_frontend_gate_forms.py` | Validation, private profile, validator outage and races, year warning, initial visibility |
| `_frontend_gate_theme.py` | Theme tokens, divider contrast, persistence, blocked storage, mark, entrance motion, heatmap theme checks |
| `_frontend_gate_layout.py` | Fonts, text scaling, touch targets, scale parity, empty states |
| `_frontend_gate_pipeline.py` | Loading composition, progress state machines, spotlight |
| `_frontend_gate_runtime.py` | Playwright loading, browser launch, `serve_app`, CDN route policy |
| `_frontend_gate_colour.py` | Pure colour and contrast maths -- landed 2026-09-11 |

Two amendments to the 2026-09-11 design. A shared module is added, because
four slices read the page inventories and two read `_reach_state`; importing
them back from the facade would be circular. The `frontend_gate_checks.toml`
registry is deferred: it changes representation rather than location, and
folding it into each move would double every slice's parity surface. It
remains a candidate once the split has landed.

**Traps the plan closes.** A test patch aimed at the facade stops reaching
code that moved, and a patched constant stops reaching a sibling that
imported it; both still pass. `serve_app` mutates `MIGRATED_PAGES`,
`ALL_PAGES` and `GATE_JOB_IDS` in place, so every module must share those
objects. `scrobblescope.config` reads the provider keys at first import, so
no sibling may import `scrobblescope` above the facade's environment
bootstrap. `tests/scripts/dev/test_frontend_gate_split.py` pins the registry,
the patch targets and the import order.

**Slice 1 landed 2026-09-11.** The seven pure helpers moved to
`_frontend_gate_colour.py` and are re-exported by the facade, pinned by the
parity tests in `tests/scripts/dev/test_frontend_gate_colour.py`. They went
first because they take no `page`, so the browser gate was not needed to
prove the move.

**Measured end state, 2026-09-21.** `frontend_gate.py` is 535 lines.
The ten `_frontend_gate_*` siblings measure: `_frontend_gate_assets` 49,
`_frontend_gate_colour` 191, `_frontend_gate_forms` 434,
`_frontend_gate_layout` 1,176, `_frontend_gate_pipeline` 854,
`_frontend_gate_results` 497, `_frontend_gate_runtime` 156,
`_frontend_gate_shared` 71, `_frontend_gate_theme` 749, and
`_frontend_gate_unmatched` 490. The facade landed under the plan's 700-line
threshold, above its roughly-450-line estimate. The gate summary line is
unchanged: `[frontend_gate] 30 checks passed in 52 runs across chromium,
firefox`.

The split is two preparatory commits plus eight slices, oldest first:
`a06f6c2` (test(gate): Pin the invariants the frontend gate split must
keep), `30310c2` (refactor(gate): Delete dead helpers before the split
moves them), `04882a2` (refactor(gate): Move what several slices read into
a shared module), `7a7b599` (refactor(gate): Move stylesheet isolation
into its own slice), `6f1186f` (refactor(gate): Move the unmatched report
check into its own slice), `06a9ae7` (refactor(gate): Move the form and
validator checks into a slice), `bfc8749` (refactor(gate): Move the theme
and motion checks into a slice), `e172b3e` (refactor(gate): Move the
layout and scale checks into a slice), `2887c23` (refactor(gate): Move the
loading and pipeline checks into a slice), and `839fa3e` (refactor(gate):
Move the server and browser runtime into a slice).

**Two lessons from the split, recorded for the next one.**

Trap 2 (a patched constant the check no longer sees) was shown to be
silent in practice rather than merely possible. During the theme slice,
pointing the persistence test's `MIGRATED_PAGES` patch back at the facade
still passed, because the mocked page is not path-aware and the check ran
the same regardless of which page name it thought it was looking at. Only
the patch-target guard in `tests/scripts/dev/test_frontend_gate_split.py`
caught that class of defect; the test's own assertions did not.

Tests that reach a moved name by attribute access
(`frontend_gate.<name>(...)`) are invisible to both ruff and the
patch-target guard, because neither tool follows a call through the
facade's re-export to the module that now owns the name. The layout,
pipeline and runtime slices each found such calls only by grep. A future
split should grep for `frontend_gate\.<name>` per moved name, not rely on
ruff or the guard to surface it.

Source: PR #227 commit-range audit, 2026-09-09.

### F-B22-2: `assert` guards an invariant that `python -O` strips, at six sites -- RESOLVED

`assert` stands in for a runtime invariant check in six places across three
files. `python -O` strips `assert` entirely, so an optimized interpreter would
fall through to an `AttributeError` a few lines later instead of a clear,
intentional failure:

- `scrobblescope/routes/album_flow.py:89,154,309` -- `assert job_context is not
  None`, narrowing the type after a validation guard clears (`if err: return
  err`). Moved verbatim from pre-split `routes.py`; not introduced by WP-0.
- `scrobblescope/spotify.py:28,29` -- `assert SPOTIFY_CLIENT_ID is not None` and
  the same for `SPOTIFY_CLIENT_SECRET`, guarding the token request. A stripped
  assert here sends `None` as a credential rather than refusing.
- `scripts/docsync/findings.py:132` -- `assert heading_match is not None` in
  `_build`, whose only caller `_parse` passes lines that already matched the
  heading pattern.

Codacy flagged the `album_flow.py` group on PR #232 and the `findings.py` site
on PR #235; the original filing named only `album_flow.py`'s three sites and
cited line 302, which had drifted to 309. The class is the pattern, not the
package or the PR that noticed it, so all six are recorded here rather than one
finding per reviewer comment.

Fix shape: replace each with `if X is None: raise RuntimeError(...)` (or
`ValueError` where the input is external), matching the pattern of an
internal-invariant check rather than a `python -O`-dependent one. Small and
testable, but out of scope for WP-0's behaviour-neutral contract -- filed
separately rather than fixed in-PR.

Since 2026-09-21 (F-SWE-4) production refuses to start without either
Spotify key, so the `spotify.py` pair can only be reached in dev mode.

Resolved 2026-09-21, and not with the suggested raise at every site. Each
invariant was put where it actually holds:

- `album_flow.py`, three sites: deleted. `_get_validated_job_context`
  returns its error before it can return a missing context, so the
  `assert`s only narrowed types; three copies of a raise that cannot fire
  would have been dead code (Rule 3 at the third occurrence).
- `findings.py`: `_parse` already holds the heading match and now passes it
  to `_build`, so the invariant holds by construction.
- `spotify.py`, two sites: missing or empty credentials now return None,
  the function's existing failure answer, so callers fall back to Deezer.
  The `assert` had raised past that fallback and failed the whole job.

Ruff `S101` is enabled outside `tests/`, so a new production `assert` fails
the commit. The affected suites also pass under `python -O`.
- [x] **Status:** resolved
**Completed:** 2026-09-21
Source: Codacy bot reviews, PR #232, 2026-09-13, and PR #235, 2026-09-20.

### F-MAS-4: broad `except Exception` catches -- RESOLVED

17 instances across `scrobblescope/*.py` (recounted 2026-07-24; 14 at
the original sweep); narrow or add structured logging per exception
class.

Resolved 2026-09-21, and gated so the count cannot creep again. It had grown
to 25 across `scrobblescope/`, and each was judged on its own rather than
narrowed wholesale: most guard the optional DB cache or decorative
enrichment, where fail-open is the documented design (`global-rules.md` Rule
6), and narrowing them to guessed library types would turn today's tolerated
failure into a crashed job. Outcome: `lastfm.py`'s JSON catch narrowed to
`aiohttp.ContentTypeError` and `ValueError`, because it had labelled every
failure "Invalid JSON"; eleven already re-raised or logged a traceback, and
`run_async_in_thread` now does too; the remaining twelve each carry a one-line
reason and `# noqa: BLE001`, and the three degradation logs and the retry
helper now name the exception class. Ruff's `BLE` rules are enabled in
`pyproject.toml`, so a new unexplained broad catch fails the commit.
- [x] **Status:** resolved
**Completed:** 2026-09-21
Source: MULTI_AGENT_SWEEP.

### F-SWE-4: the production entrypoint never validates API keys -- RESOLVED

`config.ensure_api_keys()` (`config.py:37-40`) raises when any of the three
API keys is missing, and it is called only inside the `__main__` guard at
`app.py:140-145`. Production starts with `gunicorn app:app`
(`Dockerfile:15`), which imports the module rather than running it, so the
check never fires. Verified: with all three keys unset, `import app`
succeeds and serves, while `ensure_api_keys()` would have raised.

The same file gets the neighbouring case right. `_validate_secret_key` is
called from `create_app()` (`app.py:111`) and refuses to start in
production. One secret is checked at startup and three are not.

`spotify.py:26-27` is the only remaining guard for two of them, and it uses
`assert`, which `python -O` strips. Without the startup check a missing key
surfaces as a per-request failure, classified as an upstream outage.

Fix: call `ensure_api_keys()` from `create_app()`. One line, and it closes
two C cells in the audit matrix.

Resolved 2026-09-21, and it was not quite one line. An unconditional call
would have made every environment without the keys fail at import -- the
test suite and the frontend gate both import `app`, and CI's secrets arrive
empty when unavailable. So `create_app()` now calls `_validate_api_keys`,
which mirrors `_validate_secret_key`: refuse to start in production, warn in
dev mode. `tests/conftest.py` and `scripts/dev/frontend_gate.py` supply
placeholder keys the way they already supply `SECRET_KEY`. Four tests in
`tests/test_app_factory.py` cover it, including one that `create_app()`
itself refuses; the suite also passes with every key and `SECRET_KEY` empty
in production mode, which is CI without secrets. The `spotify.py` `assert`
remains, and is F-B22-2's to settle.
- [x] **Status:** resolved
**Completed:** 2026-09-21
Source: SWE_PRINCIPLES_AUDIT.

### F-B20-2: orchestrator.py second-pass decomposition (promoted from F-B18-1) -- RESOLVED

`scrobblescope/orchestrator.py` (916 lines) mixes album workflow, Spotify
batch processing, error mapping, progress tracking, and result assembly.
Now that `heatmap.py` provides a second pipeline, extract the shared
patterns (event loop setup including the win32 Proactor guard, progress
mapping, error guards) into a common module and split the orchestrator
into pipeline / processing / result-shaping modules. Also on the README
roadmap; absorbs F-B18-7.

Both halves are done. Batch 22 WP-0 split the orchestrator into the
`scrobblescope/orchestrator/` package by phase. The event-loop setup then
reached a third copy -- `background_task`, `heatmap_task` and the
release-check worker -- which is the point `docs/agents/global-rules.md`
Rule 3 says to extract, so on 2026-09-21 it became
`worker.new_thread_event_loop`, with its own tests and every existing
slot-release test passing unmodified. Progress mapping and error guards
still have two occurrences, album and heatmap, so Rule 3 says leave them;
Batch 23's export pipeline would be the third, and its WP-0 is where that
decision belongs.
- [x] **Status:** resolved
**Completed:** 2026-09-21
Source: Batch 18 audit.

### F-B21-50: reconnaissance TODOs in production code generated eight review rounds -- NO ACTION

Commit `769f0aa` added 15 `# todo:` comments to `scrobblescope/routes.py`,
mostly appended to bare HTTP status literals (`400,  # todo: Consider adding
client-side validation`). Commit `16fbf92` removed all 15. Net change to
`routes.py` is zero: the TODO count runs 0 at `b987e48`, 15 at `a53e412`, 0 at
HEAD.

Between those commits the notes cost eight repeated Qlty rounds. The PR #227
audit records `radarlint-pythonS1135` ("Complete the task associated to this
TODO") on 15 rows, at 15 distinct `routes.py` line numbers, each carrying an
occurrence count of 8 -- 120 comment bodies for one batch of notes.

The later priority pass corrected the first verification's "13 implemented /
two genuine" tally: twelve notes described existing behavior, two retain
deferred work (unmatched redesign and possible retirement of legacy POST),
and the results note exposed the remaining F-B21-49 status defect. Removing a
note did not implement the deferred work. The per-note evidence and refreshed
review counts are in
[PR 227 priority triage](docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md).
The eight-round count above remains the original audit's snapshot.

The lesson is about where such notes live, not whether to take them. A scratch
file or a findings entry costs one reader; a TODO in a linted production module
is a standing finding that every scanner republishes on every run, and a
reviewer cannot tell an orientation note from a real defect. Keep reading notes
out of production source.

No action, by owner ruling on 2026-09-21. The code half is clean: `git grep`
finds no `TODO` or `FIXME` in `scrobblescope/` or `app.py`. The churn stays in
history, because rewriting it needs owner authorization for a net-zero gain.
What remains is the guidance above, which is a lesson rather than a defect.
- [x] **Status:** no action
**Completed:** 2026-09-21
Source: PR #227 commit-range audit, 2026-09-09.
