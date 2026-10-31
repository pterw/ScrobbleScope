<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0017

### 2026-09-19 - Docsync close-out plan Tasks 3 and 4, and a control-plane code review

Side task, no batch tag: continuation of the entries below on
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`, executed
via `superpowers:subagent-driven-development`. Not Batch 22 scope. Nothing
is committed; the whole plan remains working-tree-only by owner constraint,
and the unrelated in-flight Batch 22 edits in this worktree were neither
staged nor reverted.

Task 3 (CLI integration and multi-signal close-out) landed in six slices:
the two strict configuration tables, the definition-side close-out record,
the gate wiring, `--close-batch`, the archive maintenance modes, and DOC020.
Its review found one Important defect -- the `expected` map passed to
`transaction.publish` did not cover every path the plan had READ, so a
concurrent edit by another agent could publish a decision made about
different content. Fix round 1 made `_Corpus.read_paths()` the single source
of truth for that, so a document added to the corpus later inherits the
protection instead of needing a second hand-maintained list.

Task 4 was split into a code half and a documentation half. The code half
added `scripts/dev/docsync_preflight.py` and
`scripts/dev/install_docsync_hook.py`, moved the docsync hook to first
position in `.pre-commit-config.yaml`, and added an explicit CI preflight
step. Its review found that the control-plane refusal existed only in
`--staged` while the pre-commit entry runs `--worktree`, which is the path
that actually executes on every local commit; fix round 1 closed that.
The documentation half brought `AGENTS.md` from 728 to 498 lines by
compressing, relocating the DOC catalogue to
`docs/architecture/documentation-tooling.md` and the bootstrap edge cases to
`HANDOFF_PROMPT.md`, and relocating the `UI and Accessibility Rules` that an
in-flight Batch 22 edit had deleted into `docs/agents/ui-accessibility.md`.
That single deletion was the root cause of all three live gate errors, which
are now repaired.

Owner rulings taken during the session, both recorded in the plan ledger: the
commit preflight refuses any commit that modifies the docsync control plane,
and the one named escape is `SKIP=doc-state-sync-check git commit` rather
than `--no-verify`, so the absolute prohibition on `--no-verify` in
`AGENTS.md` anti-pattern 7 stands unchanged; and the architectural invariants
the owner supplied are now a binding document at
`docs/agents/global-rules.md`, carrying an explicit precedence order for when
two rules conflict.

An owner-requested code review of the control plane followed, and its
findings were fixed rather than filed. `--split-archive` had been writing
directly to disk with no lock, no journal and no staleness check, which
contradicted the atomicity guarantee every other writing mode honours; it now
publishes through the same transaction. The batch-definition regex that had
been constructed five times across three modules is now
`parser.root_definition_pattern`. The live-document path list, which the tool
had duplicated between `cli.py` and `integrity.py` without the declaration it
would demand of any other repository, now has one owner. On the application
side, `update_job_result` no longer normalizes every result inside the
process-global lock -- the key is attached once where results are built --
and `run_release_checks` was decomposed into three named units with its
existing tests passing unmodified as parity evidence.

Validation, run fresh in the controller session rather than taken from any
subagent's report: the two preflight and hook suites were 76 passing, the
release-check suite 23 passing unmodified before and after its refactor, and
`ruff check` plus `ruff format --check` were clean across the touched files.
`scripts/doc_state_sync.py --check` now exits 0, leaving only the expected
root `BATCH22_DEFINITION.md` warning. Validation: `pytest -q` -- **1470 passed**.

Deviations worth the next reader's attention. `AGENTS.md` landed at 498 lines
rather than the ~420 target: every remaining line is a distinct rule or
procedure, and further cuts would have removed prohibitions rather than
narrative. Two documents under `docs/agents/` were staged, against the
plan's own no-staging rule and at the owner's explicit instruction, because
DOC001 reads `git ls-files` and an untracked file can never satisfy a
reference to it.

Forward guidance, in the owner's stated order: build the DOC023 invariant
that stops resolved findings rotting in free prose, then run the final
whole-branch review, then land the work as a sequence of atomic commits
rather than one large one. The triage list for that review is every finding
marked deferred in
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`, which
remains the authoritative ledger for this plan.

### 2026-09-16 - Docsync close-out plan Task 2 closed out

Side task, no batch tag: continuation of the 2026-09-15 entry below on
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`, executed
via `superpowers:subagent-driven-development`. Not Batch 22 scope; nothing
here touches live `FINDINGS.md`, the archive files, or the docsync CLI.

Task 2's fix round 1 (resumed 2026-09-15 with a fresh implementer, since
the original handle was unavailable) addressed all 3 Important findings
recorded in `docs/history/reports/DOCSYNC_CLOSEOUT_TASK2_REVIEW_2026-09-15.md`:
a missing index no longer deletes existing pages (`_load` now rejects
orphans before returning an empty layout); a page's silently-discarded
prologue/missing header now raises `SyncError` instead of being dropped;
`page_path` now resolves beside `index_path` instead of always under the
store root. Each fix is covered by a regression test whose own docstring
names the finding it reproduces.

This session had no subagent-dispatch tool available, so the required
scoped re-review was performed by the controller directly instead of a
dispatched reviewer -- a disclosed deviation from
`superpowers:subagent-driven-development`, consistent with how Task 1's
own fix round 1 was handled for the same reason. The re-review checked
each fix against the review report's findings and the design spec's own
language (not just that tests pass), and swept for the same defect class
elsewhere in the module (`_diff`, the other `_reject_orphans` call site)
before concluding no sibling instance existed. Full re-review detail is in
`.superpowers/sdd/2026-09-15-docsync-closeout-archives/progress.md`.

Validation, run fresh: the archive suite alone was 43 passing, and the
full docsync suite (markdown/declarations/integrity/logic/parser/findings/
archives/transaction) was 355 passing; `ruff check` on all Task 1/2-owned
files was clean. Validation: `pytest -q` -- **1302 passed** (up from 1298;
the delta is this shared worktree's own concurrent, uncommitted growth in
`archives.py`/`test_docsync_archives.py`, not a regression -- see the
out-of-band fix entries above for the same observation applied to
`logic.py`).

Task 2 is complete: 3/3 Important findings addressed, 0 new
Critical/Important breakage. 7 Minor findings (recorded in the review
report) remain deferred, unchanged, to the final whole-branch review's
triage. Next step: Task 3 (CLI integration and multi-signal close-out).

### 2026-09-15 - Docsync close-out plan Task 2 review recorded

Side task, no batch tag: control-plane work on
`docs/superpowers/plans/2026-09-15-docsync-closeout-archives.md`, executed
via `superpowers:subagent-driven-development`. Not Batch 22 scope; nothing
here touches live `FINDINGS.md`, the archive files, or the docsync CLI.

Task 1 (shared Markdown scanner, DOC010-DOC012 repairs) is complete and
reviewed clean. Task 2 (finding lifecycle + bounded archives + recoverable
publish: `findings.py`, `archives.py`, `transaction.py`, DOC013-DOC018) is
implemented and controller-verified green (93/93 new suites, 351/351 full
docsync suite, Ruff clean), but its task review returned Needs fixes: 3
Important findings, all in `archives.py`, all silent history-loss/
misplacement paths with no diagnostic (a missing index deletes every
managed page; page prologue content is silently discarded; `page_path`
writes to the wrong directory when an index does not sit at the store
root). Plus 7 Minor findings, logged for the final whole-branch review.
Full detail: `docs/history/reports/DOCSYNC_CLOSEOUT_TASK2_REVIEW_2026-09-15.md`.

Validation: `pytest -q` -- **1298 passed** (unchanged; this side task adds
one documentation file and a PLAYBOOK entry only, no application or docsync
source). Tasks 3-4 of the plan are not started. Next step: resume the SDD
fix loop on Task 2's three Important findings.

### 2026-09-14 - Mutation testing scoped to hermetic modules

Side task, no batch tag: owner-directed tooling, outside Batch 22's scope and
its definition.

Scope: `scripts/dev/mutation_scope.toml` (new),
`scripts/dev/mutation_test.py` (new),
`tests/scripts/dev/test_mutation_test.py` (new), `AGENTS.md`. Motivation was
`cosmic-ray==8.7.0` sitting in `requirements-dev.txt` with no caller; the
decision was to give it a defined home rather than delete it, because a
47-mutant module costs minutes here and the repo already mutation-tests by hand
(the Batch 21 plans call it "mutests").

Implementation:
- `mutation_scope.toml` is the allowlist of modules cleared for mutation
  testing, each with the tests that cover it: `domain.py`, `enrichment.py`,
  `unmatched.py`, `worker.py`, `spotlight.py`, `orchestrator/_results.py`,
  `scripts/dev/graphify_refresh.py`. The file carries its exclusion list and
  the reason per entry, so a gap is not read as an oversight: `utils.py` and
  `repositories.py` are time- and loop-dependent, and the network and DB
  modules are not hermetic at all.
- `mutation_test.py` drives cosmic-ray for one allowlisted module and refuses
  every other path by exact normalized comparison. It builds the cosmic-ray
  config in a temporary directory, runs init/baseline/exec, and reports caught,
  survivors and unknown. Two guards protect the checkout: it refuses to start
  while the module has uncommitted changes unless `--allow-dirty`, and it
  compares the module's SHA-256 before and after so a mutant left on disk is an
  error, not a clean verdict.
- `AGENTS.md` gains a "Mutation testing (on demand, never a gate)" subsection
  under Test Quality Rules: the allowlist rule, the pre-refactor trigger, the
  survivor-is-not-a-defect warning, and that no hook and no workflow calls it.

Deviations and repairs found on the way:
- `doc_state_sync.py --check` was already failing on four integrity errors
  before this task, all fallout from the removal of the "UI and Accessibility
  Rules" section from `AGENTS.md`: DOC009 for the declared 44px touch minimum,
  and DOC010 twice for citations of a heading that no longer existed. The
  section is restored in condensed form, with items 1 and 2 keeping the numbers
  two other documents cite. That removal was mid-edit, not part of this task;
  the repair is recorded here because it shares the commit.
- `AGENT_NOTES.md` was also failing DOC009 on its declared heatmap-window site,
  and had trailing whitespace at what was line 314. Both repaired.
- `requirements-dev.txt`'s `cosmic-ray==8.7.0` line was uncommitted and
  unreferenced; this entry is the first record of an owner decision to keep it.

Validation: `pytest -q` -- **1153 passed**, up from 1108 with the 45 new tests.
`ruff check` and `ruff format --check` clean on both new files.
`doc_state_sync.py --check` passed with only the expected root-BATCH warning.
`mutation_test.py --list` prints the seven scoped modules, and `--init-only` on
`scrobblescope/unmatched.py` reports 47 mutants in about a second.

Forward guidance: the post-`exec` outcome mapping in `classify()` was written
against cosmic-ray 8.7.0's session schema. Which modules qualify, the refusals,
and the config shape are all covered by tests, but the mapping from a completed
session record to killed/survived is not yet exercised end to end, so a first
full run should be checked with `--raw` before its numbers are quoted. An
unrecognised record is reported as unknown rather than guessed, which is what
makes that check cheap.

### 2026-09-14 - DB connect timeout (found while localhost-testing the Deezer fallback)

Scope: `scrobblescope/cache.py`, `tests/test_repositories.py`. Owner-found
during manual localhost verification of Task 5's Spotify-fails-to-Deezer
fallback (an invalid `SPOTIFY_CLIENT_ID`, per the plan's own verification
step 2): the browser sat at "Preparing 129 albums for Spotify lookup..."
for three minutes with no server-log output at all, for two different
Last.fm usernames. The owner had *paused* (not stopped) the local
`ss-postgres` Docker container, which answers no SYN-ACK at all rather than
refusing the connection -- unlike the ordinary "DB is down" case the
existing retry/backoff (2026-02-14, `DB_CONNECT_MAX_ATTEMPTS`,
`DB_CONNECT_BASE_DELAY_SECONDS`) was built to smooth over.
`_get_db_connection` is the first thing `process_albums` does, before any
further progress update, so the whole stall was silent and looked
identical to a hang. Root cause: `asyncpg.connect(dsn)` carried no
explicit `timeout`, so each of the 3 default attempts ran out asyncpg's own
60s default -- 3 x 60s = 180s, matching the observed 3 minutes exactly.

Fix: a new `DB_CONNECT_TIMEOUT_SECONDS` env knob (default 5), passed as
`asyncpg.connect(dsn, timeout=connect_timeout_seconds)`, following the same
env-tunable pattern as the two existing retry knobs. Worst case with
defaults is now ~3 x 5s plus the existing sub-second backoff, not 180s. Not
part of any Batch 22 WP-1 task's file list (Task 7 already landed and
committed separately as `8eb3c2a`); a small, unrelated robustness fix,
logged here per Side-Task Handling rather than folded into a task entry.

`tests/test_repositories.py`: `asyncpg.connect` is asserted to receive the
configured `timeout=` kwarg, and a `TimeoutError` from `asyncpg.connect` is
asserted to be treated as an ordinary connect failure (retried, then
`None` with a `db-down` log line) rather than needing special handling.

Validation: `pytest -q` -- **1081 passed** (was 1079; +2 new). Not yet
verified live against a paused container (that reproduction is the owner's
local setup); the two new tests cover the mechanism directly.

`doc_state_sync.py --check` initially failed DOC006/DOC008 after this
entry rotated to the top of the log: `.claude/SESSION_CONTEXT.md`'s
Section 1 dashboard row and Section 6 heading, and `FINDINGS.md`'s header
line, all carried a hand-written "1036" test count untouched since
2026-09-11 -- separate from the `DOCSYNC:STATUS` managed block, which
`--fix` had correctly kept current all along. Corrected both to **1081**
and the module count to the re-measured **48** (was 43); `--check` passes
clean. Left as found and not swept here (a bigger doc pass, out of this
side-task's scope): `FINDINGS.md`'s own "Batch 21 is active" status line,
stale since the same 2026-09-11 date -- Batch 21 closed and Batch 22 is
now active per PLAYBOOK Section 3.

**Addendum, same day:** the underlying gap is recorded as **F-DOCSYNC-12**
-- `--fix` only ever rewrites the STATUS block's own count line, never the
other two fields DOC006 checks (the Section 1 row, the Section 6 heading)
or the FINDINGS header DOC008 checks, so all three can drift indefinitely
until something trips the check and a human corrects them by hand, as
happened here.

### 2026-09-13 - Deezer client (Batch 22 WP-1, Phase 2 begins)

Scope: `docs/superpowers/plans/2026-09-13-batch22-enrichment-providers.md`
Phase 2 Task 4. No behaviour change -- `scrobblescope/deezer.py` is new and
unused by any caller; Task 5 wires it in as the Spotify-miss fallback.

Plan vs implementation: matched. `search_deezer_album(session, artist,
album)` queries the plain `f"{artist} {album}"` (the filtered
`artist:"..." album:"..."` form favors tribute/cover results per the
plan's probe) and accepts a candidate only when
`normalize_name(candidate_artist, candidate_title)` equals the key built
from the caller's own `artist`/`album` -- never "the first result" as a
guess. `fetch_deezer_album(session, album_id)` calls `/album/{id}` for
metadata and `/album/{id}/tracks?limit=500` for every track's duration,
since `/album/{id}` alone caps at 25 tracks regardless of `nb_tracks`
(pinned with a 30-track fixture). Both share `_fetch_deezer_json`, which
treats Deezer's HTTP-200-with-body errors correctly: code 800 ("no data")
is a terminal miss: `None`; code 4 (quota) retries after a 1s wait via
`retry_with_semaphore`'s existing retry-after path, the same mechanism
Spotify's 429 handling already uses.

`scrobblescope/utils.py` adds `get_deezer_limiter()` (10 req/s, the
existing `_GlobalThrottle` + per-loop `AsyncLimiter` pattern, mirroring
`get_spotify_limiter`); `scrobblescope/config.py` adds
`DEEZER_REQUESTS_PER_SECOND` (default 10 -- Deezer's stated 50 req/5s),
`DEEZER_SEARCH_RETRIES`, `DEEZER_DETAIL_RETRIES` (default 3, matching
Spotify's retry defaults).

Validation: `pytest -q` from the worktree cwd -- **1061 passed** (1054 + 7
new in `tests/services/test_deezer_service.py`: candidate-matching,
no-match, the two HTTP-200-error-code cases, the 25-vs-30-track pagination
case, and two adversarial "the second request never succeeds" cases for
`fetch_deezer_album`, added beyond the plan's own four because a helper
this new needs at least one failure-path test per AGENTS.md's Test
Quality Rules. Task 5 (wire the fallback into the orchestrator) is next.

### 2026-09-13 - PR #232 merged to `test`; branch reset, SHAs remapped

Owner rebase-merged PR #232 into `test` (mergeCommit `812cdde`). GitHub
rebased rather than merge-committed, so every commit on the PR got a new
SHA: `e8de45c`->`d29cc5e`, `85d458f`->`a124b52`, `c5c52fb`->`735c05d`,
`594c705`->`87f3822`, `05a0ff5`->`812cdde`. **Every one of those five old
hashes is quoted earlier in this file, in FINDINGS.md, and in the Claude
project memory for this repo; none of them resolve on this branch
anymore.** Content is unchanged -- `git show <new-sha>` reproduces the
same diff as the corresponding old one -- only the identifier changed.

`feat/batch22-enrichment` (worktree and `origin`) was hard-reset to
`origin/test`'s tip and force-pushed to drop the now-orphaned pre-rebase
commits, per owner direction (reset in place, not a fresh branch --
`AskUserQuestion`, 2026-09-13). PLAYBOOK Section 3's branch name is
unchanged; WP-1 continues on `feat/batch22-enrichment`. Verified after
reset: `pytest -q` -- **1036 passed**; worktree-alignment guard passed (0
behind, 21 ahead of `origin/main`).

A second Graphify review landed on `05a0ff5` (2026-09-14 01:29 UTC, before
the merge) claiming 5 endpoints were "removed" from `scrobblescope/routes.py`
-- a stale-baseline false positive (its own index was "15 commit(s) behind
this PR's base"): the file no longer exists post-WP-0, and all five
endpoints are present, unmoved in content, in `routes/api.py` and
`routes/heatmap_flow.py`. No action taken; not filed as a finding since
it is a bot-indexing artifact, not a repo issue.

### 2026-09-13 - PR #232 bot review triage (Codacy + Graphify)

Triaged both bot reviews on PR #232 (WP-0 + F-B22-1 + AGENTS.md cleanup)
per `/pr-bot-triage`. Codacy (2026-09-13 21:49 UTC, 3 alerts) and Graphify
(2026-09-14 01:08 UTC, 5 inline coupling-delta comments + 5 "worth a look"
escalate findings from the check run) both reviewed the same branch tip.

Acted: `scrobblescope/lastfm.py:68`'s unreachable `return` after
`resp.raise_for_status()` deleted (Codacy, confirmed real -- the call
always raises for any status reaching that branch, so the line never ran).

Deferred, filed as findings: the three `assert job_context is not None`
sites in `album_flow.py` moved verbatim from pre-split `routes.py`
(F-B22-2 -- real hardening gap, `python -O` strips asserts, but out of
WP-0's behaviour-neutral scope); the job-ID-as-bearer-token design across
`/progress`, `/api/unmatched`, and `/heatmap_data` (F-B22-3 -- owner
judgment call, not a demonstrated bug).

Declined, false positives (verified against source, not fixed): Codacy's
XSS claim on `_get_filter_description`'s f-string returns (no `|safe` in
`results.html`/`unmatched.html`; Jinja2 autoescapes regardless of how the
Python string was built). Graphify's two "job slot leak on failed thread
startup" escalate findings (`worker.py`'s `start_job_thread` already calls
`release_job_slot()` in its own `except` before re-raising -- confirmed by
reading `worker.py:31-42`). Graphify's "`check_user_exists` now raises
instead of returning a fallback" escalate finding (that is the PR's own
intentional F-B22-1 fix, not a new regression). Graphify's five inline
"health regression" coupling-delta comments (expected structural churn
from WP-0's module split; the tool's own gate marked the run PASS with no
blocking health regressions).

Verification: `pytest -q` -- **1036 passed**; `doc_state_sync.py --check` and
`pre-commit run` both pass.

### 2026-09-13 - Fixed a broken batch-reference edit; graphify agent sections

Two unrelated uncommitted changes found sitting in the worktree during a
pre-clear sweep, neither written by this session:

1. **`docs/agents/domain.md` had a broken edit**, from an unknown earlier
   process: `BATCH21_DEFINITION.md` had been changed to `BATCH2_DEFINITION.md`
   -- a dropped digit, not a real batch. Fixed to `BATCHN_DEFINITION.md`
   (the file named in PLAYBOOK Section 3), matching the same generalization
   already applied to `docs/architecture/documentation-tooling.md` and
   `docs/ARCHITECTURE.md` earlier today, so it cannot go stale the same way
   again.
2. **Graphify's own tooling had added a `## graphify` section to `AGENTS.md`
   and `.github/copilot-instructions.md`**, matching one already present
   (and already noted, this session) in the gitignored `CLAUDE.md`. Kept:
   the content is operational and non-duplicative with anything already in
   `AGENTS.md`, and reaching every agent's own instructions file (Claude,
   Copilot, and via `AGENTS.md`, everyone else) is exactly the "reach every
   agent" pattern this session's earlier `AGENTS.md` edits argued for. Not
   independently trimmed -- reads as graphify's own multi-agent install
   pattern, not this session's prose.

Validation: `pytest -q` -- **1036 passed** (unchanged).
`python scripts/doc_state_sync.py --check` passes.

### 2026-09-13 - AGENTS.md trimmed, three stale architecture diagrams fixed

Side-task, owner direction after reviewing WP-0. Two parts:

1. **AGENTS.md trimmed.** The Anti-Pattern Registry (items 1-14) carried
   multi-paragraph rationale and worked-incident narratives per item; cut to
   the actionable rule plus its "how to apply" technique where one existed
   (items 11-14 kept their sub-bullets; anecdotal colour and specific past
   numbers were cut). Added item 15, the diagram-trust rule (see below), so
   it reaches every agent working this repo, not only Claude Code sessions
   with the `scrobblescope-bootstrap` skill installed -- this repo is
   multi-agent orchestrated (Codex, Copilot, and as of today DeepSeek).
   Added `docs/architecture/documentation-tooling.md` to the Document Roles
   table as an on-demand "control plane" reference (docsync, worktree
   guard, pre-commit, CI), explicitly kept out of the mandatory bootstrap
   set per the existing token-discipline principle -- it is useful when a
   gate fails unexplainably or before touching that tooling's own source,
   not for ordinary batch work.
2. **Fixed the three architecture diagrams WP-0 left stale**
   (`docs/architecture/runtime-system.md`, `top-albums-sequence.md`,
   `heatmap-sequence.md`), plus `documentation-tooling.md`'s own stale
   `BATCH21_DEFINITION.md` reference (generalized to `BATCHN_DEFINITION.md`
   so it does not go stale again next batch) and `docs/ARCHITECTURE.md`'s
   verification date and batch-scope citation. Fixed by priority: the
   full-stack runtime diagram first (broadest orientation value), then the
   control-plane diagram (has real drift, is itself the doc AGENTS.md now
   points agents at), then the two pipeline sequence diagrams (narrower
   scope, `orchestrator.py`/`routes.py` participant labels only -- the
   sequence of calls itself did not change, since WP-0 was behaviour-neutral).
   `docs/AGENT_DOC_MAP.md` already states "code wins over diagrams"
   (`docs/ARCHITECTURE.md` line 5); it was not itself edited.

Deviation not addressed here: `docs/superpowers/plans/` citations of the old
module paths are dated plan documents and stay as written, per the
dated-entry exemption. `README.md` still owes its Batch 22 pass to WP-5, as
recorded in WP-0's own log entry.

Validation: `python scripts/doc_state_sync.py --check` passes.

### 2026-09-13 - Username validation no longer fails open (F-B22-1)

Side-task, found during owner manual testing of WP-0's running app.
`check_user_exists` (`scrobblescope/lastfm.py`) swallowed every exception --
timeout, Last.fm rate limit, malformed body, any non-200/404 status -- and
returned `exists: True`. `/validate_user` and `_validate_heatmap_user` read
that as a verified account, so a transient Last.fm failure showed a green
checkmark for arbitrary, unregistered usernames. Fixed by letting the
exception propagate; every caller already had its own try/except, so
`/validate_user` and `_validate_heatmap_user` now correctly answer 503
"Validation service unavailable" instead, and `results_loading` (which
already tolerated this check failing) is unaffected. Two regression tests
added in `tests/services/test_lastfm_service.py`. Finding: F-B22-1,
`FINDINGS.md` "Resolved this batch". `pytest -q` -- **1036 passed**.

### 2026-09-13 - Batch 21 closed (WP-8 complete)

- Owner end-to-end pass in Firefox: **done**, 2026-09-13, on the running app
  at 4b4965b. It covered every page in both themes and the saved images from
  results and from the heatmap.
- Two defects the pass found, both fixed before close-out:
  - The saved heatmap drew its own header, "LISTENING HEATMAP . LAST 365
    DAYS" over "A year of <name>" in italic accent, while the page had moved
    to the possessive headline in plain ink. `renderHeadline`'s docstring
    still described the old wording, which is how the two drifted.
  - The saved legend was a bare gradient: nothing in the file said which end
    meant more listening.
  Both are `4b4965b`. The export now reads the page's headline, eyebrow and
  legend captions, and the gate saves a real image and compares what the
  canvas drew.
- WP-8's other deliverables landed in `85e7511`, recorded in the entry above.
- The frontend and accessibility audit WP-8 charters is **not** part of this
  close-out. The owner moved it to Batch 23's close-out on 2026-09-13 so it
  runs once over the final UI; `BATCH21_DEFINITION.md` WP-8 carries the
  ruling and Batch 23's plan carries the obligation.
- Validation at close: `pytest -q` -- **1034 passed**;
  `python scripts/dev/frontend_gate.py` -- **28 checks passed in 50 runs**
  across chromium and firefox; `doc_state_sync.py --check` exit 0;
  pre-commit passed. CI passed on `85e7511`
  (run 34778729537).
- Next: Batch 22, enrichment providers. It opens on its own branch, which
  PLAYBOOK Section 3 must name before any commit, or the worktree guard
  raises WT003.
