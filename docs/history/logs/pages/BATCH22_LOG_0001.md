<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# BATCH22_LOG -- page 0001

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
