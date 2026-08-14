# ScrobbleScope Repository Synthesis

Date: 2026-08-11
Purpose: point-in-time synthesis of the aligned Batch 21 worktree, current
operational discrepancies, PR #170 value and remaining findings, worktree
mechanics, and the repository's runtime and tooling architecture.

This is historical/reference documentation. PLAYBOOK.md remains the source of
truth for live work state, and AGENTS.md remains the source of agent rules.

**Status as of 2026-08-14.** The six discrepancies in Section 3 were verified
and have since been remediated: PR #170 merged on 2026-08-12, and the
dependency-graph and `asyncio_mode` corrections landed as a side-task. The
prose is preserved as the record of what was wrong and why. The architecture
diagrams that stood in Sections 5 and 6 were removed or migrated -- see those
sections. Live architecture now lives in `docs/ARCHITECTURE.md`.

---

## 1. Verified bootstrap state

Verified from the linked Batch 21 worktree after realigning its local branch:

- Worktree: `C:\Users\peter\.config\superpowers\worktrees\ScrobbleScope\batch-21`
- Primary checkout: `C:\Users\peter\Python Projects\ScrobbleScope`
- Branch: `wip/batch-21`
- Local and remote branch: `a7de76c` (`origin/wip/batch-21`)
- Relationship to `origin/main`: 0 behind, 5 ahead
- Those five commits are open PR #170, so the branch is correctly ahead.
- Full suite: **576 passed, 3 existing aiohttp/Python 3.13 warnings**
- Docsync: exit 0 with only the expected active-root
  `BATCH21_DEFINITION.md` warning
- Canonical current state: Batch 21 active; WP-0 done; PR #170 must land
  before the F-SWE-1 audit and Batch 21 WP-1.

Qualified local tools printed by the guard:

```powershell
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\python.exe"
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pytest.exe" -q
& "C:\Users\peter\Python Projects\ScrobbleScope\.venv\Scripts\pre-commit.exe" run --all-files
```

---

## 2. Worktree explanation

A Git worktree is a second checked-out working directory attached to the same
repository object store. It can hold a separate branch and separate uncommitted
changes while sharing Git history with the primary checkout.

For this repository:

- The primary checkout owns the sole `.venv`.
- The linked Batch 21 worktree owns branch `wip/batch-21`.
- The linked worktree must not create a second virtual environment.
- Commands shown as `pytest -q` or `pre-commit run --all-files` are written
  in primary-checkout form; from the linked worktree, run the absolute paths
  printed by `python scripts/dev/check_worktree_alignment.py`.

A branch can be in the right worktree and still be stale. GitHub rebase merges
can recreate commits on `main` while leaving the source branch on old commit
IDs. This can show both ahead and behind even when the files are identical.
The guard distinguishes that artifact from real divergence.

### Worktree guard files

- `scripts/dev/check_worktree_alignment.py`: CLI entry point. Prints stable
  diagnostics and exits nonzero on errors. It never fetches, switches, resets,
  pushes, or edits files.
- `scripts/dev/worktree_guard.py`: stable public facade for the internal
  modules.
- `scripts/dev/_worktree_guard_inspection.py`: collects read-only Git state:
  branch, worktree kind, dirty state, ahead/behind counts, tree identities,
  primary checkout, and active batch metadata.
- `scripts/dev/_worktree_guard_lineage.py`: parses PLAYBOOK Section 3 and
  classifies branch lineage: behind-only, diverged with identical trees, real
  divergence, missing branch metadata, detached HEAD, or wrong branch.
- `scripts/dev/_worktree_guard_venv.py`: resolves the one permitted primary
  `.venv` and detects a forbidden second environment in a linked worktree.
- `scripts/dev/_worktree_guard_runner.py`: runs specific read-only Git
  commands with a timeout.
- `scripts/dev/_worktree_guard_diagnostics.py`: constructs stable WT messages
  and applies display-safe ref rules.
- `scripts/dev/_worktree_guard_types.py`: immutable data structures shared by
  the guard modules.

Important: the guard inspects and warns. It does not repair anything.

---

## 3. Material discrepancies that can derail an agent

1. **PLAYBOOK Section 3 contradicts its own ordering.** It begins with
   "execute the full F-SWE-1 principles audit" but later says PR #170 must
   land before that audit begins. This was raised in three review rounds and
   remains live.

2. **The Batch 21 definition says WP-1 is next.** Its status line predates the
   PR #170 gate and contradicts PLAYBOOK, SESSION_CONTEXT, and FINDINGS. An
   agent opening the definition directly could start WP-1 against sources PR
   #170 still changes.

3. **PR #170 has a remaining code-safety gap.** The checked-out branch name
   (`actual_branch`) is assigned from Git and rendered verbatim in several WT
   diagnostics. Expected branch and base ref pass through the display-safe
   allowlist, but actual branch does not. Both reviewers flagged this on the
   current head.

4. **PLAYBOOK round-2 test arithmetic is internally inconsistent.** It says
   the count is unchanged because "four cases were added and three trimmed";
   that is net +1, while both round-1 and round-2 entries already record 576.

5. **SESSION_CONTEXT records a fabricated pytest setting.** It claims
   `asyncio_mode = "strict"` is configured in `pyproject.toml`; the actual
   pytest section contains only `pythonpath = "."`. Runtime behavior may be
   unaffected by the current pytest-asyncio default, but the configuration
   claim is false.

6. **The documented dependency graph has drifted.** SESSION_CONTEXT and the
   heatmap docstring claim `heatmap.py <- config`, but `heatmap.py` no longer
   imports `config`. Conversely, `app.py` imports `scrobblescope.config`
   under `__main__`, which the graph omits.

---

## 4. Recent gains

### PR #169 (merged)

PR #169 delivered the repository-integrity infrastructure now in use:

- deterministic live-documentation integrity checks (`DOC001`-`DOC006`)
- a read-only worktree alignment guard
- reliable primary-checkout Python/pytest/pre-commit resolution
- stronger pre-commit and CI enforcement
- synchronized live state across PLAYBOOK, SESSION_CONTEXT, and archives

### PR #170 (open at synthesis time)

PR #170's five commits provide real security and process gains:

1. **Closed a diagnostic-forgery trust boundary.** PLAYBOOK `Branch:` metadata
   could previously inject a fake extra WT diagnostic line. The parser now
   rejects line breaks and non-display-safe values.
2. **Unified a DRY failure into one rule.** Expected branch and base ref now
   share the `is_display_safe_ref` allowlist instead of separate, divergent
   checks.
3. **Removed a recipe for rebuilding the vulnerability.** The implementation
   plan no longer prescribes the vulnerable regex and explains why the rule
   must not be relaxed.
4. **Added adversarial regression coverage.** Tests cover line-break forgery
   and terminal repaint vectors without violating the near-duplicate test
   rule.

Remaining PR #170 items at synthesis time:

1. Label or sanitize `actual_branch` and add a targeted test.
2. Reorder PLAYBOOK Section 3 so landing PR #170 is first.
3. Correct the round-2 test-count explanation.
4. Refresh the PR description/checklist so validation claims match the current
   head.

---

## 5. Album-flow architecture

**The two diagrams that stood here were removed on 2026-08-14 because they
contradicted the code.** They are superseded by `docs/ARCHITECTURE.md`,
Sections 2 and 3, where every edge is verified against source. Recorded rather
than deleted silently, because an agent that saw them once should be able to
find out what happened to them.

What was wrong:

1. The sequence diagram drew `create_job(params)` **before**
   `acquire_job_slot()`. The real order is the reverse (`routes.py:460` then
   `:478`): the slot is acquired first and the request is rejected outright if
   none is free. An agent reconciling code to that diagram would allocate a
   `JOBS` entry and then reject the request, leaking an orphan job on every
   throttled call until TTL expiry.
2. Both diagrams drew `worker.py` as dispatching to `orchestrator.py` and
   `heatmap.py`. The import direction is the opposite -- both import `worker`
   for `release_job_slot`, and `worker.py` names neither. The dispatch is real
   but runtime-only, through a callable `routes.py` injects.
3. Neither declared its arrow semantics, which is what allowed a dependency
   edge and a control-flow edge to be drawn identically and read as the same
   claim.

### Pipeline responsibilities

- `app.py`: application factory, CSRF, logging, startup secret validation.
- `routes.py`: HTTP/session boundary and job lifecycle routes.
- `repositories.py`: shared `JOBS` state behind `jobs_lock`.
- `worker.py`: bounded job-slot semaphore and daemon thread startup.
- `orchestrator.py`: album pipeline, progress mapping, error classification,
  Spotify enrichment, and result assembly.
- `heatmap.py`: Last.fm-only heatmap pipeline and daily aggregation.
- `lastfm.py`: Last.fm HTTP client.
- `spotify.py`: Spotify token, search, and batch detail calls.
- `cache.py`: fail-open asyncpg/Postgres cache helpers.
- `utils.py`: global throttles, request cache, and async/thread helpers.

---

## 6. Operational tooling architecture

**Diagram migrated to `docs/ARCHITECTURE.md` Section 5 on 2026-08-14**, with
one edge corrected: it drew `doc_state_sync.py` importing the docsync parser,
logic, renderer and integrity modules directly. It imports only `docsync.cli`;
those four are `cli`'s own dependencies, so the `cli` node was missing and the
fan-out was attributed one level too high.

- `scripts/docsync`: keeps PLAYBOOK, SESSION_CONTEXT, and archive state
  deterministic.
- `scripts/dev/_worktree_guard_*`: protects linked-worktree bootstrap and
  primary-environment selection.
- Pre-commit enforces formatting, hygiene, private-key detection, and docsync.
- CI runs pre-commit, coverage gating, and dependency audit.
- Deployment runs one Gunicorn worker with four threads; shared in-memory job
  state depends on that single-process design.

---

## 7. Structural risks and agent mistake hotspots

1. **Single-process state is foundational.** Increasing Gunicorn workers
   silently shards `JOBS`, `REQUEST_CACHE`, and token state.
2. **`orchestrator.py` is the dominant complexity center** (916 lines) and is
   tracked as F-B20-2 for decomposition.
3. **Shared Spotify token state is not synchronized.** Last-write-wins is
   probably benign, but the race is undocumented in code.
4. **Some repository reads are shallow copies.** Mutating nested result
   objects can leak into shared state.
5. **JS has no automated test coverage.** Batch 21 will modify nearly every
   template and static surface, increasing visual-regression risk.
6. **Do not mutate `JOBS` outside `repositories.py`.** Its lock-guarded CRUD
   is the synchronization boundary.
7. **Do not run multi-worker "fixes."** The deployment contract is deliberate.
8. **Do not read `DATABASE_URL` from `os.environ` at call time in cache.py.**
   Import-time capture is a deliberate Windows workaround.
9. **Do not start Flask servers from agent shells or use `git add -A`.** Both
   are prohibited anti-patterns.
10. **Do not remove `_PLAYTIME_ALBUM_CAP` casually.** Playtime sorting causes
    proportional Spotify API load.
11. **Datetime tests must pin timezone behavior.** Heatmap day bucketing is
    UTC-anchored; naive inputs can produce vacuous tests.

---

## 8. Recommended next move at synthesis time

Do not start F-SWE-1 or Batch 21 WP-1 yet. First clear PR #170's actionable
items:

1. apply display-safe labeling to `actual_branch` and add a targeted test;
2. reorder PLAYBOOK Section 3 so landing PR #170 is first;
3. correct the round-2 test-count explanation;
4. refresh the PR description/checklist.

Then land PR #170, rerun the guard and full suite, and only then start the
F-SWE-1 audit.
