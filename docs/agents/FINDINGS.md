# ScrobbleScope Findings & Open Issues

Last updated: 2026-09-21
Status: Batch 23 is active, opened 2026-09-21; Batch 22 closed 2026-09-20.
PLAYBOOK Section 3 owns the current work order.
2187 tests across 81 tracked test modules.
**Rotation policy:** resolved and no-action findings rotate to
`docs/history/findings/FINDINGS_ARCHIVE.md` at batch close-out or during
findings-cleanup WPs; nothing is deleted. Every item uses an
`F-<context>-<N>:` heading (format: AGENTS.md "Finding-Writing Rules").
Read this file on demand -- when a task or PLAYBOOK entry references an
F-* ID or a P0/P1 item -- not as part of the standard bootstrap order.

---

## Severity Key

| Level | Meaning |
|-------|---------|
| **P0** | Fix before next deploy or next batch |
| **P1** | Next batch |
| **P2** | Scaling roadmap / future consideration |
| **Info** | Documented design choice, no action needed now |

---

## P0 -- Fix before next deploy

None open. The four P0 items open until 2026-09-23 were fixed before PR #238 deployed; see the archive.

## Resolved this batch

## P1 -- Next batch candidates

### F-B21-25: every gate runs at commit time, so the session is unguarded

The documentation integrity gate, the compiled-CSS drift hook and the test
suite all run through `pre-commit`. They work: each was mutation-tested on
2026-08-26 and each caught its defect with the right code. They also share
one blind spot.

**Nothing runs at session time or at filesystem time.** Deleting local
files, removing a worktree, deleting a branch and force-replacing its
remote produce no commit, so no gate is consulted. On 2026-08-25 a session
branched from `origin/main`, made three commits with no PLAYBOOK Section 4
entry, renamed the branch over the retained one and replaced its remote.
Every gate stayed green. A reviewer caught the missing entry, not a check.

Three causes, each fixable on its own:

1. **The worktree guard was wired to nothing.** It exits 1 on an ERROR
   diagnostic and 0 otherwise, so it was built to gate, but it appeared in
   no hook and ran only when somebody chose to run it.
2. **Bootstrap was self-referential.** The rule that says to read
   `AGENTS.md` lives in `AGENTS.md`. A session that does not open it never
   learns it should. `.claude/settings.local.json` carried a permission
   allowlist and no hooks at all.
3. **What was lost was gitignored.** `skills-lock.json` is still missing.
   Git protects tracked files; the workflow depends on untracked ones and
   nothing declares which of them matter.

**Two structural defects in `AGENTS.md` itself.** Its "Session Bootstrap
(in order)" section opens with two fast-path paragraphs that authorise
skipping bootstrap, placed above the numbered list, so a skim finds the
exemption before the obligation. And the file has accumulated origin
narrative: agents editing it explain why a rule came to be written, which
serves the editor and not the reader. A bootstrap ruleset is read cold and
under pressure. Rationale belongs in a finding or a PLAYBOOK entry; the
rule should state the intent and stop. This is the specific mechanism
behind the length problem, and it is narrower than `F-STYLE-1`.

**Partly closed on 2026-08-26.** The guard now runs as the
`worktree-alignment` pre-commit hook, verbose so lineage is visible on a
passing run, and **advisory**: it prints and never gates.

That last word was wrong twice before it was right. The hook first shipped
gating, on the claim that only WT002, WT007 and WT014 are errors. A PR #220
reviewer corrected it: eleven of the fifteen codes are errors -- WT001,
WT002, WT003, WT004, WT005, WT006, WT007, WT008, WT012, WT014, and WT009
inside a linked worktree. WT003 fires for any branch the active batch does
not name, and WT004 for the identical-tree divergence a rebase merge always
leaves, so the gating version would have refused every commit on a feature
branch and every commit after a merge until realignment. The owner ruled it
advisory on 2026-08-26: the problem was that the guard's output was
invisible, not that commits needed a new gate. `--advisory` carries that,
and a test asserts it exits 0 on an ERROR while the same run without the
flag still exits 1.

The claim was wrong because the severity check grepped two of the guard's
six modules and generalised. That is the same incomplete-sweep mistake
`AGENTS.md` names, made while writing this finding about mechanisms that
only hold in one place.

It is skipped in CI, and the reason is worth keeping: the
first push went red on `ERROR WT007`, because `actions/checkout` makes a
shallow single-branch clone with no `origin/main`, so the guard failed
closed on a base ref that is legitimately absent. The guard measures
developer worktree lineage and a runner has no worktree topology to
protect, so the step sets `SKIP: worktree-alignment` rather than fetching
a base ref to satisfy a check that would then measure nothing. The
failure is itself an instance of this finding: a check added without
asking where it runs, whose assumptions held on one machine only. A `SessionStart` hook injects branch, working-tree state,
guard codes and the machine-managed status block into every new Claude
Code session, so the state arrives without depending on effort level,
model, or the model choosing to read. The second virtualenv the allowlist
had been authorising is deleted.

Remaining, and not started: a declared manifest of untracked-but-essential
files, in the shape of `config/docsync.toml` so the mechanism carries no
repository facts; and the two `AGENTS.md` defects above. The Codex/Copilot
entry point moved to F-B21-63.

**2026-09-25 (control-plane plan).** Items 1-2 are done: the two fast-path
paragraphs moved below the numbered bootstrap list, and `skills-lock.json`
is declared in `config/docsync.toml` `[untracked_essentials]`, warned about
(WT015) by `scripts/dev/_worktree_guard_essentials.py` when missing.
Retired 2026-09-28: nothing in the repository read `skills-lock.json`, so
it was removed from `[untracked_essentials]` (owner ruling); the
declared-manifest mechanism itself stands, empty until a real essential
needs it. The findings/issues sync (item 2's other half) is not built:
findings are not mirrored to GitHub (owner ruling, 2026-09-25). The
remaining AGENTS.md origin-narrative defect stays open.

Status: partly closed. The remaining items need an owner ruling, because
two of them edit `AGENTS.md`.
Source: workflow review after the worktree retirement, 2026-08-26.

### F-B23-11: titles shown next to Spotify artwork are Last.fm spellings

Spotify's guidelines ("Using our content", "For metadata") say "Track,
artist, playlist, and album titles must always be presented with the
metadata provided by Spotify." The results rows, the spotlight and the
unmatched report show `album`/`artist` from Last.fm, next to Spotify
artwork and links. P1, not P2, because it is the same compliance class as
F-B21-60, which the owner graded P1 ("a compliance defect, not a taste
question").

Fix shape: carry Spotify's album and artist names through `_results.py` and
the cache for Spotify-sourced rows, and render them. Deezer rows follow
Deezer's rules. More than a 20-line change.

Status: open (P1). Filed 2026-09-28, not in the Part C set (filed after
F-B21-60 was fixed); owner to schedule. Source: F-B21-60 "To check", Task 1
of the 2026-09-28 review workspace.

### F-B23-18: unmatched artist portraits show Spotify photos with no link back to Spotify

A release-scope or no-match row without album artwork loads the artist's photo from
`/api/artist_spotlight` into `.unmatched-artist-image` (`static/js/unmatched.js`,
`fetchArtistImage`). The reply carries `spotify_url`; the script discards it, so the photo
links nowhere. The results page's spotlight links its photo's artist to Spotify
(`results-spotlight.js`, `renderLink`), and the unmatched banner says the page shows
"artist photos from Spotify". Spotify's design guidelines ask for content to link back to
Spotify. Grouped with F-B23-11 (also P1, Spotify metadata presentation) for the owner:
adding a link makes each portrait a Tab stop and changes the row's reading order, which is a
design decision for the page the owner delegated.

- [ ] **Status:** open (P1). Source: second /code-review of PR #245, Section F, finding F5,
  2026-09-29.

### F-B23-9: F-B21-18's residual items -- export contract deviation and duplicated validators

Batch 23 WP-0 frontend Task 1 built the harness for F-B21-18's `rocketColor`,
`countToNorm` and export-header scope, but F-B21-18's text also carried two
more items that harness does not touch, and no live register now covers
either (checked: `git grep` outside `docs/history/`, `docs/logarchive/` and
`docs/superpowers/`):

**(a) The export contract deviation.**
`docs/design/components/heatmap/HeatmapFrame.prompt.md` requires JPEG export
to render the desktop 53x7 grid at every viewport, while `saveHeatmapImage()`
still serializes whichever mobile or desktop SVG is on screen at export
time. Its own docstring records the deviation, but no owner ruling adds it
to `docs/design/RECONCILIATION.md`.

**(b) The duplicated validators.** `static/js/index.js` and
`static/js/heatmap.js` each own their own username-validation state machine.
Both now compare request generations to avoid the A-to-B-to-A staleness bug
an earlier review found, but centralising the shared base is deferred until
broader browser parity checks cover both consumers -- refactoring it sooner
would trade a demonstrated shotgun-surgery bug for an unproved rewrite.

Origin: F-B21-18 (`docs/history/findings/FINDINGS_ARCHIVE.md`), archived
2026-09-26 for its harness scope only; these two items were not part of that
closure. Joins WP-0 Part C's set by controller ruling 2026-09-26
(`BATCH23_DEFINITION.md` Part C).

Status: open (P1). Source: Batch 23 WP-0 frontend Task 1, fix round 1 code
review, 2026-09-27.

## P2 -- Scaling roadmap

### F-DOCSYNC-16: docsync silently ignores an `allow_after` marker that matches no line

`check_retired` (`scripts/docsync/declarations.py`) compares a raw file line
against a declared `allow_after` marker with `line.strip() == marker.strip()`
-- exact equality, no prefix match -- and when nothing matches, `exempt_from`
simply stays `None`: the declaration silently loses its whole history
exemption for that file, with no warning that the marker itself is dead. The
three `[[retired]]` declarations in `.docsync.toml` that predate this finding
all declared `[retired.allow_after] "PLAYBOOK.md" = "## 4. Execution log"`,
but the real `docs/agents/PLAYBOOK.md` heading is `## 4. Execution log (for agent
handoff)`, so none of the three matched anything. Reproduced directly against
`check_retired` with the real heading text: a claim placed below the heading
was still reported, not exempted (confirmed 2026-09-24, Task 5's live probe
for the new fourth declaration that task added).

**Impact was latent, not live.** No dated Section 4 entry restated
`limit_results ... thresholds disclosure`, `fonts self-hosted under
static/fonts/` or a bare `DOC001-DOC011`, so `--check` on the real corpus
never actually exercised the mismatch before it was caught. It would have
surfaced as a false-positive DOC011 the day a dated entry legitimately quoted
one of those retired phrases as history.

**The three markers are corrected in `.docsync.toml`** (2026-09-24, Task 5
fix round) to the real heading text, matching the fourth declaration that
task added, which used the correct text from the start. That corrects this
one instance; the finding stays open because the mechanism -- a declared
`allow_after` marker can silently match nothing, for any file, and nobody is
told -- is still unchecked, so the next marker written this way fails the
same way undetected.

**Fix shape, not yet built:** a declaration check that errors when an
`allow_after` marker matches no line in its named file (a new check; not
built here).

- [ ] **Status:** open (P2). Source: Batch 23 WP-0 foundation Task 5 live
  probe, 2026-09-24.

### F-DOCSYNC-19: `--check` has no diagnostic for an interrupted publication

Transactional publication recovers a crash mid-publish by replaying its
journal against the on-disk state on the next writer, but a read-only
`--check` run gives no signal that a journal is present and an earlier
publish was interrupted -- recovery exists, a diagnostic does not.
- [ ] **Status:** open (P2). Source: `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md`
  DoD row 29, GPT Sol Max review.

### F-DOCSYNC-20: the docsync close-out review's carried-over Minors, still true at HEAD

The docsync close-out plan's final review (PR #234 round) covered automated
tool reports on the engine commit but never worked its own ledger's
carried-over triage list of "minor (deferred)" items from Tasks 1-4a; checked
individually against the code and tests at HEAD, eleven were still true. The
owner ruled one of them intended behaviour on 2026-09-24 -- `--cold-storage`
may repaginate a never-paginated monolith -- so it is dropped here and ten
remain.

- `transaction.py`: `_atomic_write` and `_restore` both write through
  `_stage_and_replace`, but every rollback fault-injection test
  (`test_publication_failure_rolls_every_file_back`,
  `test_interruption_restores_exact_bytes`,
  `test_a_failed_run_restores_a_file_it_had_already_deleted`) patches only
  `_atomic_write`, so none proves a rollback write itself surviving a
  disk-full condition.
- `findings.py`: the DOC017 branch of `_lifecycle_issues` reads `body_lines`
  from `prose_lines()`, which excludes fenced and commented text, so a "no
  action" explanation written only inside a fence still trips DOC017 as a
  false positive.
- `findings.py`: the DOC014-vs-DOC015 branch still selects the code by
  `PENDING_QUALIFIER_RE`'s literal word list, so it can still misattribute
  the diagnostic on a non-terminal outcome that happens to use one of those
  words.
- `test_undated_entries_keep_their_page_hot`
  (`tests/test_docsync_archives.py`) still asserts
  `any(page["location"] == "hot" for page in pages[:-1])` rather than naming
  the page holding the undated entry, so a masking pass remains possible.
- `archives.py`: `normalize()` (via `_join`) still joins entries with a fixed
  blank line, collapsing original blank-line spacing; conservation holds
  modulo normalization, not byte-for-byte.
- `transaction.py`: `publish(root, {}, {})` with both maps empty still never
  resolves `root`, so a nonexistent root surfaces `_exclusive_lock`'s raw
  `FileNotFoundError` rather than `SyncError`.
- `tests/test_docsync_archives.py` still has no test pinning that a fenced
  `### ` heading is not a page or entry boundary, unlike `findings.py`'s
  `test_fenced_example_heading_is_never_a_finding`.
- A deleted archive index with surviving `pages/` files still reports no
  DOC020. Confirmed live: `--check` instead fails with a generic "Required
  file is missing" (exit 2), and `--paginate-archives`/`--cold-storage`
  silently skip the archive entirely because `_managed_archive_paths`
  filters by `path.is_file()` -- `ArchiveStore._load`'s own orphan-page guard
  is unreachable from the CLI for this exact case.
- `install_docsync_hook.py`: no test gives `SKIP` a prefix collision (a hook
  id preceded by extra characters before the comma);
  `test_generated_wrapper_does_not_skip_for_unrelated_skip_value` covers only
  a suffix collision.
- `install_docsync_hook.py`: `install()`'s containment-refusal message still
  prints `disclosure.hook_directory`, the unresolved candidate, rather than
  the resolved path `hook_directory_is_contained` actually compared.

- [ ] **Status:** open (P2). Source: the docsync close-out plan's final-review
  triage list, and `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md`
  Task 7 / DoD row 32.

### F-DOCSYNC-23: the tracked test-module count is hand-maintained and unchecked

`.claude/SESSION_CONTEXT.md` Section 1 ("across N tracked test modules") and the
`docs/agents/FINDINGS.md` header carry the same count, but `doc_state_sync.py
--fix --test-count N` writes only the test count to both -- nothing derives or
checks the module count, and nothing checks that the two copies agree.
Batch 23 control-plane Task 7 needed a hand fix, 72 -> 73 (`c39da3c`), because
`--fix` had left SESSION_CONTEXT's copy stale after FINDINGS.md's was
corrected.

Measured now (2026-09-27) the way the current number is counted -- `git
ls-tree -r --name-only HEAD tests | grep -c '/test_[^/]*\.py$'` -- gives 78,
matching both SESSION_CONTEXT's and FINDINGS.md's current copies: **both
sites are right today.** (`tests/scripts/dev/test_mutation_test.py` is
untracked, per F-SWE-8, so it does not count.)

Proposal, not yet built: derive the module count in `--fix` from `git
ls-files 'tests/**/test_*.py'` instead of hand-editing it, or declare it as a
value fact in `config/docsync.toml` so a mismatch is caught the way DOC008
catches a stale test count.

- [ ] **Status:** open (P2). Source: Batch 23 WP-0 close-out CO2, 2026-09-27.

### F-WORKTREE-6: the guard's base ref is a flag default, not a fact PLAYBOOK declares

`check_worktree_alignment.py --base-ref` defaults to `origin/main`, and
nothing lets the guard learn a branch's actual base from PLAYBOOK, so a
branch cut from `test` reads as diverged or behind until the agent knows to
pass `--base-ref origin/test` by hand. It is worse since PR #241 merged
into `main` on 2026-09-24: against `origin/main` the guard now reports
WT006 (behind) while the branch has nothing past the merge, and WT005
(diverged) once it does, with an empty merge-base diff. When this was filed,
F-WORKTREE-3's open items were the between-batch ancestry skip, a dirty
detached worktree missing WT010, and the doubled base-ref label -- none was
this defect, so this is a separate finding. F-WORKTREE-3 has since been
archived.
- [ ] **Status:** open (P2). Source: found opening Batch 23, 2026-09-21;
  sharpened by `docs/history/reports/HANDOFF_2026-09-24.md` section 2 after
  PR #241 merged, 2026-09-24.

### F-B22-5: the release-year lookup has a precision path it does not use

`lookup_original_release` (`scrobblescope/musicbrainz.py`) finds a release
group by searching artist and title text, then guards the result with a score
floor and a normalized identity check. It is one request and it is usually
right. It is not exact, and two measured cases show the edges.

**Measured against the live APIs, 2026-09-20**, five albums, one request per
second:

| Album | Spotify's date | URL path | Search path |
| --- | --- | --- | --- |
| The Beatles (White Album) | 1968-11-22 | 1968-11-22 | top candidate scored 100 with **no** `first-release-date` |
| Rumours | 1977-02-04 | 1977-02-04 | 1977-02-04 |
| Kind of Blue | 1959-08-17 | 1959-08-17 | 1959-08-17 |
| Geogaddi | 2002-02-19 | **not mapped (404)** | **no candidate returned** |
| Stratosphere | 1998-02-24 | 1998-02-24 | 1998-02-24 |

**The URL path.** `GET /ws/2/url?resource=https://open.spotify.com/album/<id>&inc=release-rels`
returns a "free streaming" relation to a MusicBrainz **release** when an
editor has mapped that Spotify album. A second request on that release with
`inc=release-groups` yields the release group's `first-release-date`. It is
exact -- no scoring, no name matching -- and it answered two cases the search
path did not. It costs **two requests where the search costs one**, which at
one request per second is the whole budget doubled, and it needs a Spotify
album id, so it can never serve a Deezer-only album.

Note for anyone implementing it: `inc=release-groups` on the `url` endpoint
returns nothing. The relation include is `release-rels`, and the target is a
release, not a release group. `inc=release-group-rels` returned zero
relations for the same album.

**The ISRC path is not viable as a third option.** `GET /v1/albums/{id}`
returns simplified track objects with **no** `external_ids`, confirmed by
reading the keys off a live response, so every ISRC costs an extra Spotify
request. `GET /ws/2/isrc/{isrc}` then returns *recordings*, and a recording's
earliest release group may be a single or a compilation rather than the album
-- dating an album by its lead single is worse than not correcting it.

**Recommended shape, not yet built:** keep the search as the primary path,
and spend the second request only where it buys something -- when the search
returns no candidate, or a candidate with no `first-release-date`, and the
album has a Spotify id. Cache the outcome under the existing
`(artist_norm, album_norm)` key, never under a Spotify id: 9 of the 10 albums
Spotify could not enrich in the owner's 2026-09-20 run were rescued by
Deezer, and those have no Spotify id at all.

**Also measured:** adding `AND type:album` to the Lucene query, as proposed,
would exclude EPs, which this application ranks alongside albums --
`normalize_name` deliberately strips "ep" from titles. The release-group
search field is `primarytype`, not `type`. If the query is narrowed at all,
it should be to exclude live albums and compilations by secondary type, not
to require a primary type.

- [ ] **Status:** open (P2, owner-gated -- a scope decision, not a defect)

Source: owner proposal and live probes, 2026-09-20.

### F-B22-6: server-sent events would consume the whole thread pool

Replacing the results page's polling with an SSE stream was proposed. It does
not fit this deployment. Gunicorn runs `--workers 1 --threads 4`
(`Dockerfile`), and an SSE response holds its worker thread open for the life
of the connection. Four readers with a results page open would occupy every
thread, and the fifth request -- any request, including the home page --
would wait for one of them to disconnect.

The current design has the opposite shape: a poll every two seconds that
stops at a terminal state, pauses while the tab is hidden, and holds a thread
only for the milliseconds each reply takes.

SSE would become reasonable only alongside a different serving model, which
is a larger change than the feature it would serve.

- [ ] **Status:** open (P2, no action recommended)

Source: owner proposal, measured against the Dockerfile, 2026-09-20.

### F-B21-62: the design system's status colours are documented but undefined

`docs/design/README.md` names three status colour pairs -- `--ss-good`
`#2f7a4a`/`#6fcf97`, `--ss-warn` `#b35a1f`/`#e0a458`, `--ss-bad`
`#b03434`/`#e07070` -- and states what they are for: "3px rules and mono
kickers, never as full-bleed tinted cards". No stylesheet defines any of the
three. `test_every_custom_property_a_page_reads_is_defined_by_a_sheet_it_loads`
fails any page that reads one, so the documented treatment cannot be used at
all, and the first attempt to use it (the release-correction kicker, Batch 22
WP-4 Task 11) had to pick a different token.

This is the `docs/ARCHITECTURE.md` rule in another form: the document is a
claim about the code that nothing checked, and the code wins. Either the
tokens ship in `static/css/tailwind.src.css` for both themes, or the README
stops describing a treatment nothing can apply. Sizing is small; deciding
which way is a design-system call, not an implementation one.

- [ ] **Status:** open (P2, owner-gated)

Source: Batch 22 WP-4 Task 11, 2026-09-20.

### F-SWE-8: the mutation-test runner is written, unadopted, and uncommitted

`scripts/dev/mutation_test.py` and `scripts/dev/mutation_scope.toml` exist in
the working tree and are not committed. They were built during the docsync
close-out side task, run for the first time against `scripts/docsync/`, and
that first run found four real defects in the runner itself, the fourth
needing a rework rather than a patch. The owner's call on 2026-09-20 was that
mutation testing is not adopted on the strength of a tool that had never been
run: finishing it is a work package of its own, and the code stays out of the
corpus until then.

This is recorded here because it was recorded nowhere a clone can read. The
only written copy was a section of the gitignored CLAUDE.md at the repository
root, and that section was deleted the same day once the work it tracked
merged. DOC001 is the reason that file name carries no backticks here: a
concrete Markdown reference has to name a tracked file, and it is not one.

Do not stage those two files as part of another task's commit, and do not
treat the runner's output as evidence until its own defects are fixed.

- [ ] **Status:** open (P2, owner-gated)

Source: docsync close-out side task, 2026-09-20. It is a future work package
rather than a defect in shipped code.

### F-B22-4: provider attribution on results/unmatched rows is text, not each provider's official logo

Batch 22 WP-2 Task 6 added a per-row attribution link (`.provider-badge` in
`templates/results.html` and `templates/unmatched.html`) naming the album's
provider and linking to its `album_url`. Deezer's developer guidelines
require "a clearly visible Deezer Logo" for any app using its API
(developers.deezer.com/guidelines#local, /guidelines/logo); F-B21-60 records
the equivalent Spotify ruling ("Use Spotify's asset as supplied, not a
redrawn glyph"). Neither provider's actual logo file could be sourced from
an agent session: no image-fetch tool was available, and guessing a brand
CDN URL to hotlink was rejected as unsafe. The owner chose the text-badge
interim over blocking Task 6 on asset sourcing (2026-09-13).

Fix shape: replace `.provider-badge`'s text content with each provider's
official logo asset once the owner supplies the files (or an agent gains
image-fetch tooling) -- swap the `<a>`'s text node for an `<img>`/inline
`<svg>` sized per that provider's own minimum-size rule (Spotify: 21px+, per
F-B21-60's owner ruling; Deezer: size unspecified on the guidelines page
itself, deezerbrand.com carries the detail but did not render for an agent
session). Small and self-contained; no test rewrite beyond swapping the
`provider-badge` element type assertions.

Spotify's half is closed under F-B21-60 as of 2026-09-28 (official icon,
attributed once per list). Deezer: developers.deezer.com/guidelines/logo points to
deezerbrand.com, a Frontify portal whose API needs a signed-in user and
whose files are served from media.ffycdn.net, not a Deezer domain. The
owner must supply the Deezer logo file.

Status: open (P2), Deezer only. Source: Batch 22 WP-2 Task 6, 2026-09-13.

### F-B22-3: job endpoints trust an unguessable job ID with no session ownership check

`scrobblescope/routes/api.py` (`unmatched_data`, `progress`) and
`scrobblescope/routes/heatmap_flow.py` (`heatmap_data`) accept `job_id` from
a query parameter and look it up in the process-local `JOBS` dict with no
check that the requesting session originated that job. `create_job`
(`scrobblescope/repositories.py:41`) generates `job_id = uuid4().hex` -- a
128-bit unguessable value -- so the design already relies on the ID itself as
a bearer/capability token rather than session-bound ownership. This is
consistent across every job-polling endpoint, not a WP-0 regression: the
pre-split `routes.py` had the same shape.

Graphify's PR #232 review flagged two instances (`api.py:103`,
`heatmap_flow.py:179`) as missing an "ownership check," unverified
(consensus-only, no reproducing execution). Read as a security question
rather than a bug: is a 128-bit unguessable ID sufficient authorization for
an ephemeral (TTL-bounded, `JOB_TTL_SECONDS`) result set, or should these
endpoints also require the ID to match the requesting session's
`_LATEST_ALBUM_JOB`/`_LATEST_HEATMAP_JOB`? No incident or reported leak
motivates this; filed for owner judgment, not because current behaviour is
demonstrated wrong.

Status: open (P2, owner-gated). Source: Graphify bot review, PR #232,
2026-09-14.

### F-B23-1: album calculation writes its exclusions into the job instead of returning them

`orchestrator/_results._build_results` takes `job_id`, returns the album rows,
and sends each release-scope exclusion out through a hidden
`add_job_unmatched` call on the facade. So a test of a corrected-date
exclusion has to create a real job and read it back
(`tests/services/test_orchestrator_helpers.py` does). The calculation's
answer is also split between its return value and a side effect.

Batch 23 WP-6 adds per-album statistics to this same module. A calculation
that returns rows, exclusions and statistics together, with the caller
publishing them to the job, would give WP-6 a place to land those statistics
that can be tested without a job.

A migration can leave the Last.fm path's tests unmodified: add the pure
calculation, and keep `_build_results(cache_hits, job_id, ...)` as a thin
wrapper that publishes its result. The existing `orchestrator.add_job_unmatched`
patch target then still holds.

Status: open (P2). Owner timing, 2026-09-23: settle it after WP-0's provider
repairs and before WP-6's detailed design. Scheduling it inside Batch 23 needs
an explicit scope amendment, and `BATCH23_DEFINITION.md` WP-6 carries that
decision point. Source: card 01 of
`docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`
(2026-09-23).

### F-B23-2: Last.fm's payload shape travels into both calculations

`lastfm.py` returns raw JSON pages. `orchestrator.fetch_top_albums_async`
then reads `recenttracks`, `track`, `album.#text`, `artist.#text` and
`date.uts` itself, and `heatmap._aggregate_daily_counts` reads `recenttracks`
and `date.uts`. A change to Last.fm's payload therefore reaches two
calculations, and WP-6's first-listen and busiest-hour statistics would add
more of the same reads. Global Rule 4 puts that translation inside the
provider module.

The fix is to have `lastfm.py` translate the payload into native listening
facts, keeping completeness explicit. Two differences must survive:
- the heatmap counts dated rows even without album metadata, while album
  aggregation needs artist, album and track;
- the Spotify-export rules (30 seconds, private sessions) must not be imposed
  on Last.fm.

It cannot land inside Batch 23 as-is: `tests/test_heatmap.py` feeds
`_aggregate_daily_counts` raw pages, and Batch 23 keeps the Last.fm path's
tests unmodified. It is separate from F-B22-7, which translates Spotify's
metadata payload.

Status: open (P2). A parity refactor for a batch after Batch 23. Source:
card 02 of `docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`
(2026-09-23).

### F-B23-3: the album pipeline runs the cache connection protocol itself

`orchestrator.process_albums` opens the cache connection, holds it across
provider work, and closes it in a `finally`. Meanwhile
`orchestrator/_cache.py` owns the cache-failure policy, including writing job
warnings through the facade. So understanding what "the cache is optional"
means takes both modules. It also makes the connection-closure test in
`tests/services/test_orchestrator_process_albums.py` configure the provider
machinery.

The fix is for the existing cache module to own the operation's lifetime and
its failure classification, while job messages and enrichment decisions stay
with the caller. There is one concrete adapter, so no generic cache-backend
layer. Metadata and release-check cache policy stay separate.

Status: open (P2). F-B22-7 and F-B22-8 have both landed (reconcile Tasks
4-6 and 11); reassess against the code they left. No performance gain is
claimed. Source: card 03 of
`docs/history/reports/ARCHITECTURE_DEPTH_2026-09-23.html`
(2026-09-23).

### F-B23-4: the frontend gate's touch-target check failed once on a tree that passes

At `ffbee0e` the frontend gate failed once, and then passed three times on
the same tree. The failure was in `check_touch_targets`
(`scripts/dev/_frontend_gate_layout.py`), in the wide-touch profile, on the
404 page:

```
touch targets [wide touch]: /no-such-page-for-the-gate [as loaded]: a.btn is 124x40, smaller side under 44px
touch targets [wide touch]: /no-such-page-for-the-gate [as loaded]: button.btn is 89x40, smaller side under 44px
```

40px is the plain `.btn` height. On the 404 page the 44px comes from one
rule in `static/css/error.css`:
`@media (any-pointer: coarse), (max-width: 859.98px)`. The wide-touch
profile is 1280px wide, so only the `any-pointer: coarse` half can match
there. The mobile profile also matches on width, which is why it never
failed. So at measurement time that rule was not in effect. Either
`error.css` had not applied yet, or the emulated touch pointer was not yet
reported to the page. The check measures straight after
`page.goto(..., wait_until="load")`, with nothing waiting for either.

Not caused by the commit under test: that commit (reconcile Task 7) did not
touch `error.css`, `templates/error.html` or the gate's layout checks.

Status: open (P2). Non-blocking, by owner ruling 2026-09-23. Until it is
fixed, a frontend-gate failure that the implementer's runs did not show is
re-run once before anyone acts on it. The fix should make the check wait for
the state it measures, not add a retry. Source: the gate-runner's run for
Batch 23 WP-0 reconcile Task 7 (2026-09-23). Its logs are in a git-ignored
SDD workspace on the owner's machine; the failure lines above are quoted
from them.

### F-B23-10: three frontend-gate failures were gate defects, each green on an immediate rerun

Three intermittent `frontend_gate.py` failures during the WP-0 frontend
plan's landings, none reproducing on a rerun of the same tree, so each is a
gate defect rather than a code regression:

1. **`chromium: divider contrast [desktop]/dark`** failed once in the
   frontend Task 1 landing (2026-09-26); clean on rerun, and clean on a
   fresh `git archive` of the base commit (`9523603`). See the frontend
   plan's Task 1 landing report, evidence held in the plan's SDD workspace.
2. **The gate hung** once in the frontend Task 4 landing (2026-09-27), on an
   apparently stalled `Thread-2 (runner)` after a mocked Spotify 400; the two
   Python processes were killed and a clean rerun finished normally. See
   the frontend plan's Task 4 landing report.
3. **`chromium: pipeline state machines [desktop]`** raised `Error:
   Page.evaluate: Execution context was destroyed, most likely because of a
   navigation` once in the frontend Task 2 fix-round-2 landing (2026-09-27);
   green again on an immediate rerun. See the frontend plan's Task 2 fix
   round 2 report.

Each check currently relies on timing (a fixed wait, or none) rather than an
explicit condition, and nothing in the gate enforces a per-check timeout, so
a stall hangs the whole run instead of failing loudly.

Proposal, not yet built: rewrite each of the three checks to wait on an
explicit condition instead of a timer, and add a per-check timeout to the
gate runner so a stalled check fails fast rather than hanging.

- [ ] **Status:** open (P2). Source: Batch 23 WP-0 frontend Task 1, Task 4
  and Task 2 fix round 2 landings, 2026-09-26/27; close-out CO2, 2026-09-27.

### F-B23-15: the unmatched cover ruling calls 4rem / 4.5rem "the Results size", but Results rows are 3rem / 3.5rem

RECONCILIATION section 16 records the owner's 2026-09-13 ruling. The
unmatched cover ships at 4rem below 768px and 4.5rem from it, called "the
Results size". Results rows draw their covers at 3rem and 3.5rem:
`w-12 h-12 md:w-[calc(3.5rem*var(--results-scale))]` in
`templates/results.html`, where `w-12` compiles to `var(--spacing-12)`, 3rem.
The 4rem / 4.5rem figures are `.album-cover-img` and `.album-cover-placeholder`
in `static/css/results.css`. No template, script or Python module has ever
used those classes: `git log --all -S album-cover-img -- templates static/js
scrobblescope` finds nothing, and they came into results.css with 7a46d38a.
Not changed: the ruling's numbers are explicit, and `check_unmatched_report`
pins them. The owner decides: keep 4rem / 4.5rem and correct the ruling's
premise, or match the Results rows. Either way both classes, with their
`object-fit: cover`, are dead CSS. `docs/design/designsystemaudit.md` also
states 4rem / 4.5rem for Results rows; it is a dated record and was not edited.

- [ ] **Status:** open (P2). Source: Task 7 audit of the unmatched page, 2026-09-28.

### F-B23-13: the "Save image" JPEG export clips the artist line under each album title

Seen during Task 1's export checks (F-B21-60 part 2 landing): the results
page's "Save image" JPEG export clips the artist line under each album
title. Pre-existing, not Spotify-specific.

Status: open (P2). Source: Task 1 code report, 2026-09-28.

### F-B23-16: the error classifier matches bare substrings

`scrobblescope/errors.py` `classify_exception_to_error_code` answers `user_not_found` for any
exception message that contains both "not found" and "user", in any case, and
`spotify_rate_limited` or `lastfm_rate_limited` for any message holding "Too Many
Requests". Both pipelines call it on every unhandled exception before falling back to
`internal_error`: the album pipeline (`orchestrator/__init__.py`, `_fetch_and_process`)
and, since this branch, the heatmap pipeline (`heatmap.py`, `_report_heatmap_failure`). No
current raise site produces a colliding message, so nothing is misreported today; an
unrelated exception whose text happens to hold both words would be blamed on the user. The
fix is a typed exception for the Last.fm 404 (and the rate limits), classified by type, which
is larger than a fix-wave change. The same typed exception is the fix for F-B23-21
(`reraise=(ValueError,)` in the Last.fm page fetch), so the two land together.

- [ ] **Status:** open (P2). Source: second /code-review of PR #245, Section A, finding A3,
  2026-09-29.

### F-B23-17: a Section 4 Validation line with no number passes --check

Two landings on 2026-09-29 committed the entry template's placeholder,
`` Validation: `pytest -q` -- **N passed**. ``, with the letter N in place of the count
(36ade83 and 95973fd; filled in by 931828d). `doc_state_sync.py --check` exited 0 on both.
DOC012 (`scripts/docsync/integrity.py`, `_check_unbolded_test_counts` and
`_unpaired_result_issue`) looks only for digits: `_EXPLICIT_CLAIM_RE`, `TEST_COUNT_RE`,
`_UNPAIRED_RESULT_RE` and `_UNBOLDED_COUNT_RE` all need one, so an entry whose only count is
a letter records nothing and raises nothing. With the count pinned in
`config/docsync.toml`, Section 4 is not re-scanned for the number, so the dashboards stay
right; what is lost is the entry's own evidence, silently. Fix: DOC012 flags a
Validation-trigger line whose bold count holds no digit.

- [ ] **Status:** open (P2). Source: controller check of the 36ade83 and 95973fd landings
  and the Task 9 sdd-reviewer, 2026-09-29.

### F-B23-19: a non-square spotlight photo is letterboxed inside a rounded box, so the photo's own corners are square

`.spotlight-artist-photo` uses `object-fit: contain` inside `.spotlight-image-box`, which
rounds and clips (`static/css/results.css`). A non-square artist photo (the review's
case was 640x427) is letterboxed: the rounded corners fall on the empty band and the
visible photo keeps square corners. RECONCILIATION section 18 rejected exactly this for the
unmatched portraits and sized them by their own ratio instead (`data-portrait`). The
spotlight's "square, uncropped photo" is an owner ruling (F-B21-60), so rounding the photo
rather than its box is the owner's call. Album covers are square and unaffected.

- [ ] **Status:** open (P2). Source: second /code-review of PR #245, Section F, finding F4,
  2026-09-29.

### F-B23-20: the spotlight card waits for every candidate before showing any

`results-spotlight.js` hydrates every candidate with `Promise.all` and reveals the card only
when all have settled, so one slow artist holds the card back for up to `HYDRATE_TIMEOUT_MS`
(8s) after the first confirmed photo is ready, and the card then appears late in the sticky
rail and pushes the rail's content down. Showing the first confirmed candidate at once and
adding the rest to the rotation as they settle would avoid both.
The third review of PR #245 (S2-23) adds that every candidate's photo is preloaded at page
load (five requests against one on `main`); preloading one ahead of the rotation belongs
to this finding.

- [ ] **Status:** open (P2). Source: second /code-review of PR #245, Section F, finding F8,
  2026-09-29.

### F-B23-21: `reraise=(ValueError,)` in the Last.fm page fetch ends the job on any ValueError, skipping every retry

`scrobblescope/services/lastfm.py` `fetch_recent_tracks_page_async` passes `reraise=(ValueError,)` to `retry_with_semaphore` so that the 404 "user not found" it raises as a `ValueError` is not retried. That tuple matches every `ValueError` subclass, so a non-integer or HTTP-date `Retry-After` (the header parse raises `ValueError`) and a non-UTF-8 error body (`UnicodeDecodeError`) also skip all three attempts and end the whole job: `internal_error` in the heatmap, the raw exception text in the album pipeline. The mechanism was reproduced in the review; no live trigger has been seen. The fix is the typed not-found exception that F-B23-16 already proposes, with `reraise` narrowed to it, plus a defensive `Retry-After` parse and `text(errors="replace")` on the error body. This is the same typed exception as F-B23-16, so land them together.

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), S1-4.

### F-B23-22: the album pipeline answers an unclassified exception with `unknown`, retryable, and the heatmap with `internal_error`, though the docstrings claim parity

`scrobblescope/orchestrator/__init__.py` `_fetch_and_process` ends its except branch with `error_code="unknown"` (not a member of `ERROR_CODES`), retryable, carrying the raw exception text; `heatmap.py` `heatmap_task` publishes `internal_error`. The docstrings of `errors.classify_exception_to_error_code`, `heatmap.heatmap_task` and `_report_album_failure`, and the archived closure of F-SWE-5, all say the two pipelines answer alike. The album behaviour predates PR #245; the docstrings were written by it. Owner decision: make the album fallback `internal_error` (which flips `retryable` to false and stops showing raw text to the user), or keep the split and reword the docstrings to say so. Either way a test is missing: the mutant `error_code = None` in that branch survives the full suite, so a test must assert the published code and the retryable flag for an unclassified exception in the album pipeline.

- [ ] **Status:** open (P2, owner decision). Source: third review of PR #245 (2026-09-29), S1-5.

### F-B23-23: the Last.fm privacy check caches verdicts it should not, and a private profile met inside a job is reported as an outage

`lastfm.check_profile_is_public` caches the private verdict for `REQUEST_CACHE_TIMEOUT` (3600s), so a user told to make the profile public and try again is refused from the cache for an hour. The mirror case: a cached public verdict lets a profile that has since gone private start a job, and the job fails as `lastfm_unavailable`, retryable, for the rest of the hour. `check_user_exists` caches any 200 body, so error 6 ("user not found") is cached as `exists=True`. Inside a job, `fetch_once`'s non-200 branch retries a 403 (Last.fm error 17) three times and reports "Last.fm unavailable, try again", and `ERROR_CODES` has no `private_profile` code. Invalid-key errors 10 and 26 may behave the same (unverified). The 403-in-job part is plausible rather than reproduced; the caching parts were reproduced. Fix shape: cache only a well-formed public answer, and add a `private_profile` code that a 403 or error 17 maps to without retry.

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), S1-6 and S1-16 (gap sweep), one finding.

### F-B23-24: a null Deezer track title raises TypeError outside the retry wrapper and fails the job, orphaning sibling requests

`scrobblescope/deezer.py` `fetch_deezer_album` normalises track titles after the retried request returns, so a null `title` raises `TypeError` outside `retry_with_semaphore`. In `orchestrator/_deezer_fallback.py` `_run_deezer_fallback_phase` the bare `as_completed` loop lets that exception end the phase and the job (`unknown`), and four sibling tasks are left running. The cancel-and-drain fix from this branch covers two of the five fan-outs, not this one, nor the search and details phases. Mechanism reproduced; no live trigger seen; identical on `main`. Fix: tolerate a null title inside the wrapper (skip the track) and give the remaining fan-outs the same cancel-and-drain. Do not adopt `asyncio.TaskGroup` for it before F-B23-16 lands: an `ExceptionGroup`'s text defeats the substring classifier.

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), S1-11.

### F-B23-25: the mobile heatmap strip is sized from a hidden container on first render and not re-laid-out on a rotation inside the mobile range

`static/js/heatmap.js` `renderHeatmapMobile` reads `gridContainer.clientWidth` while `#heatmap-result` is still `hidden`, so the width is 0 and the fallback `innerWidth - 48` guess is used: at 390px the strip draws 14 columns of about 19px scaled into a 277px box, and after any breakpoint round trip it draws 12 columns of 22px. The padding-aware sizing and its comment ("sized to what is left inside it") never run on first render. Separately `handleResize` re-renders only when `innerWidth` crosses 860px, so rotating 390 to 844 stretches the strip to about 50px cells, and opening at 844 then rotating to 390 gives 28 columns of 10px, under `MOBILE_MIN_CELL_SIZE` and any tap target. Reproduced in Chromium and Firefox. Fix: measure after the frame is visible (or from a laid-out ancestor minus the frame and grid padding), drop the guess, and re-render through `rerenderKeepingFocus` whenever the computed column count differs from the rendered one. It is a layout change, not a fix-wave one.

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), S2-9.

### F-B23-26: the artist spotlight can show another artist's photo and link under the Last.fm name

`scrobblescope/spotify.py` `_request_spotlight_artist` asks Spotify for `limit: 1` and returns `items[0]` with no name check, and neither `static/js/results-spotlight.js` `hydrateCandidate` nor `static/js/unmatched.js` `fetchArtistImage` compares `data.name` with the requested artist. A Last.fm artist Spotify does not know (a local band, a misspelling) gets the closest other artist: the card shows that photo with the alt text "Photograph of <Last.fm name>" and a link to the other artist's page. With the album-cover fallback gone, this is the only photo source, and the card treats the result as a confirmed photo. Reproduced with the API mocked to return a different name; how often it happens against the live API is unmeasured. Fix: the route returns the hit only when `normalize_name` of its name equals that of the requested artist, else null `image_url` and `spotify_url`.

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), S2-12.

### F-B23-27: a long artist credit paints over the plays and date columns on the Results page from 768px

`templates/results.html` `.album-info` is a flex item without `min-width: 0`, so its `truncate` artist span never shrinks: at 1024px an artist credit of about 65 characters runs from x 192 to 674 while its cell ends at 324, painting over the plays and release-date columns with no ellipsis. The same happens at 768, 1280 and 1920px, and on `main`. `static/css/results.css` fixes only widths below 768px, and `unmatched.css` already carries the `min-width: 0` rule for the unmatched table. Fix: `.results-table .album-info { min-width: 0 }` in `results.css` (Tailwind's `min-w-0` is dead under this theme, F-B21-52).

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), S2-13.

### F-B23-28: the unmatched threshold column clips "1234 plays" below 768px

`static/css/unmatched.css` sets the below-threshold column to 4.75rem in the `max-width: 767.98px` block, with `.unmatched-threshold { white-space: nowrap }` and `overflow: hidden` on `td`. From 320 to 767px "1234 plays" is cut by 8px ("1234 play") and "150 plays" loses about 1px of the "s"; from 768px the column is 104px and nothing clips. The CSS comment says the width "holds either", which is false. Reproduced in Chromium and Firefox; `main` clips the same. Fix: let `.unmatched-threshold` wrap (`white-space: normal; overflow-wrap: anywhere`) or widen the phone column to about 5.5rem, and add a four-digit case to the gate's seed.

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), S2-14.

### F-B23-29: small cleanups the third review of PR #245 found, none changing behaviour a user sees

One bundle, to be taken opportunistically:

- `utils.retry_with_semaphore` docstring: the sentence about the `Retry-After` cap sits inside the `jitter` entry; and jitter can push a capped sleep slightly past `MAX_RETRY_AFTER_SECONDS` (Task 3 review minors).
- `api_logging._record` takes an elapsed value the caller derives; deriving it inside would shrink the signature. `lastfm.fetch_pages_batch_async` has a gather path that no production caller reaches (one fan-out, one drain would do); `tests/test_routes.py` has duplicate helpers and row factories (Rule of Three: the helpers may wait, the dead path should go) (S1-15).
- `static/js/heatmap.js` labels the 15 day and month `<text>` nodes of the grid without `aria-hidden`, so the accessibility tree lists them as a loose text run before the 365 named cells (S2-18).
- `templates/results.html` `data-album-image` and `data-spotify-id` use `default('')`, which leaves "None" for a Deezer row; `default('', true)` covers it. Nothing reads them today (S2-20).
- The `.provider-badge` span is 10px uppercase in `input-mono`, under the 12px small-label floor and off the narrow face; one `.provider-badge` rule for all four copies of the badge markup would fix both (S2-21).
- Comments a cold reader cannot resolve: `results-spotlight.js` cites "B2", "B3" and "B3 follow-up"; `results.css` `.spotlight-details` cites "polish round 2"; `tests/frontend/conftest.py` says "see Step 1"; none of those labels exists in a tracked file. `.spotlight-image-box` calls the results thumbnail 4rem/4.5rem (it is 3rem/3.5rem), the threshold-column comment ("holds either") and `renderHeatmapMobile`'s "sized to what is left inside it" are false (see F-B23-28 and F-B23-25) (S2-22).
- S2-23 bundle: the `#heatmap-grid` ring-room CSS (a container that never scrolls at any width) and the padding subtraction in `renderHeatmapMobile`; the server-rendered spotlight card body and the `top_artist_*` route variables, dead because JS overwrites them; unused remnants in `results-spotlight.js` (a `content` id lookup, a `hidden`/`opacity-0` reset on an `<img>`, a once-read `state.reducedMotion`, `formatDurationMobile`) and an unread `event` parameter of `showTooltip`; the badge markup copied four times (Rule of Three: may wait); a `sr-only` re-implementation; the theme not following the system setting live. The five photo preloads are recorded on F-B23-20.

- [ ] **Status:** open (P3). Source: third review of PR #245 (2026-09-29), Task 3 review minors, S1-15, S2-18, S2-20, S2-21, S2-22, S2-23.

### F-B23-30: a Last.fm page whose `recenttracks.track` is a single object would be read as a list of dict keys

Last.fm is known to serve a single-item collection as a bare object rather than a one-element list in some of its JSON responses. `lastfm._is_well_formed_page` does not check `recenttracks.track`, and both aggregators, `heatmap._aggregate_daily_counts` and `orchestrator.fetch_top_albums_async`, iterate it as a list, so a one-track page would be read as a sequence of dict keys. Not confirmed against the live API (found while fixing the well-formed-page check, Task 2). Fix: normalise a lone object into a one-item list at the anti-corruption layer in `lastfm.py`, and check `track` in the predicate so a page with any other shape is refused and retried.

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), Task 2 implementer concern.

### F-B23-31: tests that stay green when the defect they exist for is planted back

Five tests were shown to survive the mutation they are meant to catch, each with the reviewer's proposed fix:

- Spotlight seed fallback (S1-7): restoring the deleted album-cover fallback in `spotlight.select_spotlight_artists` keeps the suite and the gate green. Add a route test that every spotlight seed `image_url` is empty.
- Span start (S1-8): the mutants `span_s = entry["span_end"]` and dropping the span-start update both survive `tests/services/test_api_logging.py`. Use a non-zero clock start, and record the later-starting call first.
- Cancel loop (S1-9): removing the cancel loop in `lastfm.fetch_all_recent_tracks_async` passes after 60s in `tests/services/test_lastfm_service.py` (`_PageFetchLedger`), and no per-test timeout exists. Count `CancelledError`, assert four, and wrap in `asyncio.timeout(2)`; the reviewer ran this: 2 passed in 0.13s at HEAD, 2 failed on the mutant.
- Fixture URL (S1-10): in `tests/test_provider_fixtures.py` the fixture's `external_urls.spotify` equals the code's fallback URL, so a typo in the key name passes. Give the fixture a distinct URL, and adopt `SPOTIFY_ALBUM_DETAILS_MOCK` for the two inline copies in `tests/test_orchestrator_process_albums.py` that escape the drift test.
- Frontend harness (S2-24): `tests/frontend/test_heatmap_pure_functions.py` asserts only `exportHeaderLayout(...).columns`, `exportHeaderModel().eyebrow` and `rocketColor` at exact stops; ten mutations survive (`Math.round` to `Math.floor`, `beside` forced false, the legend offset dropped, the headline dropped, and others). Assert whole layout objects for one beside and one stacked case, a `rocketColor` value between two stops, and the headline and legend.

- [ ] **Status:** open (P2). Source: third review of PR #245 (2026-09-29), S1-7, S1-8, S1-9, S1-10 and S2-24.

### F-B21-61: the architecture diagrams are claims about the code that nothing checks

`docs/architecture/` holds five mermaid diagrams, one each in
`docs/architecture/runtime-system.md`,
`docs/architecture/development-cycle.md`,
`docs/architecture/documentation-tooling.md`,
`docs/architecture/top-albums-sequence.md` and
`docs/architecture/heatmap-sequence.md`. Their nodes name real modules and
functions -- `orchestrator.py`, `create_job()`, `cleanup_expired_jobs()` -- so
each diagram states facts about the code. Nothing verifies them: no pre-commit
hook, no CI step, no test. Every symbol resolves today, verified 2026-09-13, so
this is drift prevention rather than a repair.

Every other repeated fact in this repository has a control plane: docsync
carries a generic mechanism plus `config/docsync.toml` declarations plus a gate, and
the worktree guard reads PLAYBOOK Section 3. A diagram node is the same kind of
claim as a `[[anchor]]`, and it is the only one with no owner.

Fix shape (owner ruling, 2026-09-13): extend docsync rather than add a tool.
- Mechanism: `scripts/docsync/diagrams.py` finds fenced mermaid blocks, reads
  their labels, and resolves any label naming a code symbol against the tree.
  It holds no repository-specific value, so it lifts with the rest of the
  package.
- Declarations: a `[[diagram]]` kind in `config/docsync.toml` naming each diagram's
  claimed symbols and the labels that are prose, not code ("Last.fm API"). The
  prose exemption is a local convention, like `strikethrough_exempt`.
- Gate: the existing `doc-state-sync-check` hook, reporting a new `DOC013`
  with a path, a line and a remedy. Record the code in
  `docs/architecture/documentation-tooling.md` beside `DOC001`-`DOC012`.
- Standard library only: `re` and `pathlib`. Mermaid syntax validation needs a
  parser, so if it is wanted, add it as a CI-only step using the Node
  toolchain the Tailwind build already requires, never as a pre-commit hook.
- `docs/agents/AGENT_NOTES.md` "This repository is also a template being
  extracted" gains a line naming diagrams as a third declared surface
  beside values and anchors.

Note (2026-09-19): DOC013 is taken (docsync finding-lifecycle codes).

Note (2026-09-24): DOC023 is also taken (docsync finding-lifecycle
grandfathered-finding count, `scripts/docsync/findings.py`). A new invariant
for this finding starts at the next free code named in
`docs/architecture/documentation-tooling.md`'s catalogue; DOC021 and DOC022
are reserved by
`docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`.

Status: open (P2). Not scheduled; it belongs with docsync work, not with
Batch 21. Source: architecture review, 2026-09-13.

### F-B21-54: PR 227 still reports test assertions through a separate scanner

The 2026-09-09 PR snapshot contains 268 inline Bandit B101-bearing comments
across seven pytest files. The published `.codacy.yml` excludes `tests/**`
from Codacy, but those B101 comments are from Qlty. The local
`.qlty/qlty.toml` is untracked and names test patterns without a targeted
B101 exclusion. Changing Codacy does not configure the other reviewer.

This is P2 review-tooling debt, not 268 production vulnerabilities. Keep
test assertions and preserve production analysis. A future tooling change
should scope only the noisy rule to test paths and validate the actual
review provider; do not hide whole production modules or suppress other
findings bundled in the same comment. The float and callback-comparison
claims were checked separately in
[PR 227 priority triage](docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md).

Status: open, deferred. No scanner configuration changed in this priority pass.
Source: PR #227 live comments and local scanner configuration, 2026-09-09.


### F-DATA-1: reissue editions collapse onto the original's cache row

`normalize_name()` strips `deluxe`/`edition`/`remastered`/`anniversary`
and seven more words from the album string, so
`"viagr aboys (Deluxe Edition)"` and `"viagr aboys"` both normalize to
`viagr aboys`. The `spotify_cache` primary key is
`artist_norm + album_norm`, so **both editions share one row** holding
whichever release populated it first, for the 30-day TTL. When the
reissue wins that race its `release_date` is served for the original.

Observed 2026-07-31: Viagra Boys "viagr aboys" (2025) appears under
`release_scope: same` for 2026, matching the JP deluxe released
2026-01-09, on an account that never played the deluxe.

The collapse is not a bug on its own -- it is what makes matching work
across Last.fm's inconsistent album strings, where the same record is
scrobbled as `Album`, `Album (Deluxe Edition)`, and `Album - Deluxe`
depending on the reporting client. Keying editions apart would fragment
one album into several leaderboard rows with split playcounts, which is
a worse defect than an occasional wrong year. Collapsing is correct for
*counting* and wrong for *dating*; the two need decoupling, not one
shared key.

Candidate fix (untested): keep the collapse for aggregation, but when
resolving `release_date`, select the **earliest** date among candidate
Spotify matches instead of whichever cached first. The original predates
its reissues by construction, and this approximates the "Original
Release Date" that Deezer's API team confirmed is a separate field from
the digital release date labels supply. No schema change required.

Rejected: a boolean `is_deluxe` discriminator. The stopword list has 11
entries that combine freely (deluxe, expanded, anniversary, JP deluxe),
so a boolean still collides variant-against-variant. Retaining the
stripped tokens as a variant tag would work but reintroduces the
fragmentation above.

Open questions, answerable by investigation rather than speculation:
1. Do the scrobbles themselves carry the deluxe title? Last.fm stores
   whatever album metadata the player reported, which is a second
   independent path to the same result.
2. Which other albums are affected? **Not answerable from the cache
   alone:** `(artist_norm, album_norm)` is the primary key
   (`init_db.py:42`) and the upsert overwrites the single stored
   `release_date`, so there are no sibling rows and no losing candidate
   dates to compare against. Detection requires re-running the Spotify
   search for each cached album and flagging rows whose stored date is
   later than the earliest candidate in the fresh result set, or
   cross-checking against an external original-release source
   (MusicBrainz, per the note below).
3. Can both a Latin-script deluxe and a JP deluxe surface at once? Only
   if the JP title carries Japanese characters -- NFKC preserves those,
   so it would not collapse; a Latin-script `(Deluxe Edition)` always
   merges to one row.

Note: Spotify exposes no original-release-date field. `release_date`
belongs to the matched release object, and `release_date_precision`
(`year`/`month`/`day`) only reports granularity. Disambiguation must
come from the search result set, the discarded `(Deluxe Edition)`
suffix, or `total_tracks`. MusicBrainz does carry original release
dates -- a lookup narrowed to that single field, cached, is far smaller
than the full-enrichment attempt abandoned in 2025.

Status: open (P2). Low user impact -- one recalled instance across ~14
years of scrobbles, and `release_scope: all` bypasses date filtering
entirely. Source: session 2026-07-31.

### F-DOCSYNC-2: STATUS block misreports current batch between batches

When a close-out entry (untagged `(Batch N close-out)` suffix) still sits
inside the CURRENT-BATCH markers, `renderer.py:85-86` falls back to
`last_completed + 1` even though the Section 3 parse correctly returns
the between-batches state. Transient: rotation self-corrects it when the
next batch's WP-0 entry lands. Fix candidates: prefer the between-batches
branch whenever the parse returns none, or make close-out tags parseable.
Status: open (P2). Source: PR #162 review round 4.

### F-DOCSYNC-3: close-out entries route to the monolith, not the batch log

Close-out headings use a `(Batch N close-out)` suffix that `ENTRY_BATCH_RE`
does not recognize as batch-tagged, so rotation routes them into the
untagged monolith archive instead of `docs/history/logs/BATCHN_LOG.md`.
Affects only close-outs written with that suffix: BATCH19_LOG.md and
BATCH20_LOG.md lack their close-out entries (both sit in the monolith),
while Batch 18's close-out was tagged `(Batch 18 WP-5)` and routed
correctly. Per-batch history is therefore incomplete for the affected
batches without a monolith grep. Fix belongs in a docsync
WP together with F-DOCSYNC-1/F-DOCSYNC-2 (make close-out tags parseable,
then one-time re-route of the existing close-out entries); hand-retagging
machine-rotated archive content was declined in PR #162 round 3 and again
in PR #163 round 3 on the same point-in-time principle.

**Another instance, found 2026-09-20.** Batch 22's Task 4 entry was headed
`(Batch 22 WP-1, Phase 2 begins)`. `ENTRY_BATCH_RE` requires the closing
parenthesis immediately after the work-package number, so the trailing
clause made the heading unparseable as batch-tagged and rotation sent the
entry to the monolith. Batch 22's own per-batch log will therefore be
missing its Task 4 entry unless the routing is corrected first. The entry
itself stays where the tool put it, per the declines above. What this adds
is that the defect is not limited to the `(Batch N close-out)` suffix: any
extra text inside the parentheses does it, and the tool reports nothing.
Status: open (P2). Source: PR #163 review round 3; second instance
2026-09-20.

### F-B21-57: `check_retired` uses one variable for the declaration index and the line number

`check_retired` (`scripts/docsync/declarations.py`) names the outer loop's
target `index` (`for index, declaration in enumerate(declarations)`), and its
inner scan rebinds the same name to a line number inside the scan (`for index, line in enumerate(lines,
start=1)`), so one name carries two meanings in one function.

Measured 2026-09-11: the reuse is latent, not live. `_validate("retired", index,
declaration)` at the top of the outer loop runs before the inner loop of its own iteration, and the
`for` statement reassigns `index` at the top of each outer iteration, so the
declaration index is restored before it is read again. Calling `check_retired`
with two declarations -- the first scanning `docs/agents/PLAYBOOK.md` behind an
`allow_after` marker, so its inner loop ran and rebound the name, and the second
carrying an unknown key -- named the fault `retired 1`, the declaration index
rather than a line. Nothing reads `index` after the inner loop's comparison.

It is filed anyway, because the message is correct only by statement order:
moving `_validate` below the scan, or reading `index` after it, turns a
declaration-shaped diagnostic into a line number, and a reader sent to the wrong
line of a long TOML file is the cost. Renaming the inner target to
`line_number` closes it.

Status: open (P2). No behaviour change; the current message is correct.
Source: Task 7 fix round 1, 2026-09-11, from that task's implementer report.

### F-MAS-5: in-memory JOBS dict limits horizontal scaling

Process-local dict breaks polling under multiple workers/machines;
migration path is Redis or a Postgres-backed job table.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-MAS-6: Celery/Redis RQ for task queue

**Owner decision:** out of scope until features complete.
Status: open (P2, owner-gated). Source: MULTI_AGENT_SWEEP.

### F-MAS-7: process-local Spotify token cache

Redundant refreshes under multiple workers; acceptable at current scale.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-MAS-8: REQUEST_CACHE growth with always-on machines

Cleanup is opportunistic (at job start); TTL mitigates, does not cap.
Status: open (P2). Source: MULTI_AGENT_SWEEP.

### F-SWE-3: a Spotify server error bypasses the configured retries

`search_for_spotify_album_id` (`spotify.py`, its inner `search_once`) returns
`(None, None, True)` for every non-200, non-429
response, and `is_done=lambda t: t[2]` treats that `True` as terminal. A 500
or 503 therefore ends the attempt loop after one try, while
`SPOTIFY_SEARCH_RETRIES` is set to 3 -- verified by running it. The retries
only ever fire for 429. `fetch_spotify_album_details_batch` has the same
shape in the `fetch_once` inside it.

The consequence is narrow: an album that _is_ on Spotify can be recorded as
unmatched when a second attempt would have found it.

**Rescoped by the owner, 2026-08-20, and the correction is worth keeping.**
The audit first filed this as a user-facing mislabelling -- `search_once`'s final branch
returns the same value for a genuine empty result, so
`_run_spotify_search_phase` (`orchestrator.py` at the time, now
`scrobblescope/orchestrator/_search.py`) records the album with the reason
`No Spotify match`, and the report treated that label as wrong. It is not.
Thousands of Last.fm-scrobbled albums genuinely have no Spotify release, so
the label is accurate for the ordinary case and what the user sees is
correct. What survives is the defect above -- configured retries that never
run -- which is a smaller thing than the audit claimed. Severity drops from
P1 to P2 and the finding moved from the P1 section to this one.

The related UI need -- the unmatched modal and page should say plainly that
an album had no Spotify match -- is already Batch 21 WP-7 scope
(the `WP-7 -- Unmatched page + reason_code` section of
`docs/history/definitions/BATCH21_DEFINITION.md`: the `no_spotify_match` reason code and the reason
panels with human copy). It is not extra work and is not tracked here.
Status: open (P2). Source: SWE_PRINCIPLES_AUDIT, rescoped by owner review.

### F-SWE-7: utils.py holds five unrelated concerns

One module (346 lines when filed; 423 on 2026-09-29) carries API rate
limiting (`_GlobalThrottle` and the `get_*_limiter` functions), aiohttp
session construction (`create_optimized_session`), an in-memory response
cache (`get_cached_response`, `set_cached_response`,
`cleanup_expired_cache`), duration formatting for display (`format_seconds`,
`format_seconds_mobile`) and a generic async retry loop
(`retry_with_semaphore`). Nothing binds them together except the file
name, and `utils` is the name that accretes.

Each function is individually clean, which is why SRP grades B while SoC
grades C. The cost is discoverability: the response cache that F-MAS-8
tracks lives in the same file as `format_seconds`, and a reader looking for
either has no reason to look here.

A split into rate limiting, HTTP and caching, and formatting is a sibling
of the F-B20-2 orchestrator decomposition, archived on 2026-09-21. It is a
structural change with its own parity-test cost, so it wants a work
package of its own rather than a side task.
Status: open (P2). Source: SWE_PRINCIPLES_AUDIT.

### F-B21-48: Last.fm history is re-fetched because only page responses are cached

Every album and Heatmap job calls `user.getrecenttracks` for its requested
range. `scrobblescope.utils.REQUEST_CACHE` retains an exact URL-and-parameter
page response for one hour, in process memory only. A restart clears it, and
different `from`/`to` ranges cannot reuse their overlapping listening history.
PostgreSQL stores Spotify album metadata but no Last.fm scrobble events.

A persistent cache should store normalized scrobble events by user and played
timestamp, with explicit coverage ranges and a short refresh window for recent
history. That model lets album-year and rolling Heatmap requests reuse overlap
without treating Last.fm page numbers as stable storage. Its definition must
also set retention and invalidation behavior for edited or deleted scrobbles.
Keep this out of F-B21-47: it changes shared pipeline data and needs its own
schema, completeness rules, and parity tests.

- [ ] **Status:** open (P2), re-graded 2026-09-23 by owner ruling: a persistent scrobble cache is a feature, not a defect

Source: owner pipeline-performance observation and source cache audit,
2026-09-06.

### F-B18-11: heatmap Last.fm page fetch is rate-limit bound

Fetch time is bound by page count and the shared 10 req/s throttle
(2026-05-16: 103 pages, 10.9s vs a 10.3s floor; fetching is already
concurrent at `limit=200`). Options: heatmap-specific caching,
progressive rendering, or a higher rate limit (not recommended).

- [ ] **Status:** open (P2), re-graded 2026-09-23 by owner ruling: a persistent scrobble cache is a feature, not a defect; its only unrejected remedy is F-B21-48

Source: Batch 18 audit + perf session 2026-05-16.

### F-B21-63: Codex and Copilot have no equivalent of the session-start hook

`AGENTS.md`'s "Session Bootstrap" is enforced for Claude Code sessions by a
`SessionStart` hook that injects branch, working-tree state, guard codes and
the machine-managed status block into every new session. Codex and Copilot
have no comparable entry point: for them, the top of `AGENTS.md` is the only
forcing function there is, and a session that does not open the file never
learns the rule that says to open it.

- [ ] **Status:** open (P2)

Source: F-B21-25, re-graded by owner ruling 2026-09-23.

---

## Info -- Design decisions (no action needed)

### F-LOAD-3: in-memory REQUEST_CACHE is intentional

Avoids re-fetching Last.fm on re-searches; clears on machine sleep.
Status: standing design decision. Source: load testing 2026-03-04.

### F-LOAD-4: Spotify cache TTL is ToS-compliant

Hits do NOT refresh `updated_at`; 30-day expiry from last API call.
Status: standing design decision. Source: cache verification 2026-03-04.

### F-LOAD-5: pre-slicing reduces Spotify API load

Playcount filter + 500-album playtime cap applied before cache lookup.
Status: standing design decision. Source: load testing 2026-03-04.

### F-DOCSYNC-14: DOC023 fires on prose that quotes the outcome vocabulary

`_claims_a_terminal_outcome` (`scripts/docsync/findings.py`) suppresses a
claim when a `not` directly qualifies the outcome word, including the
tab-separated and uppercase spellings and the Markdown-emphasised form. Two
classes of prose therefore still block, and both are deliberate.

First, a `not` earlier in the sentence does not suppress a later claim. The
negation rule is anchored to the outcome word, so prose that says it does not
know something and then states an outcome still reads as a claim. That is
asserted by `test_negation_does_not_reach_across_a_sentence`.

Second, a compound that takes the vocabulary's `no` branch and appends a
trailing qualifier carries no `not` for the rule to find, so it blocks as
well.

There is a practical consequence worth recording, because it was learned the
hard way: this file cannot quote a sentence that trips the gate. The first two
drafts of this very entry quoted the trigger sentences in order to explain
them, and DOC023 blocked both -- the first on a `no`-branch compound, the
second on the sentence the boundary rule above describes. The quoted sentences
and the 14-case measurement live in
`docs/history/reports/ADVISORY_VERIFICATION_2026-09-20.md`, which sits
outside DOC023's scan. This file does not, so it describes the shapes instead
of spelling them.

Measured 2026-09-20 against 14 synthetic findings run through the real gate,
`collect_rot_issues` (probe: `tmp/_zG_doc023_verdict.py`). Every negation
spelling the rule was written for is handled, and the boundary case above
still blocks, as documented. `tests/test_docsync_findings.py` already covers
the intended behaviour --
`test_a_finding_saying_it_is_not_resolved_is_not_a_claim`,
`test_negation_does_not_reach_across_a_sentence`,
`test_a_deployed_resolution_still_reads_as_a_claim`.

Recorded so a later agent does not "fix" either boundary by widening the
negation window. That trade buys silence on a couple of phrases and pays for
it by missing real completion claims, which is the failure DOC023 exists to
prevent. Blocking is the safe direction -- Rule 7's "a wrong green is worse
than a red" -- and the cost is one reword by an author whose open finding
happens to use the phrase.

Status: standing design decision. Source: PR #234 advisory verification,
2026-09-20.

---

## Deferred / future-batch candidates (Batch 18/19 audits)

One-line cross-references; detailed bodies live in pre-Batch-20
`docs/agents/FINDINGS.md` (git history before `494f2c7`) or the `docs/history/`
audits; 2026-03-04 load-test data is in the findings archive.

- F-B18-1: orchestrator monolith -- promoted to F-B20-2, resolved 2026-09-21.
- F-B18-2: JOBS dict lacks TypedDict/dataclass annotations.
- F-B18-3: `loading.js` album messaging; extract shared polling utility
  if a third feature emerges.
- F-B18-4: `_check_user_exists` creates a throwaway event loop per call.
- F-B18-5: inline SVG payload growth; lazy-load or sprite if more added.
- F-B18-7: duplicated win32 event-loop guard -- absorbed into F-B20-2,
  resolved 2026-09-21 as `worker.new_thread_event_loop`.
- F-B18-10: heatmap + album jobs share the 10 req/s throttle (by design).
- F-B18-12: mode pills differ in width (no `min-width` on `.mode-pill`)
  -- RESOLVED 2026-08-25 by Batch 21 WP-3. They are equal-width `<button>`
  elements in a two-column grid, which also closes the `span[role="button"]`
  item in F-B21-5.
- F-B19-3: last.timer aggregate endpoints are not a drop-in heatmap
  speedup; future perf experiments listed in the archive.
- F-B19-4: front-end UI audit notes -- basis of `docs/history/definitions/BATCH21_DEFINITION.md`.
- F-MAS-2: no automated JS tests -- absorbed into F-B21-18.

---

## Feature preparation notes

### F-FEATURE-1: top songs feature

Rank most-played tracks for a year (separate task type + loading/results
flow). Status: deferred; on the README roadmap. Source: owner roadmap.

- F-FEATURE-2: listening heatmap -- shipped in Batches 18/19, archived;
  perf follow-ups continue as F-B18-11.

---

## Source documents

- `docs/history/reports/DOCSYNC_AUDIT_2026-02-25.md` -- 11 findings, detailed code refs
- `docs/history/reports/AUDIT_2026-02-27_MULTI_AGENT_SWEEP.md` -- Full architecture sweep
- `docs/history/reports/AUDIT_2026-02-11_IMPLEMENTATION_REPORT.md` -- Earlier audit
- `docs/history/reports/AUDIT_2026-01-10.md` -- Rate limit regression audit
- `docs/history/findings/FINDINGS_ARCHIVE.md` -- Rotated resolved/no-action items
- Agent memory: load-test-findings.md (not a repository file) -- raw load
  test data and analysis
