<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0008

### 2026-08-15 - PR #171 final four review threads remediated (side-task)

- Scope: the four remaining unresolved review threads on `e73540d` -- two
  Codex path-repointing reports and two Codex Top Albums sequence reports.
  All four were verified against the code and the moved files before any
  edit and all four were valid.
- Verification:
  - `docs/superpowers/plans/2026-08-11-pr-170-remediation.md` still cited
    `docs/history/GUARD_HARDENING_2026-08-11.md` and
    `docs/history/REPOSITORY_SYNTHESIS_2026-08-11.md`, both moved to
    `docs/history/reports/` by commit `5865c55`. The links resolved to
    nonexistent files.
  - `docs/history/definitions/BATCH9_DEFINITION.md` pointed twice to
    `docs/history/BATCH9_AUDIT_REMEDIATION_PLAN_2026-02-20.md`, and
    `BATCH10_DEFINITION_2026-02-21.md` pointed to the old
    `docs/history/ROUTES_SOC_AUDIT_2026-02-21.md` and
    `docs/history/TEST_QUALITY_AUDIT_2026-02-21.md` paths. All three reports
    now live under `docs/history/reports/`. These are definition-to-report
    references, not exempt point-in-time citations, so they must be repointed.
  - `_fetch_and_process()` returns immediately after `set_job_error` when
    `fetch_metadata["status"] == "error"`, while a `partial` status records
    `partial_data_warning` and continues. The diagram drew an unconditional
    transition from page fetching into grouping.
  - `_fetch_spotify_misses()` raises `SpotifyUnavailableError` when token
    acquisition fails with no cache hits, caught in `_fetch_and_process` as
    `set_job_error("spotify_unavailable"); return []` -- no merge or store.
    The diagram's no-cache-hits branch rejoined the unconditional merge/store
    steps.
- Plan vs implementation: repointed the four report paths in the remediation
  plan and the two batch definitions; the Top Albums sequence now branches on
  Last.fm status (terminal error vs partial-success-with-warning) and
  terminates after the no-cache-hits token failure while retaining the
  cached-success continuation.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the Last.fm error/partial paths and the
  no-cache-hits token failure.
- Validation: the updated diagram passes Mermaid validation and opens in
  preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run
  --all-files` -- all hooks pass. `doc_state_sync.py --check` -- exit 0 with
  the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this final remediation, then resolve the
  four threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 final two Codex threads remediated (side-task)

- Scope: the two remaining unresolved Codex threads on `3508c48`, both on the
  Top Albums sequence diagram. Both were verified against the code before any
  edit and both were valid.
- Verification:
  - `_get_db_connection()` returns `None` when `DATABASE_URL` is unset,
    asyncpg is unavailable, or connection attempts fail; `process_albums`
    then sets a `db_cache_warning` stat and skips lookup, cleanup, and
    persistence, so every album becomes a miss. The diagram presented those
    three cache operations as unconditional.
  - `_fetch_spotify_misses()` sets `partial_data_warning` and returns without
    searching when Spotify token acquisition fails and cache hits exist, so
    the pipeline completes successfully with cached albums only; it raises
    `SpotifyUnavailableError` only when no cache hits exist. The diagram sent
    every miss through search and grouped the token failure with the terminal
    path.
- Plan vs implementation: the Top Albums sequence now branches on DB
  availability before the cache lookup and branches the Spotify token-fetch
  failure into a success-with-warning path (cached albums only) versus the
  terminal `spotify_unavailable` path.
- Deviations: none. No production behavior changed and no tests were added;
  existing tests already cover the DB-disabled fallback and the partial-cache
  continuation.
- Validation: the updated diagram passes Mermaid validation and opens in
  preview; the tracked block exactly matches its ignored `.mmd` source.
  `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0 with the expected
  active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit and push this final remediation, then resolve both
  threads. PR #171 remains unmerged pending separate owner instruction.

### 2026-08-15 - PR #171 post-push review round remediated (side-task)

- Scope: two new visible Codex threads and all five suppressed Copilot
  comments on commit `11c9885`. The seven reports described six distinct
  defects because both reviewers found the omitted heatmap admission check.
  An independent review found one adjacent README polling claim during the
  required sibling sweep.
- Verification and loop check:
  - `routes.py` confirms that heatmap requests reject a missing username,
    unavailable validation service, and unknown user before cleanup or slot
    acquisition. `loading.js` and `heatmap.js` confirm that both browsers poll
    while their background tasks run. `docsync.logic` confirms tagged entries
    rotate to per-batch logs while untagged entries rotate to the side archive.
  - Git blame assigns all three affected diagram owners to the preceding
    review-fix commit. The omitted validation and rotation branch plus both
    serialized pollers are therefore self-inflicted extraction defects, not
    newly reached backlog. The older date headers became stale when this PR
    later changed the live dashboard and findings state without refreshing
    them. README's claim that `heatmap.js` polls `/heatmap_data` predated this
    review round; the script and Batch 18 records show that it polls
    `/progress` and fetches `/heatmap_data` only after completion.
- Plan vs implementation:
  - The tooling graph now distinguishes tagged rotation into
    `docs/history/logs/` from untagged rotation into `docs/logarchive/`.
  - The heatmap sequence now shows required-input and Last.fm user-existence
    validation, including terminal 400, 404, and 503 responses before job
    admission.
  - Both request sequences now use Mermaid parallel blocks for background
    processing and progress polling. SESSION_CONTEXT and FINDINGS carry the
    current 2026-08-15 update date.
  - README now distinguishes heatmap progress polling from the completed-data
    fetch.
- Deviations: no production behavior changed and no tests were added. Existing
  tests already cover heatmap validation responses and task lifecycle behavior.
- Validation: all three edited diagrams passed Mermaid validation and opened
  in preview; each tracked block exactly matches its ignored `.mmd` source.
  `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit run --all-files`
  -- all 10 hooks pass.
- Closure boundary: the pushed remediation commit and its passing Quality Gate
  define done for PR #171. Do not start another patch-review-patch cycle from
  later automated comments; a future agent may scrutinize them during a
  separately scoped deep sweep, but they are not automatic blockers for this
  documentation PR. Do not merge PR #171 without separate owner instruction.
- Forward guidance:
  - Execute the already-chartered Python-only F-SWE-1 audit, then start Batch
    21 WP-1. Keep architecture streamlining found by that audit separate from
    the frontend strangler unless it directly blocks a named WP acceptance
    criterion.
  - At WP-1, decide how CI obtains and caches the pinned, digest-verified
    standalone Tailwind and daisyUI artifacts. At WP-8, make the CSS drift hook
    `always_run` with no filenames or narrow the top-level pre-commit exclude;
    otherwise it cannot see `static/`. Add focused CSS, JS, and HTML checks
    before close-out because those paths currently have no lint coverage.
  - Treat `ruff` as an optional, separately measured Python-tooling migration,
    not a frontend prerequisite. It overlaps Black, isort, autoflake, and
    flake8, would require owner-approved dependency changes, and should land
    only with explicit parity criteria after the F-SWE-1 findings are known.

### 2026-08-15 - PR #171 review findings verified and remediated (side-task)

- Scope: all eight unresolved Codex and Copilot threads on PR #171, checked
  against the current code, tests, repository rules, and sibling documentation
  before any edit. A separate two-axis review found no additional verified
  spec or standards defect in the cumulative `origin/main...HEAD` diff.
- Plan vs implementation:
  - Seven factual comments were confirmed: partial heatmap data is successful
    with a warning; cache hits still write JOBS state; both task entry points
    release their slot unconditionally; `start_job_thread` releases the slot
    before re-raising while the route deletes the new job; README's dotted-edge
    legend omitted dispatch; and `orchestrator.py` was not the import-graph top.
  - The eighth comment was also confirmed against the complete new-file rule:
    the 499-line `docs/ARCHITECTURE.md` exceeded its existing `docs/` peer cap.
    It is now a 49-line index preserving all five section anchors. Five focused
    files under `docs/architecture/` own one diagram each and are 47-101 lines.
  - README, SESSION_CONTEXT, and the Mermaid instruction now point to the
    focused owners without duplicating diagrams. Gitignored `.mmd` sources were
    used for validation and preview only.
- Deviations: no production behavior changed and no tests were added; existing
  regression tests already cover partial-data continuation, startup slot
  release, and unconditional task cleanup.
- Validation: all six published diagrams passed Mermaid validation and opened
  in preview. `pytest -q` -- **590 passed**, 3 known warnings. `pre-commit
  run --all-files` -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0
  with the expected active-root `BATCH21_DEFINITION.md` warning.
- Forward guidance: commit the review remediation, push only with owner
  authorization, then post one batched reply and resolve the eight threads.

### 2026-08-14 - F-DATA-1 filed under P2; stale skill name corrected (side-task)

- Closes the two items the previous entry left as forward guidance.
- `F-DATA-1` self-labelled `Status: open (P2)` while sitting as the last
  entry under the P1 heading. Fixed by moving the `## P2` heading above it
  rather than relocating a 65-line block -- same result, far less churn, and
  the finding's own text is untouched.
- `DEVELOPMENT.md` still named the PR triage skill `gemini-pr-triage`; it was
  renamed `pr-bot-triage`. Real drift, not a snapshot, so it is corrected
  rather than preserved.
- **Scoping correction from the owner, recorded because an agent got it
  wrong today:** `DEVELOPMENT.md` is not an agent document. It is absent from
  docsync's live-document set and from the AGENTS.md bootstrap reading list,
  and belongs with `README.md` as human-facing methodology writing. A line
  added to `AGENT_NOTES.md` earlier the same day pointed agents at it for the
  skills-are-local decision; that line now states the decision directly
  instead. Batch definitions may still direct an agent to *write* a build
  step into it -- writing to it is in scope, treating it as a source of
  operating rules is not.
- Plan vs implementation: these two were dropped from the Phase 5 scope
  reduction and then reinstated by the owner, since both sit in working
  documents rather than in the archive the reduction was about.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0. `check_worktree_alignment.py`
  -- exit 0. Verified exactly one `## P2` heading remains and that `F-MAS-4`
  is still the last P1 entry.
- Forward guidance: nothing outstanding from the remediation. Next is the
  F-SWE-1 audit, then Batch 21 WP-1.

### 2026-08-14 - Batch 21 tooling mapped to its work packages (side-task)

- Scope: `AGENT_NOTES.md` gains a map from the installed skills and MCP
  servers to WP-1 through WP-8, written before WP-1 rather than discovered
  during it. Every entry was verified against the live machine and repository
  on the day rather than carried forward from the plan's older table.
- Structural fact recorded so nobody hunts for what is not there:
  `BATCH21_DEFINITION.md` has **no per-WP acceptance criteria**. It carries
  one batch-level list of 9 plus a per-WP validation gate that every WP runs
  identically, so the map keys on the WP and names the criteria each serves.
- Four separate skill sources are installed and their names collide -- `tdd`
  and `test-driven-development` are different files from different upstreams,
  as are `diagnosing-bugs` and `systematic-debugging`. The map says which
  source each comes from, because naming the wrong one loads the wrong file.
- Seven gaps recorded, all verified. Three of them converge on WP-8 and one
  of those has to be decided at WP-1: the pre-commit top-level exclude covers
  13 directories including `static/` and `templates/`, so the planned
  `tailwind-css-drift` hook could never fire as a file-scoped hook and must
  use the `always_run` pattern; CI has no Node and no Tailwind binary, so the
  headless-Linux fetch is unsolved; and no CSS, JS or HTML hook exists at all,
  leaving the files eight WPs rewrite unreachable by two mechanisms at once.
- Two plan claims were corrected against the live state. The exclude covers
  **13** directories, not the 12 the plan's Phase 6 still said -- an earlier
  phase had already found 13 and the later section was never updated. And the
  `skills-lock.json` drift (22 locked, 20 present) is bookkeeping only: both
  absent skills are supplied by the superpowers plugin, so it is not the
  capability gap it looks like.
- One claim was verified rather than assumed after a false negative:
  `workflow_dispatch` is on `origin/main` and usable. An initial check
  reported it missing, which turned out to be Git Bash rewriting the
  `rev:path` argument on Windows rather than anything about the repository.
- Plan vs implementation: as planned, with the MCP inventory re-enumerated
  live as the plan instructed rather than copied.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0 (expected root warning for the
  active `BATCH21_DEFINITION.md`). `check_worktree_alignment.py` -- exit 0.
- Forward guidance: this closes the post-merge remediation. Next is the
  F-SWE-1 principles audit per `docs/SWE_AUDIT_CHARTER.md`, whose report
  belongs under `docs/history/reports/`, then Batch 21 WP-1. The three open
  PR #170 review threads and the four ruleset settings remain owner-side.

### 2026-08-14 - docs/history one-off documents collected under reports/ (side-task)

- Scope: the 26 loose files at the top of `docs/history/`, which had grown
  into a flat pile beside the three organised subdirectories. Organisation
  only -- the owner scoped this to moving files, not revising them.
- 25 moved into `docs/history/reports/` with `git mv`. Not one of their
  bodies was edited.
- `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` deliberately stayed at the
  top level. It is the Batch 14 "Moved:" tombstone whose only purpose is to
  resolve references to that legacy path, so relocating it would defeat it.
  `FINDINGS.md:115` records the same disposition.
- One folder rather than a split by kind. Three Markdown links exist between
  these files, and they connect an audit, a changelog, a performance summary
  and a refactor plan -- four different kinds. Any by-kind split breaks all
  three and forces edits to files that were explicitly out of scope. A single
  folder keeps every relative link resolving untouched.
- References repointed in the live documents only: `AGENTS.md`,
  `DEVELOPMENT.md`, `FINDINGS.md`, `.claude/SESSION_CONTEXT.md` and
  `docs/SWE_AUDIT_CHARTER.md`. Two of those are forward-looking and mattered
  most: `FINDINGS.md` F-SWE-1 and the charter's output contract both name
  where the pending SWE principles audit must write its report, and both now
  name `reports/`. `AGENTS.md` documentation-touch rule likewise.
- Dated records were left as written, including the ones that now cite a
  path that moved: the archived batch definitions and logs,
  `docs/logarchive/`, the superseded plan under `docs/superpowers/plans/`,
  and PLAYBOOK Section 4's own earlier entries. A point-in-time record
  rewritten to match a later reorganisation stops being a record. This is
  the same reasoning already applied to `SESSION_CONTEXT_REFERENCE.md`.
- Consequence, stated so it is not later mistaken for rot: paths cited inside
  `docs/history/reports/*` and inside the dated archives may name the
  pre-2026-08-14 flat layout. `DEVELOPMENT.md` now says so where it describes
  the archive.
- `DOC001` scans only the live documents, so the archive's internal citations
  never entered the gate; the repointing above was still required because
  five of the moved paths were cited from documents it does scan.
- Plan vs implementation: reduced on owner direction. The planned content
  remediation -- linking the two orphans, repointing three dangling
  `EXECUTION_PLAYBOOK_2026-02-11.md` cites, annotating seven dead `app.py`
  line references in `PERFORMANCE_TIMING.md`, a completion note on
  `BATCH8_REFACTOR_PLAN.md`, collapsing the overlapping 2026-01-04
  performance documents, and a `docs/history/README.md` index -- was dropped
  as out of scope for an organisation pass.
- Deviations: none beyond that reduction.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `doc_state_sync.py --check` -- exit 0 (expected root warning for the
  active `BATCH21_DEFINITION.md`). `check_worktree_alignment.py` -- exit 0.
  Every repointed path was confirmed to resolve on disk.
- Forward guidance: `FINDINGS.md` F-DATA-1 still sits under the P1 heading
  while labelling itself P2, and `DEVELOPMENT.md` still calls the
  `pr-bot-triage` skill by its old `gemini-pr-triage` name. Both were part of
  the dropped remediation and remain open.

### 2026-08-14 - F-WORKTREE-5 closed: count branch candidates before filtering (side-task)

- Scope: the last open guard defect, reported independently by Codex in PR
  #170 round 5 and by Copilot in round 6, and left open across both.
- Defect: `parse_batch_branch` filtered candidates through
  `is_display_safe_ref` and only then counted them. Because that allowlist is
  deliberately narrower than Git's ref rule, a rejected candidate can still
  name a real branch, so a Section 3 declaring two branches -- one of them
  non-ASCII -- had one side discarded and reported the survivor as expected.
  The predicate decides whether a value may be rendered, not whether it exists.
- TDD: the regression test failed first with `DID NOT RAISE`, using
  `wip/b\xe4tch-21` as the second value -- Git accepts non-ASCII letters in a
  ref name, and the escape keeps the test source ASCII. Then counted distinct
  candidates before any filtering and moved the display-safety filter after
  the conflict check, where it only decides what may be rendered.
- Anti-vacuity: both orderings are load-bearing. Deleting the
  count-before-filter fails the new test; deleting the display-safety filter
  fails three cases of
  `test_a_branch_value_cannot_repaint_the_diagnostic_line`.
- Also corrected the stale justifying comment in the source, and added a
  correction note to `docs/superpowers/plans/2026-08-05-worktree-safety-guard.md`,
  whose Step 3 still prescribed the defective ordering in prose. Leaving that
  in place would have let the plan teach the defect back into the code.
- Plan vs implementation: as planned.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `pre-commit run --all-files` -- all 10 hooks
  pass. `check_worktree_alignment.py` -- exit 0.
- Forward guidance: F-WORKTREE-5's two PR #170 threads can now be answered and
  resolved. F-WORKTREE-3 and F-WORKTREE-4 remain open by decision.

### 2026-08-14 - architecture diagrams corrected and given one owner (side-task)

- Scope: newly integrated Mermaid material that contradicted the code, plus
  the three older diagram copies that disagreed with it and each other.
- The central defect, in both sequence diagrams: `create_job` was drawn with
  no preceding `acquire_job_slot`. The real order is the reverse
  (`routes.py:460` then `:478`, and `:570` then `:582`) and is a fail-fast:
  the slot is taken first and the request rejected outright if none is free.
  An agent reconciling code to the diagram would allocate a `JOBS` entry and
  then reject, leaking an orphan job on every throttled call until TTL expiry.
  README already stated the correct order, so the repository contradicted
  itself. The same inversion was present in the synthesis document.
- Nine further defects, each verified against source: `worker.py` drawn as
  importing `orchestrator` and `heatmap` when both import *it* (the dispatch
  is real but runtime-only, through a callable `routes.py` injects); a
  `cache.py -> utils.py` edge that does not exist in any form; the cache
  hit/miss partition attributed to `cache.py` when it happens in
  `orchestrator.py:561-578`, and cannot happen in `cache.py`, which never sees
  the full candidate set; expiry cleanup drawn as cache-internal when the
  orchestrator calls it; `start_job_thread` given the wrong signature; the
  heatmap response typed as a rendered page rather than JSON 202; and missing
  `routes -> orchestrator`, `routes -> heatmap`, `routes -> utils` and
  `repositories -> errors` edges.
- Ownership after this change: `README.md` keeps one high-level diagram and
  now declares its arrow semantics, which was the root defect the wrong
  diagrams shared -- a dependency edge and a control-flow edge were drawn
  identically and read as the same claim. `docs/ARCHITECTURE.md` owns every
  detailed diagram. SESSION_CONTEXT Section 5 keeps a corrected compact
  summary and points there for detail. The synthesis Section 5 diagrams were
  removed with a note recording why, and its Section 6 tooling diagram
  migrated with one edge corrected: `doc_state_sync.py` imports only
  `docsync.cli`, so the fan-out had been attributed one level too high.
- Renamed the incoming doc from a dated filename to `docs/ARCHITECTURE.md`.
  It is a living reference, and `docs/` root holds durable documents while
  `docs/history/` holds dated ones; a date in the name would have become
  false at the first correction.
- Every diagram was validated before being written, per
  `.github/instructions/mermaid.instructions.md` Rule 1. This caught a real
  parse failure: a `;` inside a sequence-diagram message terminates the
  statement. The incoming document had escaped it as `&#59;&#59;`, which
  parsed but rendered as visible garbage and dropped a `%`. Removed the
  semicolon rather than escaping it.
- Now tracked, with the disposition rule recorded in the previous entry:
  `docs/ARCHITECTURE.md`, the two `.github` instruction files (converted to
  ASCII, with a ScrobbleScope scoping section reconciling their `.mmd` rule
  against this repository's tracked-Markdown layout), the corrected synthesis,
  and the PR #170 remediation plan under a superseded header naming the four
  ways it must not be executed.
- Plan vs implementation: the plan called for deleting `sequenceDiagram.mmd`
  as a duplicate. Kept instead and moved to `diagrams/`, with `*.mmd`
  gitignored -- deleting the only `.mmd` would contradict Rule 5 of the
  instruction file being tracked in the same change.
- Deviations: none.
- Validation: `pytest -q` -- **590 passed**. All six diagrams return
  `valid: true` from the Mermaid validator. `doc_state_sync.py --check` --
  passed with the expected root-BATCH warning.
- Forward guidance: `docs/history/` still needs an index and its dead
  references repointed, and `AGENT_NOTES.md` still needs the tooling map.

### 2026-08-14 - dependency-graph and pytest-config claims corrected (side-task)

- Scope: four documentation claims that contradict the code, plus the
  ordering statements left stale by the PR #170 merge.
- Dependency graph, SESSION_CONTEXT Section 4. `heatmap.py <- config` was
  false -- `heatmap.py` imports lastfm, repositories, utils and worker, and
  reaches config only transitively through those. The same wrong chain was
  repeated in the `heatmap.py` module docstring, so fixing one source alone
  would have left the other. `app.py <- routes` omitted the `config` edge at
  `app.py:143` (`ensure_api_keys`), which exists only under the `__main__`
  guard; recorded with that scope rather than as an unconditional import.
  Added `dev/dev_start.py`, documented in Section 3 but absent from the
  graph. Every other edge was re-derived from the imports and is correct.
- Pytest config, SESSION_CONTEXT Section 7. The claimed
  `asyncio_mode = "strict"` is not configured anywhere: `pyproject.toml`
  contains only `pythonpath = "."`, and no `pytest.ini`, `setup.cfg` or
  `tox.ini` exists. `git log -S` shows the key was never in the file, so
  this was wrong when written rather than drift. The same sentence appears
  in `docs/history/SESSION_CONTEXT_REFERENCE.md`, which is left as written:
  that file is a labelled 2026-02-23 snapshot of SESSION_CONTEXT.md, and a
  snapshot that silently corrects its original stops being a snapshot.
- Ordering. PR #170 merged, so PLAYBOOK Section 3, BATCH21_DEFINITION,
  SESSION_CONTEXT Section 1 and FINDINGS all still said it must land first.
  All four now name the merge and give the F-SWE-1 audit as the next action.
  The batch-open baseline in BATCH21_DEFINITION gained its date so the 390
  is not misread as current.
- README cross-reference. "See `AGENTS.md` for the full dependency graph"
  pointed at a file that has no graph; repointed to SESSION_CONTEXT
  Section 4, which is where it lives.
- AGENTS.md gained a note that WT004 after a merge is expected and routine,
  with the tree-equality precondition that separates it from a real
  divergence. Without it the guard's stop-and-escalate remediation reads as
  alarming for what is now a per-merge occurrence.
- Plan vs implementation: as planned.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `check_worktree_alignment.py` -- exit 0.
  `doc_state_sync.py --check` -- passed with the expected root-BATCH warning.
- Forward guidance: the architecture diagrams still contradict the code they
  describe, most seriously by drawing `create_job` with no preceding
  `acquire_job_slot`. That is the next side-task, followed by F-WORKTREE-5.

### 2026-08-14 - post-merge realignment and untracked-artifact disposition (side-task)

- Scope: restore a green bootstrap after PR #170 merged, and give every
  untracked path an explicit disposition. Two gates were failing at once.
- Gate 1, the worktree guard. `main` requires linear history and its ruleset
  permits only squash and rebase merges, so the merge rebased the branch and
  left `wip/batch-21` 9/9 diverged from `origin/main` with byte-identical
  trees (`dedd776` both) -- `ERROR WT004`, exit 1. Verified the two tree
  hashes matched and `git diff HEAD origin/main` was empty, then reset the
  branch onto `origin/main` and force-pushed with lease under the owner
  approval the guard's remediation requires. No file changed; only the
  commit objects the branch points at. This state will recur after every
  merge, since it follows from the ruleset rather than from any mistake.
- Gate 2, the integrity gate. The `setup-matt-pocock-skills` skill had
  appended an `## Agent skills` section to `AGENTS.md` pointing at a new
  untracked `docs/agents/`, which produced three `DOC001` errors and would
  have failed `pre-commit` and CI. Reverted. The skill followed its own
  file-selection rule (no `CLAUDE.md` exists, so `AGENTS.md` was its
  fallback); the mismatch is that it treats `AGENTS.md` as an appendable
  conventions file while this repository treats it as a governed ruleset.
- Disposition: untracked files went from 73 to 5, all five of which are
  slated for tracking in later side-tasks. Ignored with recorded reasons:
  `.agents/` and `skills-lock.json` (vendored from two upstream skill
  repositories, already drifting -- the lock names 22 skills, the tree holds
  20); `docs/agents/` (unedited vendor templates describing a layout this
  repository does not use); and `*.mmd` (Mermaid authoring scratch, kept
  separate so no diagram has a second copy free to drift).
- Note for future audits: `git status` collapses directories, so the set
  read as 8 paths and was actually 73 files. Use `-uall`. Separately,
  `git check-ignore -v <path>/` reports a spurious match against a blank
  `.gitignore` line for any path given a trailing slash -- a nonexistent
  directory and a fully tracked one both "match" it.
- Plan vs implementation: as planned. `sequenceDiagram.mmd` was slated for
  deletion as a duplicate; kept instead and moved to
  `diagrams/top-albums-sequence.mmd`, because
  `.github/instructions/mermaid.instructions.md` requires diagrams be
  written to `.mmd` files. Ignoring the pattern satisfies both that rule and
  single-source-of-truth.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `check_worktree_alignment.py` -- exit 0
  (WT010 only). `doc_state_sync.py --check` -- passed with the expected
  root-BATCH warning.
- Forward guidance: the four documents still describe PR #170 as pending;
  correcting them is the next side-task. Then the architecture diagrams,
  which contradict the code they describe, and F-WORKTREE-5, which two
  reviewers filed independently and which still has two open threads.
