# Batch 23 WP-0 Parts B and C: reconcile and clear -- Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take every finding in `BATCH23_DEFINITION.md` WP-0 Part C's set, plus the Part B records, to one
of the three exits the definition allows -- fixed, confirmed already fixed, or ruled out by the owner --
so the Spotify export feature starts on a repository with no stale record and no open P0 or P1 defect.

**Architecture:** Three stages, in this order:

- **Stage 1 -- records.** Close what is already fixed, with evidence. This needs no ruling.
- **Stage 2 -- pipeline fixes.** These are the findings Batch 23's own code will sit on: F-SWE-5,
  F-SWE-6, F-B22-7, F-B21-6 and F-LOAD-1. They are written in full, for the recommended answer to each
  question they depend on.
- **Stage 3 -- the owner's rulings, written into the findings.**

The control-plane and frontend clusters get their own plans once the rulings are in, one per subsystem
(the writing-plans skill's scope rule). "After this plan" says what each covers and in what order.

**Tech Stack:** Python 3.13 stdlib, Flask, pytest, `unittest.mock`, Playwright (frontend gate). No new
dependency.

**Evidence base.** Four read-only triage passes checked all 38 IDs against `167e650` on 2026-09-23. Their
reports are in the untracked workspace `.superpowers/sdd/2026-09-23-batch23-wp0-reconcile-and-clear/`,
as `triage-A-stale-records.md`, `triage-B-frontend.md`, `triage-C-backend.md` and
`triage-D-control-plane.md`. The controller re-ran the load-bearing checks:

- the ancestry of all seven fix commits named in Task 1;
- the call sites of `enrich_albums`, `as_cache_row` and the job getters;
- the `loading.js` source-label defect found in Task 7, which triage missed.

## Global Constraints

Every task's requirements include this section.

- **Qualified interpreter only.** This is a linked worktree. Use
  `C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe` and its sibling `pytest.exe` /
  `pre-commit.exe`. Never bare `pip`, never a second venv. Quote the path, since it contains a space.
- **No new dependency, no version change** without the owner's approval (`AGENTS.md` "Environment Setup").
- **Logging (owner ruling, 2026-09-23).** Every commit logs an **untagged** `PLAYBOOK.md` Section 4
  entry, placed directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker. Its heading carries no
  `WP-<digit>` token, and its body opens with "Side task, no batch tag: ... part of Batch 23 WP-0". The
  reason is in `BATCH23_DEFINITION.md` WP-0. Never move entries across the markers by hand.
- **Section 3 stays true.** Keep the `**Next action:** WP-0 is next.` wording exactly, because DOC007
  reads it. Update only its progress sentence.
- **Part C may change behaviour and may edit an existing test, but only where the finding being fixed
  requires it.** The commit body names every changed assertion by test id. A commit never mixes Part A
  and Part C work.
- **Commit procedure, in this order** (`AGENTS.md` "Commit Rules"):
  1. the Section 4 entry;
  2. `doc_state_sync.py --fix`;
  3. the full suite;
  4. `pre-commit run --all-files`;
  5. `frontend_gate.py`, whenever a task touches `static/`, `templates/` or `scripts/dev/_frontend_gate_*`;
  6. `doc_state_sync.py --check`, which must exit 0; the only acceptable warning is the root
     `BATCH23_DEFINITION.md` one.
- **Measure the count.** Run the suite as
  `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" -m pytest -q --ignore=tests/scripts/dev/test_mutation_test.py -p no:cacheprovider`
  and quote it exactly as `` Validation: `pytest -q` -- **N passed**; the untracked mutation-runner tests
  were excluded, since they are not repository state. `` A task that adds tests also updates the count
  sites DOC006 and DOC008 name:
  - the `.claude/SESSION_CONTEXT.md` Section 1 `Tests` row;
  - the `.claude/SESSION_CONTEXT.md` `## 6. Test structure (N tests)` heading;
  - the `FINDINGS.md` header count.
  A new test module also changes the module count.
- **Resolving a finding.** Replace its free-prose `Status:` line with the canonical record from
  `docs/agents/issue-tracker.md`. The status line carries the bare outcome and nothing else. The
  archive's order is the status line, the completion date, then the reason on its own line:
  ```
  - [x] **Status:** resolved
  **Completed:** <YYYY-MM-DD, the commit's date>
  <What fixed it, naming the function.>
  ```
  *Corrected 2026-09-23, after Task 1.* This template first put the reason on the status line
  (`resolved -- <reason>`). The gate accepts only `resolved` or `no action` there: any trailing text
  fails DOC015, and "deploy", "pending" or "accepted" fails DOC014 (`scripts/docsync/findings.py`,
  `_TERMINAL_SUFFIXES`, `PENDING_QUALIFIER_RE`). Where a task below says "the canonical record's
  reason: ...", that text is the reason line.
  Run `--fix`, which rotates the record into `docs/history/findings/FINDINGS_ARCHIVE.md`, then stage both
  files. Never write "resolved" about a *different* finding in prose (DOC023): say "archived" or
  "settled" instead.
- **Commit discipline.** Conventional Commits, imperative mood, no trailing period, subject of 72
  characters or fewer. Stage paths by name; `git add -A` and `git add .` are forbidden. Never
  `--no-verify`. No `Co-authored-by` trailer and no other attribution line.
- **Untracked files belong to other agents.** Never stage, edit or delete them: the mutation runner, its
  scope file and tests, `progress_copy.md`, the review HTML files, `plan.md`, the audit documents, and
  anything under `.superpowers/`.
- **ASCII only** in every file: `--`, not an em dash.
- **The pre-commit `worktree-alignment` hook prints `ERROR WT005 ... origin/main` and still passes.** It
  is advisory, and the branch is cut from `test`, so do not act on it.

---

## Where this plan sits in WP-0

1. **Part A first:** `docs/superpowers/plans/2026-09-21-batch23-wp0-foundation.md` Task 2, the three
   behaviour-neutral extractions. It needs no ruling and can run while the owner answers the questions
   below. Its parity acceptance is easiest to prove before Part C starts changing tests.
2. **This plan's Stage 1**, then **Stage 2**. Stage 2's tasks are written for the recommended answers to
   Q1 and Q2. If the owner picks differently, rewrite the affected task before dispatching it.
3. **Stage 3**, once the answers are in.
4. **The foundation plan's Tasks 4-10**, which are Part B's control-plane work.
5. **The three follow-on plans** listed under "After this plan".
6. **WP-0 close-out**: one tagged `(Batch 23 WP-0)` entry, once Parts A, B and C each meet their
   acceptance.

---

## Owner rulings needed

The owner answers these once, before Stage 2. Reply with the question number and a letter, and mark
each answer here. A question marked **(asked)** has no default; every other question has a recommended
answer.

| # | Question | Options | Recommended |
| --- | --- | --- | --- |
| Q0 | The 2026-09-23 run shows Spotify answering 142 of 146 lookups, so the Spotify credentials are restored. Did MusicBrainz corrections appear on that results page (the Batch 22 owner check)? | a) yes, corrections seen; b) not checked -- keep it owed; c) no corrections although expected -- file a finding | **(asked)** |
| Q1 | **F-SWE-6** (P2): add it to the set, and pick the lease policy | a) reads never renew: a job expires `JOB_TTL_SECONDS` after its last write; b) keep sliding renewal but cap the absolute lifetime from `created_at`; c) keep today's behaviour and document it | **a** -- see "Controller's view" below |
| Q2 | **F-B22-7** (P2): add it to the set, and pick the shape | a) translate Spotify's payload in `spotify.py`, route every metadata row through a corrected `as_cache_row`, and retire the unused `enrich_albums`; b) make `enrich_albums` the live path, as the Batch 22 facade test intended (22 test patch sites move from the orchestrator to `spotify`); c) delete `as_cache_row` and `enrich_albums` and leave the orchestrator parsing the payload | **a** |
| Q3 | **F-DOCSYNC-11, -12 and -13** are one mechanism under three IDs | a) an explicit `--fix --test-count N` input that writes all four count sites; b) a count file a test run drops, which `--fix` reads; c) accept the same-date limitation | **a** |
| Q4 | **New docsync finding:** a work package reads as complete on its first tagged entry | a) an entry closes a work package only when it carries a `**Status:** WP-N complete` line; b) read completion from the definition's checkboxes; c) keep the untagged-until-done convention, and document it in `AGENTS.md` | **a** |
| Q5 | **F-B21-20:** the Tailwind hook compares against the index, but the procedure stages last | a) reorder `AGENTS.md` to stage named paths before `pre-commit run --all-files`; b) make the hook compare against pre-rebuild bytes | **a** |
| Q6 | **F-B21-3:** the unused-PDF packages and the HTTP advisories are already fixed (`0f5b2468`, `c1620a9d`, both on `main`), but `virtualenv`, `distlib`, `filelock` and `platformdirs` still ship in `requirements.txt` | a) move the four to `requirements-dev.txt`, still pinned; b) drop them; c) leave them | **a** |
| Q7 | **F-MAS-1:** mocks may drift from the real APIs | a) fixtures transcribed from each provider's published docs, plus shape tests, recorded as a weaker guarantee; b) approve a recording library and supply one capture yourself; c) re-grade to P2 | **a** |
| Q8 | **F-B21-14:** the heatmap has no non-colour path to its data | a) focusable, labelled cells that reuse the tooltip text; b) a table view; c) both | **a** |
| Q9 | **F-B21-22:** the theme detaches from the system on first toggle | a) Light/Dark/System three-state control; b) two-state toggle that clears the stored choice when it matches the system; c) leave it | **b** |
| Q10 | **F-B21-53:** the light card (`#f9f7f1`) is marginally darker than the page (`#faf7f0`) | a) raise the card token above the page; b) accept that cards are delineated by their border, and stop calling them elevated | **(asked)** |
| Q11 | **F-B21-60:** the spotlight breaks Spotify's content rules | a) ship the crop, overlay, animation and fallback fixes now, and add the Spotify icon when an asset exists; b) hold the whole fix; c) you supply the official icon file now and it ships complete | **a**, or **c** if you have the file |
| Q12 | **F-B21-19:** the heatmap's mobile layout and day-detail drifted from the handoff | a) record an override for the width-driven mobile grid, and rule day-detail a future feature; b) build the four season strips | **a** |
| Q13 | **F-B21-4 item 3:** the Results "matched vs seen" stat card | a) fold it into WP-6, which rebuilds Results statistics; b) build it now; c) drop it | **a** |
| Q14 | **F-B21-18:** the JavaScript unit seam | a) build the Chromium harness now for `rocketColor`, `countToNorm` and the export header, and let WP-6 cover `computeStreak`; b) wrap `computeStreak` now as well | **a** |
| Q15 | **F-B21-25 items 1-2 and F-B21-9** | a) move the two fast-path paragraphs below the bootstrap list, declare `skills-lock.json` in a warn-only manifest, and build the findings/issues sync as a manual `gh`-based script; b) the same, but run the sync as a scheduled CI job | **a** |
| Q16 | **Rule-outs, approved as a batch** (the exact records are in Task 10) | a) approve all; b) approve with exceptions (name them) | **a** |

**Owner answers, 2026-09-23.** Every question takes its recommended answer, except these:

- **Q0.** No MusicBrainz lines appeared in the run's log. That is expected, and it is not a result:
  - `release_checks._run_release_checks` skips when the cache database is unavailable, logging
    "Release checks skipped: the cache DB is unavailable." Postgres was down on purpose for that run.
  - `enqueue_release_check` skips silently when `MUSICBRAINZ_CONTACT` is unset.
  - A second run the same day, with Postgres up, also logged nothing. That is not evidence either:
    the worker logs nothing on a successful run, and the primary checkout sets no
    `MUSICBRAINZ_CONTACT`.
  - So the Batch 22 MusicBrainz check stays **owed**. Settle it from the results page's release-check
    disclosure, from `GET /api/release_checks`, or from `original_release_cache`'s row count
    (`docs/history/reports/HANDOFF_2026-09-23.md` section 6).
  - The worker needs start and finish log lines with counts, plus a line for the silent contact skip.
    Add them to the test-infrastructure plan, not as a new finding.
- **Q10: b.** The UI stays as it is. F-B21-53 becomes no action: cards are delineated by their
  border, and `docs/design/README.md` stops calling them elevated. Task 10 records it.
- **Q11: a**, since no icon asset was supplied.
- **Q16: a.** All the rule-outs below are approved.
- **Q0, settled later on 2026-09-23.** `original_release_cache` held 121 rows. 60 were written within
  a minute of the owner's 16:34 local run (Postgres up) and 60 at 06:04 local, so both runs with the DB
  up produced corrections. The worker is silent on success, which is why the logs showed nothing. The
  Batch 22 MusicBrainz owner check is **done**.
- **F-B22-8 added (owner, 2026-09-23).** The run with Postgres down logged "Release checks skipped: the
  cache DB is unavailable." The owner ruled that checks run whatever the cache's state. Only local
  development reaches that branch, so the finding is P2, and it joins the set as F-SWE-6 and F-B22-7
  did. Task 11 fixes it.

The rule-outs Q16 approves:

- **F-B21-15:** no action. Batch 23 schedules no `GET /heatmap/<username>` route, and the finding says
  "with the route or not at all".
- **F-B21-48:** re-graded to P2. It is a persistent-cache feature, not a defect.
- **F-B18-11:** re-graded to P2, with a pointer to F-B21-48. Its only unrejected remedy is that cache.
- **F-STYLE-1:** no action. It is guidance that cannot become a gate, and its one example was gone by
  `14ba5705`.
- **F-STYLE-2:** no action on the docstring convention, recorded as declined. Its other two items are
  already settled.
- **F-WORKTREE-4:** no action. This is the owner's 2026-09-21 ruling, written in the canonical form.
- **F-DOCSYNC-6:** three boundary items become no action, and its two mechanical items are fixed in
  the control-plane plan.
- **F-WORKTREE-3:** the between-batch ancestry item becomes no action, and the other two items are
  fixed.
- **F-B21-25 item 3:** the Codex/Copilot entry point is re-graded to P2 as a new finding, because it
  is unscoped.
- **F-B21-24:** Tasks 2-5 are confirmed done. Task 6 is Batch 23 WP-7's audit under another name, so
  the finding is recorded as folded into WP-7.
- **F-MAS-2:** no action, absorbed into F-B21-18. It is the same untested JavaScript, which F-B21-18
  describes with exact functions, an owner-ruled mechanism and a schedule.

### Controller's view on F-SWE-6 (the owner asked)

**It is worth doing, and it is cheap.**

The cost is three deleted lines, three docstrings, one comment and one parametrized test. No
existing test asserts the renewal: every test that touches `updated_at` checks a *writer*.

The benefit is larger than the finding says. `get_job_context` renews the lease, and two callers poll
it:

- **`GET /api/release_checks`.** The results page polls it while it is open, so an open tab keeps its
  job alive indefinitely.
- **The release-check worker thread** (`release_checks.py`, where it checks that a job still exists).
  The server therefore renews jobs with no browser involved.

For Batch 23 this breaks a stated promise. The definition says the parsed upload expires with the
two-hour TTL, and with renewal on read an open results tab holds it indefinitely.

The one thing given up: someone returning to a results page more than two hours after their job last
changed must search again. Session recovery works as before within that window. An in-memory store
that promises to forget uploads should behave exactly this way.

---

## Disposition of the set

Every ID the definition lists, plus the P2s Q1 and Q2 would add. "Verified" is the triage result at
`167e650`.

| ID | Verified | Exit | Where |
| --- | --- | --- | --- |
| F-B20-3, F-B21-10, F-B21-26, F-B21-27, F-B21-28, F-B21-29 | fixed, and the fix is on `main` | already fixed | Task 1 |
| F-MAS-2 | same defect as F-B21-18 | ruled out: absorbed, with a pointer (Q16) | Task 10 |
| F-SWE-6 (P2, if Q1) | real | fixed | Task 3 |
| F-B22-7 (P2, if Q2) | real, and wider than filed | fixed | Tasks 4-6 |
| F-SWE-5 | real; the foundation sketch's "tests to update" premise is false | fixed | Task 7 |
| F-B21-6 | real, at three `datetime.now()` sites | fixed, before WP-4 | Task 8 |
| F-LOAD-1 | real; an occupancy count would always read full | fixed | Task 9 |
| F-B22-8 (P2, owner-added) | real, local development only | fixed | Task 11 |
| F-B21-15, F-B21-48, F-B18-11, F-STYLE-1, F-STYLE-2, F-WORKTREE-4, F-B21-24 | ruling-only | ruled out, as Q16 | Task 10 |
| F-B21-4 | items 1, 2 and 4 fixed; item 3 open | item 3 per Q13 | Task 10 |
| F-B21-19 | real | per Q12 | Task 10 (override) or the frontend plan |
| F-DOCSYNC-6, F-DOCSYNC-7, F-DOCSYNC-11, F-DOCSYNC-12, F-DOCSYNC-13, F-MAS-3, F-WORKTREE-3, F-B21-9, F-B21-20, F-B21-25, the new WP-state finding | real | fixed | control-plane plan |
| F-B21-53 | real; the owner accepts it (Q10 = b) | ruled out | Task 10 |
| F-B21-14, F-B21-18, F-B21-22, F-B21-23, F-B21-60 | real; F-B21-23's Bootstrap blocker is gone | fixed | frontend plan |
| F-LOAD-2, F-MAS-1, F-B21-3 (remainder) | real | fixed | test-infrastructure plan |

---

## Stage 1 -- records (Part B)

### Task 1: Close the six stale "pending deploy" records

**Files:**
- Modify: `FINDINGS.md` (the six findings, the P0 section and the header)
- Modify (by `--fix`): `docs/history/findings/FINDINGS_ARCHIVE.md`
- Modify: `PLAYBOOK.md` (a Section 4 entry)
- Test: none. The evidence is `git` and the gate is docsync.

**Interfaces:** none.

The fix commits, all confirmed ancestors of `origin/main` on 2026-09-23:

| Finding | Fix commit(s) |
| --- | --- |
| F-B20-3 | `85e7511` (WP-8 retired the legacy stack) |
| F-B21-10 | `079c2b0c` |
| F-B21-26 | `b1fdb121` |
| F-B21-27 | `ee5ee4eb` |
| F-B21-28 | `47321b23`, completed by `b1fdb121` |
| F-B21-29 | `df28c06d`, completed by `8b37566a` |

- [x] **Step 1: Re-verify each commit is on main.** A record must not outrun its evidence.

```bash
for s in 85e7511 079c2b0c b1fdb121 ee5ee4eb 47321b23 df28c06d 8b37566a; do
  git merge-base --is-ancestor $s origin/main && echo "$s on main" || echo "$s NOT ON MAIN - STOP"
done
```

Expected: seven "on main" lines. If any says STOP, report BLOCKED and do not write that record.

- [x] **Step 2: Find each finding's completion date: the day its last fix commit first reached
  `origin/main`.**

```bash
for s in 85e7511 079c2b0c b1fdb121 ee5ee4eb 8b37566a; do
  d=$(git log --ancestry-path --merges --reverse --format=%cs "$s..origin/main" | head -1)
  [ -n "$d" ] || d=$(git log -1 --format=%cs "$s")
  echo "$s $d"
done
```

Use `b1fdb121`'s date for F-B21-26 and F-B21-28, and `8b37566a`'s for F-B21-29.

- [x] **Step 3: Rewrite each finding's status line.** Replace the
  `- [ ] **Status:** resolved locally, pending deploy` line in each of the six with the canonical form,
  keeping the rest of each body as written:

```
- [x] **Status:** resolved -- fixed by `<sha>` and deployed with it; confirmed an ancestor of `origin/main` on 2026-09-23.
**Completed:** <date from Step 2>
```

For F-B20-3, the reason reads "Bootstrap and both CDN providers were retired by `85e7511` (Batch 21
WP-8)".

*As executed (`f3942de`):* the gate refused the form above, for the reason Global Constraints
"Resolving a finding" gives. Each record was written as a bare `- [x] **Status:** resolved`, with
the same sha, dates and sentence on the line below it.

- [x] **Step 4: Leave the P0 heading true.** Once `--fix` has rotated the four P0 records out, the
  `## P0 -- Fix before next deploy` section is empty. Put one line under the heading, rather than
  deleting the heading, because other documents cite the severity levels:

```
None open. The four P0 items open until 2026-09-23 were fixed before PR #238 deployed; see the archive.
```

- [x] **Step 5: Close the Batch 22 owner check.** Done ahead of this task, in the commit that recorded
  the owner's 2026-09-23 rulings on card 3 and F-B22-8. That commit rewrote PLAYBOOK Section 3's
  Batch 22 owner-verification bullet to record both halves as done, and ticked the definition's
  owner-actions box. The Q0 answer holds the evidence. Leave the bullet and the box as they are.

  *Amended 2026-09-23:* this step first recorded only the Spotify half and kept MusicBrainz owed. Q0
  was settled before Task 1 ran, and Section 3 must stay true at every commit, so the ruling commit
  took this step over.

- [x] **Step 6: Run the gates and commit.** Follow the Global Constraints procedure. Stage
  `FINDINGS.md`, `docs/history/findings/FINDINGS_ARCHIVE.md`, `PLAYBOOK.md`, and
  `.claude/SESSION_CONTEXT.md` if `--fix` changed it. Then:

```bash
git commit -m "docs(findings): Close six records that shipped with the deploy"
```

### Task 2: File the docsync work-package gap

**Files:**
- Modify: `FINDINGS.md` and `PLAYBOOK.md`

**Interfaces:** Produces the new finding's ID, which Q4 and the control-plane plan cite. Record it in
the Section 4 entry.

- [x] **Step 1: Find the next free `F-DOCSYNC-` number.** Take the highest in use and add one:

```bash
git grep -h -o "F-DOCSYNC-[0-9]*" -- FINDINGS.md docs/history/findings/ | sort -t- -k3 -n | uniq | tail -1
```

- [x] **Step 2: File the finding under "P1 -- Next batch candidates"**, using the number from Step 1:

```
### F-DOCSYNC-<N>: a work package reads as complete on its first tagged log entry

`scripts/docsync/parser.py` `_collect_wp_numbers` counts every `WP-<n>` token in a current-batch entry heading as a completed work package, so the first commit of a multi-commit work package already makes the dashboard name the next one. `docs/history/logs/BATCH22_LOG.md` shows it happened: three `(Batch 22 WP-4)` entries landed on 2026-09-20 before WP-4 was done. Nothing went red, because DOC007 compares only against a claim someone wrote, and nobody wrote "WP-5 is next" in that window. Batch 23 WP-0 works around it by logging untagged until the package closes (owner ruling, 2026-09-23). The fix shape is Q4 of `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`.

- [ ] **Status:** open (P1). Source: Batch 23 WP-0 definition amendment and triage D, 2026-09-23.
```

- [x] **Step 3: Run the gates and commit.** Stage both files by name, then:

```bash
git commit -m "docs(findings): File the work-package state gap"
```

---

## Stage 2 -- pipeline fixes (Part C)

### Task 3: Reading a job never renews its lease (F-SWE-6, for Q1 = a)

**Files:**
- Modify: `scrobblescope/repositories.py` (`cleanup_expired_jobs`, `get_job_progress`,
  `get_job_unmatched`, `get_job_context`)
- Modify: `scrobblescope/config.py` (the comment above `JOB_TTL_SECONDS`)
- Test: `tests/test_repositories.py` (append)

**Interfaces:** No signature changes. Behaviour: only writers set `updated_at`.

- [x] **Step 1: Write the failing test.** Append to `tests/test_repositories.py`. Extend its
  `from scrobblescope.repositories import (...)` block with any of `cleanup_expired_jobs`,
  `get_job_context`, `get_job_progress` and `get_job_unmatched` it lacks.

```python
@pytest.mark.parametrize(
    "read",
    [get_job_progress, get_job_unmatched, get_job_context],
    ids=["progress", "unmatched", "context"],
)
def test_reading_a_job_does_not_renew_its_lease(read):
    """
    GIVEN a job whose last write is older than JOB_TTL_SECONDS
    WHEN a getter reads it and cleanup then runs
    THEN the job is reaped: reading is not activity (F-SWE-6).

    Before this, each getter wrote updated_at, so a polled job -- an open
    results tab, or the release-check worker asking whether it still
    exists -- never expired.
    """
    job_id = create_job(TEST_JOB_PARAMS)
    expired_time = time.time() - JOB_TTL_SECONDS - 60
    with jobs_lock:
        JOBS[job_id]["created_at"] = expired_time
        JOBS[job_id]["updated_at"] = expired_time

    assert read(job_id) is not None  # the read itself still works

    cleanup_expired_jobs()

    with jobs_lock:
        assert job_id not in JOBS
```

- [x] **Step 2: Run it to verify it fails.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_repositories.py -q -k reading_a_job_does_not_renew`
Expected: 3 failed, each on `assert job_id not in JOBS`.

- [x] **Step 3: Remove the renewal.** In `get_job_progress`, `get_job_unmatched` and `get_job_context`,
  delete the line `job["updated_at"] = time.time()`. Then replace their first docstring lines:

```python
def get_job_progress(job_id):
    """Return a shallow copy of a job's progress dict, or None if not found.

    Reading is not activity: this never renews the job's lease, so a polled
    job still expires JOB_TTL_SECONDS after its last write (F-SWE-6).
    """
```

```python
def get_job_unmatched(job_id):
    """Return a copy of a job's unmatched albums dict, or None if not found.

    Never renews the job's lease; see get_job_progress.
    """
```

In `get_job_context`, append one paragraph to the existing docstring:

```
    Never renews the job's lease; see get_job_progress. The release-check
    worker calls this to ask whether a job still exists, and that question
    must not keep the job alive.
```

Replace `cleanup_expired_jobs`'s docstring:

```python
def cleanup_expired_jobs():
    """Remove jobs whose last write is older than JOB_TTL_SECONDS.

    The lease is ``updated_at``, and only writers renew it. A getter never
    does, so an open page polling a finished job cannot keep that job, or
    an uploaded export's aggregate, in memory indefinitely (F-SWE-6).
    """
```

In `scrobblescope/config.py`, put this directly above `JOB_TTL_SECONDS = 2 * 60 * 60`:

```python
# A job expires this long after its last write (repositories.cleanup_expired_jobs).
# Reads never renew it: Batch 23 promises an uploaded export is forgotten
# within this window, and a polling tab must not extend that.
```

- [x] **Step 4: Run the tests to verify they pass.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_repositories.py tests/test_routes.py tests/services/test_release_checks.py -q`
Expected: pass.

- [x] **Step 5: Sweep the live docs for the old claim.**

```bash
git grep -n -i -e "renew" -e "touch-on-access" -e "polled job" -- '*.md' ':!docs/history' ':!docs/logarchive' ':!docs/superpowers'
```

Correct any sentence that says reading keeps a job alive. The F-SWE-6 finding body is the expected hit;
Step 6 resolves it.

- [x] **Step 6: Resolve F-SWE-6 and commit.** Use the canonical record, with the reason "getters no
  longer write `updated_at`; `repositories.cleanup_expired_jobs` reaps on the last write only". Run the
  gates, stage `scrobblescope/repositories.py`, `scrobblescope/config.py`, `tests/test_repositories.py`,
  `FINDINGS.md`, the findings archive, `PLAYBOOK.md` and `.claude/SESSION_CONTEXT.md`, then:

```bash
git commit -m "fix(jobs): Stop a read from renewing a job's lease"
```

### Task 4: `as_cache_row` writes a Spotify id only into the Spotify column (F-B22-7, part 1)

**Files:**
- Modify: `scrobblescope/enrichment.py` (`AlbumMetadata.as_cache_row`)
- Test: `tests/services/test_enrichment.py`

**Interfaces:** Produces `AlbumMetadata.as_cache_row(artist_norm, album_norm) -> tuple`, a 9-tuple whose
index 2 (`spotify_id`) is `album_id` when `provider == "spotify"` and `None` otherwise. Tasks 5 and 6
rely on this.

**Why this change comes first.** The method currently writes a Deezer album id into the `spotify_id`
column. The live Deezer path writes `None` there, and
`tests/services/test_orchestrator_process_albums.py` pins that at the row's index 2. So routing Deezer
through the method unchanged would corrupt the cache. The method's own two tests pin the wrong value.
They are the only existing assertions this task changes, and the finding requires changing them.

- [x] **Step 1: Change the two pinned assertions, and add the Spotify case.** In
  `tests/services/test_enrichment.py`:

  In `test_album_metadata_carries_its_provider_and_url`, the expected tuple's third element changes
  from `"6237061",` to:

```python
        None,
```

  In `test_cache_row_matches_what_the_persistence_layer_unpacks`, replace
  `assert row[2] == meta.album_id` with:

```python
    # The spotify_id column holds a Spotify id only; a Deezer row carries its
    # id in provider_album_id (row[7]), as the live fallback always wrote it.
    assert row[2] is None
```

  Append:

```python
def test_cache_row_puts_a_spotify_album_id_in_the_spotify_column():
    """A Spotify row keeps its id in both spotify_id and provider_album_id."""
    meta = AlbumMetadata(
        provider="spotify",
        album_id="sp1",
        url="https://open.spotify.com/album/sp1",
        release_date="2025-01-01",
        image_url=None,
        track_durations={},
    )
    row = meta.as_cache_row("artist", "album")

    assert row[2] == "sp1"
    assert (row[6], row[7], row[8]) == (
        "spotify",
        "sp1",
        "https://open.spotify.com/album/sp1",
    )
```

- [x] **Step 2: Run the tests to verify they fail.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/services/test_enrichment.py -q`
Expected: the two edited tests fail on index 2, and the new Spotify test passes. It passes already
because the defect only affects non-Spotify providers, which is the point.

- [x] **Step 3: Fix the method.** In `scrobblescope/enrichment.py` `as_cache_row`, replace the third
  tuple element `self.album_id,` (the one directly after `album_norm,`) with:

```python
            # The legacy spotify_id column holds a Spotify id only. Any other
            # provider writes None there -- as the live Deezer fallback always
            # has -- and keeps its own id in provider_album_id below.
            self.album_id if self.provider == "spotify" else None,
```

  In the docstring, replace the sentence beginning "the nine-element form is the provider-aware one"
  with:

```
        it. The nine-element form is the provider-aware one: ``spotify_id``
        carries ``album_id`` only for a Spotify row, and ``provider_album_id``
        always carries the id the provider itself issued.
```

- [x] **Step 4: Run the tests to verify they pass.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/services/test_enrichment.py tests/services/test_orchestrator_process_albums.py -q`
Expected: pass.

- [x] **Step 5: Run the gates and commit.** The count rises by 1. The commit body names the two edited
  assertions:

```bash
git commit -m "fix(enrichment): Keep a Deezer id out of the Spotify column"
```

### Task 5: The Spotify payload is translated once, in `spotify.py` (F-B22-7, part 2)

**Files:**
- Modify: `scrobblescope/spotify.py` (add `album_metadata_from_details`; `enrich_albums` uses it)
- Modify: `scrobblescope/orchestrator/__init__.py` (import it from `scrobblescope.spotify`, and add it
  to `__all__` in alphabetical position)
- Modify: `scrobblescope/orchestrator/_details.py` (the "Extract cacheable fields" loop, the
  `normalize_track_name` import and the module docstring)
- Modify: `scrobblescope/orchestrator/_deezer_fallback.py` (the inline 9-tuple)
- Test: `tests/services/test_spotify_service.py` (append) and
  `tests/services/test_orchestrator_process_albums.py` (append)

**Interfaces:**
- Consumes: Task 4's `as_cache_row`.
- Produces: `spotify.album_metadata_from_details(spotify_id: str, details: dict) -> AlbumMetadata`,
  re-exported on the orchestrator facade.

**What changes for the cache.** Spotify rows are persisted as 9-tuples, so `provider_url` now holds the
album's Spotify URL instead of `NULL`. `provider` and `provider_album_id` hold the same values the
6-tuple default already wrote. `_batch_persist_metadata` keeps accepting 6-tuples: that is a tolerant
input path, not an unused call (global rule 6).

- [x] **Step 1: Write the failing translation tests.** Append to `tests/services/test_spotify_service.py`,
  and add `album_metadata_from_details` to its `from scrobblescope.spotify import (...)` block:

```python
def test_album_metadata_from_details_translates_one_payload():
    """One Spotify album object becomes the provider contract, whole."""
    from scrobblescope.domain import normalize_track_name
    from scrobblescope.enrichment import AlbumMetadata

    details = {
        "release_date": "1977-02-04",
        "images": [
            {"url": "https://i.scdn.co/cover-large.jpg"},
            {"url": "https://i.scdn.co/cover-small.jpg"},
        ],
        "external_urls": {"spotify": "https://open.spotify.com/album/sp1"},
        "tracks": {
            "items": [
                {"name": "Dreams - 2004 Remaster", "duration_ms": 257800},
                {"name": "Songbird", "duration_ms": 200000},
            ]
        },
    }

    assert album_metadata_from_details("sp1", details) == AlbumMetadata(
        provider="spotify",
        album_id="sp1",
        url="https://open.spotify.com/album/sp1",
        release_date="1977-02-04",
        image_url="https://i.scdn.co/cover-large.jpg",
        track_durations={
            normalize_track_name("Dreams - 2004 Remaster"): 257,
            normalize_track_name("Songbird"): 200,
        },
    )


@pytest.mark.parametrize("images", [None, []], ids=["no-key", "empty"])
def test_album_metadata_from_details_degrades_field_by_field(images):
    """A sparse payload yields defaults, never an exception (global rule 6)."""
    details = {} if images is None else {"images": images}

    meta = album_metadata_from_details("sp2", details)

    assert meta.url == "https://open.spotify.com/album/sp2"
    assert meta.release_date == ""
    assert meta.image_url is None
    assert meta.track_durations == {}
```

- [x] **Step 2: Write the failing persistence test.** Append to
  `tests/services/test_orchestrator_process_albums.py`:

```python
@pytest.mark.asyncio
async def test_process_albums_persists_a_spotify_row_through_the_contract():
    """
    GIVEN a cache miss that Spotify finds and details
    WHEN process_albums persists it
    THEN the row is the provider contract's nine-element form, so the
    Spotify URL is stored rather than left NULL (F-B22-7).
    """
    from scrobblescope.domain import normalize_track_name

    job_id = create_job(TEST_JOB_PARAMS)
    filtered = {
        ("artist", "album"): {
            "play_count": 20,
            "track_counts": {"track one": 5},
            "original_artist": "Artist",
            "original_album": "Album",
        }
    }

    mock_conn = AsyncMock()
    mock_session = AsyncMock()
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(
            "scrobblescope.orchestrator._get_db_connection",
            new_callable=AsyncMock,
            return_value=mock_conn,
        ),
        patch(
            "scrobblescope.orchestrator._batch_lookup_metadata",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "scrobblescope.orchestrator._batch_persist_metadata",
            new_callable=AsyncMock,
        ) as mock_persist,
        patch(
            "scrobblescope.orchestrator.fetch_spotify_access_token",
            new_callable=AsyncMock,
            return_value="tok",
        ),
        patch(
            "scrobblescope.orchestrator.create_optimized_session",
            return_value=mock_session_ctx,
        ),
        patch(
            "scrobblescope.orchestrator.search_for_spotify_album_id",
            new_callable=AsyncMock,
            return_value="sp1",
        ),
        patch(
            "scrobblescope.orchestrator.fetch_spotify_album_details_batch",
            new_callable=AsyncMock,
            return_value={
                "sp1": {
                    "release_date": "2025-01-01",
                    "images": [{"url": "https://img.example.com/a.jpg"}],
                    "tracks": {"items": [{"name": "Track One", "duration_ms": 240000}]},
                }
            },
        ),
    ):
        await process_albums(job_id, filtered, 2025, "playcount", "same")

    mock_persist.assert_awaited_once()
    (row,) = mock_persist.call_args[0][1]
    assert row == (
        "artist",
        "album",
        "sp1",
        "2025-01-01",
        "https://img.example.com/a.jpg",
        {normalize_track_name("Track One"): 240},
        "spotify",
        "sp1",
        "https://open.spotify.com/album/sp1",
    )
```

- [x] **Step 3: Run them to verify they fail.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/services/test_spotify_service.py tests/services/test_orchestrator_process_albums.py -q -k "album_metadata_from_details or through_the_contract"`
Expected:
- the translation tests fail with `ImportError: cannot import name 'album_metadata_from_details'`,
  which is a collection error for that file;
- the persistence test fails, because the live row has 6 elements, not 9.

- [x] **Step 4: Add the translation.** In `scrobblescope/spotify.py`, directly above
  `async def enrich_albums`:

```python
def album_metadata_from_details(spotify_id, details):
    """Translate one Spotify album object into the provider contract.

    The one place the application reads Spotify's album JSON. The
    orchestrator's detail phase files what this returns and never drills into
    the payload itself (global rule 4, F-B22-7). A sparse payload degrades
    field by field -- no images gives ``image_url=None``, no external URL
    falls back to the album's canonical URL -- rather than raising.

    Args:
        spotify_id: The album id Spotify issued.
        details: One album object from Get Album or Get Several Albums.

    Returns:
        AlbumMetadata with ``provider="spotify"`` and track durations in
        whole seconds, keyed by ``normalize_track_name``.
    """
    images = details.get("images") or [{}]
    return AlbumMetadata(
        provider="spotify",
        album_id=spotify_id,
        url=details.get("external_urls", {}).get(
            "spotify", f"https://open.spotify.com/album/{spotify_id}"
        ),
        release_date=details.get("release_date", ""),
        image_url=images[0].get("url"),
        track_durations={
            normalize_track_name(t.get("name", "")): t.get("duration_ms", 0) // 1000
            for t in details.get("tracks", {}).get("items", [])
        },
    )
```

  In `enrich_albums`, replace everything from `images = details.get("images") or [{}]` through the
  closing `)` of the `AlbumMetadata(...)` call with:

```python
            matched[key] = album_metadata_from_details(spotify_id, details)
```

- [x] **Step 5: Re-export it on the facade.** In `scrobblescope/orchestrator/__init__.py`:
  - add `album_metadata_from_details,` to the `from scrobblescope.spotify import (...)` block, in
    alphabetical position;
  - add `"album_metadata_from_details",` to `__all__`, also alphabetically.

- [x] **Step 6: File, don't parse, in the detail phase.** In `scrobblescope/orchestrator/_details.py`:
  1. Delete `from scrobblescope.domain import normalize_track_name`.
  2. In the module docstring, change `(``fetch_spotify_album_details_batch``, ``set_job_progress``)` to
     `(``fetch_spotify_album_details_batch``, ``album_metadata_from_details``, ``set_job_progress``)`.
  3. Replace the whole `# Extract cacheable fields, promote to cache_hits` loop with:

```python
    # Translate at the edge: spotify.album_metadata_from_details owns the
    # payload's shape, and this phase only files the result (F-B22-7).
    for spotify_id, album_details in all_album_details.items():
        if not album_details:
            continue
        original_data = spotify_id_to_original_data.get(spotify_id)
        if not original_data:
            continue
        key = spotify_id_to_key[spotify_id]
        metadata = _orchestrator.album_metadata_from_details(spotify_id, album_details)

        cache_hits[key] = {
            "cached": {
                "spotify_id": spotify_id,
                "release_date": metadata.release_date,
                "album_image_url": metadata.image_url,
                "track_durations": metadata.track_durations,
            },
            "original": original_data,
        }
        new_metadata_rows.append(metadata.as_cache_row(key[0], key[1]))
```

- [x] **Step 7: Route the Deezer row through the contract.** In
  `scrobblescope/orchestrator/_deezer_fallback.py`, replace the whole
  `new_metadata_rows.append((key[0], key[1], None, ... metadata.url,))` call with:

```python
            new_metadata_rows.append(metadata.as_cache_row(key[0], key[1]))
```

  Since Task 4, that tuple is identical to the one it replaces.

- [x] **Step 8: Run the tests to verify they pass.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/services -q`
Expected: pass. That includes the unchanged Deezer row test, which pins `row[2] is None` and the three
provider columns.

- [x] **Step 9: Run the gates and commit.** The count rises by 4 (one test, one parametrized pair, one
  process test). No existing assertion changes.

```bash
git commit -m "refactor(enrichment): Translate the Spotify payload in spotify.py"
```

### Task 6: Retire the unused `enrich_albums` (F-B22-7, part 3, for Q2 = a)

**Files:**
- Modify: `scrobblescope/spotify.py` (delete `enrich_albums`)
- Modify: `scrobblescope/orchestrator/__init__.py` (drop its import and its `__all__` entry)
- Modify: `tests/services/test_spotify_service.py` (delete the `enrich_albums` section and its import)
- Modify: `tests/services/test_orchestrator_fetch_spotify.py` (delete
  `test_enrich_albums_is_exposed_on_the_orchestrator_facade` and both of its imports)
- Modify: `FINDINGS.md` (resolve F-B22-7) and the findings archive

**Interfaces:** Removes `spotify.enrich_albums` and `orchestrator.enrich_albums`. Nothing in the
application calls either.

**Why delete rather than wire up.** The live path already does what `enrich_albums` does, through
`_run_spotify_search_phase` and `_run_spotify_batch_detail_phase`, and adds the per-phase progress the
loading page shows. `enrich_albums` has no progress hooks. Wiring it would mean adding them, and would
move 22 existing test patch targets off the orchestrator facade that Batch 22 WP-0 set up. After Task
5, the contract the function stood for -- a provider hands back `AlbumMetadata`, and the orchestrator
never parses provider JSON -- holds on the live path without it.

- [x] **Step 1: Confirm nothing but tests call it.**

```bash
git grep -n "enrich_albums" -- '*.py'
```

Expected hits only:
- its definition in `spotify.py`;
- the facade import and `__all__` entry;
- `test_spotify_service.py`, meaning the four tests and the import;
- `test_orchestrator_fetch_spotify.py`, meaning the facade test and two imports.

Any other hit means a caller exists: stop and report NEEDS_CONTEXT.

- [x] **Step 2: Delete it and its tests.** Remove from `tests/services/test_spotify_service.py`:
  - the banner comment `# enrich_albums (Batch 22 WP-1 Task 3: the provider-contract seam)` and the
    `###` rule under it;
  - `test_enrich_albums_empty_misses_makes_no_request`, `test_enrich_albums_returns_matched_and_unmatched`,
    `test_enrich_albums_marks_unmatched_when_detail_lookup_misses` and
    `test_enrich_albums_handles_missing_cover_art`;
  - `enrich_albums,` from the import block.

  In `tests/services/test_orchestrator_fetch_spotify.py`, remove the facade test, `enrich_albums,` from
  the `from scrobblescope.orchestrator import (...)` block, and the line
  `from scrobblescope.spotify import enrich_albums as spotify_enrich_albums`.

  Delete `async def enrich_albums(...)` whole from `scrobblescope/spotify.py`, and delete its two
  references from the facade.

- [x] **Step 3: Verify.**

Run: `git grep -n "enrich_albums" -- '*.py'`, then
`"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/services -q`.
Expected: no `.py` hits, and the suite passes. The count falls by 5.

- [x] **Step 4: Resolve F-B22-7 and commit.** The canonical record's reason:

  > "the Spotify payload is translated only in `spotify.album_metadata_from_details`; every metadata row
  > is built by `AlbumMetadata.as_cache_row`, whose Deezer rows no longer carry an id in `spotify_id`;
  > the unused `enrich_albums` and its tests are removed".

  The commit body names the five deleted tests. Then:

```bash
git commit -m "refactor(spotify): Remove enrich_albums, which nothing called"
```

### Task 7: Both pipelines end a crash as `internal_error` (F-SWE-5)

**Files:**
- Modify: `scrobblescope/errors.py` (add `internal_error`)
- Modify: `scrobblescope/heatmap.py` (`_report_heatmap_failure` and the `heatmap_task` docstring)
- Modify: `scrobblescope/orchestrator/__init__.py` (a new `_report_album_failure`; the `background_task`
  docstring and its `on_run_error`)
- Modify: `static/js/loading.js` (`showFailure`)
- Modify: `scripts/dev/_frontend_gate_pipeline.py` (`_exercise_pipeline_state_machines`)
- Test: `tests/test_heatmap.py` and `tests/services/test_orchestrator_fetch_and_process.py` (append)

**Interfaces:**
- Produces: the `ERROR_CODES["internal_error"]` entry, with `source: "internal"` and
  `retryable: False`.
- Produces: `orchestrator._report_album_failure(job_id, username, year)`.
- Batch 23 WP-3 publishes export failures through these same terminal states.

**Corrections to the foundation plan's Task 11 sketch**, from triage C:
- `tests/test_errors.py` does not exist.
- No existing test pins `lastfm_unavailable` from the outer handler. The only such assertion is on the
  inner, status-based path, and it stays. So this task **adds** tests and edits none.

**A defect triage missed.** `loading.js` `showFailure` renders `Source: Spotify` for every source that
is not `lastfm`. Without the fix below, an `internal_error` would tell the user Spotify failed, and so
would WP-1's `spotify_export` source.

- [x] **Step 1: Write the failing tests.** Append to `tests/test_heatmap.py`, inside `class TestErrorCode`:

```python
    def test_internal_error_exists(self):
        """internal_error is registered for faults that are ours (F-SWE-5)."""
        from scrobblescope.errors import ERROR_CODES

        code = ERROR_CODES.get("internal_error")
        assert code is not None, "internal_error not in ERROR_CODES"
        assert code["source"] == "internal"
        assert code["retryable"] is False
        assert "{username}" not in code["message"]
```

  Append inside `class TestHeatmapTask`:

```python
    def test_unhandled_crash_publishes_internal_error(self):
        """A crash that escapes the pipeline ends the job as internal_error,
        not as a Last.fm outage that never happened (F-SWE-5)."""
        from scrobblescope.repositories import create_job, get_job_progress
        from tests.helpers import TEST_JOB_PARAMS

        job_id = create_job(TEST_JOB_PARAMS)
        with (
            patch("scrobblescope.heatmap.release_job_slot"),
            patch(
                "scrobblescope.heatmap._fetch_and_process_heatmap",
                new_callable=AsyncMock,
                side_effect=ZeroDivisionError("ours"),
            ),
        ):
            heatmap_task(job_id, "user")

        progress = get_job_progress(job_id)
        assert progress["error"] is True
        assert progress["error_code"] == "internal_error"
        assert progress["error_source"] == "internal"
        assert progress["retryable"] is False
```

  Append to `tests/services/test_orchestrator_fetch_and_process.py`:

```python
def test_background_task_crash_publishes_internal_error():
    """
    GIVEN _fetch_and_process raises something no inner handler classified
    WHEN background_task runs it
    THEN the job ends as internal_error, so a polling page stops waiting
    (F-SWE-5: before this the album backstop only logged).
    """
    job_id = create_job(TEST_JOB_PARAMS)

    with (
        patch(
            "scrobblescope.orchestrator._fetch_and_process",
            new_callable=AsyncMock,
            side_effect=ZeroDivisionError("ours"),
        ),
        patch("scrobblescope.orchestrator.release_job_slot"),
    ):
        background_task(job_id, "flounder14", 2025, "playcount", "same")

    progress = get_job_progress(job_id)
    assert progress["error"] is True
    assert progress["error_code"] == "internal_error"
    assert progress["error_source"] == "internal"
```

- [x] **Step 2: Run them to verify they fail.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_heatmap.py tests/services/test_orchestrator_fetch_and_process.py -q -k "internal_error"`
Expected: 3 failed.
- The registry test fails on `code is not None`.
- The heatmap test fails because `error_code` is `lastfm_unavailable`.
- The album test fails because `progress["error"]` is not True: nothing published a state.

- [x] **Step 3: Register the code.** In `scrobblescope/errors.py`, add as the last entry of
  `ERROR_CODES`:

```python
    # A fault that escaped every inner classifier is ours, not an upstream's.
    # Both background entry points publish it (F-SWE-5). Not retryable: an
    # immediate identical retry meets the same bug.
    "internal_error": {
        "source": "internal",
        "retryable": False,
        "message": "Something went wrong on our side and the search stopped. Please start a new search.",
    },
```

- [x] **Step 4: The heatmap reaction.** Replace `_report_heatmap_failure` in `scrobblescope/heatmap.py`:

```python
def _report_heatmap_failure(job_id, username):
    """Log the crash and publish this pipeline's terminal state.

    Called from inside the helper's ``except`` block, so ``logging.exception``
    still sees the active exception. A fault that reaches this backstop is
    ours: ``internal_error`` says so, where ``lastfm_unavailable`` blamed an
    upstream that never failed (F-SWE-5). The inner, status-based Last.fm
    path inside ``_fetch_and_process_heatmap`` still publishes its own code.
    """
    logging.exception(f"Unhandled error in heatmap task for {username}")
    set_job_error(job_id, "internal_error", username=username)
```

  In `heatmap_task`'s docstring, replace the last sentence ("What stays here is local: ... F-SWE-5.")
  with:

```
    ``worker.run_coroutine_in_new_loop``. What stays here is local: a failed
    run is reported as ``internal_error`` rather than raised, the same answer
    the album entry point gives (F-SWE-5).
```

- [x] **Step 5: The album reaction.** In `scrobblescope/orchestrator/__init__.py`, add directly above
  `def background_task(`:

```python
def _report_album_failure(job_id, username, year):
    """Log the crash and publish this pipeline's terminal state.

    Called from inside the helper's ``except`` block, so ``logging.exception``
    still sees the active exception. Publishes the same ``internal_error``
    the heatmap entry point does: two entry points, one answer (F-SWE-5).
    Before this, the album backstop only logged, and a page polling the job
    waited on a job that would never finish.
    """
    logging.exception(f"Unhandled error in background task for {username}/{year}")
    set_job_error(job_id, "internal_error", username=username)
```

  Replace `background_task`'s whole docstring with:

```python
    """Run the album pipeline on this thread, in a loop the worker owns.

    The build-run-close-release protocol lives in
    ``worker.run_coroutine_in_new_loop``. What stays here is the reaction to
    a failed run: ``_report_album_failure`` logs it and publishes
    ``internal_error``. Upstream failures are classified deeper in, inside
    ``_fetch_and_process``, so this backstop only sees faults that are ours.
    """
```

  Replace its `on_run_error=lambda _exc: logging.exception(...)` argument, all three lines, with:

```python
        on_run_error=lambda _exc: _report_album_failure(job_id, username, year),
```

- [x] **Step 6: Name only a source the page knows.** In `static/js/loading.js`, replace `showFailure`:

```js
/** Upstream names a failure may cite; any other source shows no source line. */
const ERROR_SOURCE_LABELS = { lastfm: 'Last.fm', spotify: 'Spotify' };

/** Render a job failure and name its upstream source when there is one. */
function showFailure(message, source) {
  errorDetected = true;
  progressBar?.classList.add('is-error');
  errorContainer?.classList.remove('hidden');
  if (errorText) errorText.textContent = message;

  if (errorSource) {
    // A fault that is ours ('internal') is not blamed on an upstream.
    const label = ERROR_SOURCE_LABELS[source];
    errorSource.textContent = label ? `Source: ${label}` : '';
    errorSource.classList.toggle('hidden', !label);
  }
}
```

- [x] **Step 7: Pin the label in the gate.** In `scripts/dev/_frontend_gate_pipeline.py`
  `_exercise_pipeline_state_machines`, directly after the album block's
  `page.locator("#retry-button").wait_for(state="visible")` and its `if not page.url.startswith(...)`
  check, insert:

```python
    source_line = page.locator("#error-source")
    source_text = source_line.inner_text().strip()
    if source_text != "Source: Last.fm":
        failures.append(
            f"album rate-limit failure named its source {source_text!r}, "
            "not 'Source: Last.fm'"
        )
    # internal_error's source is ours, not an upstream's: the line must hide
    # rather than fall through to 'Spotify' (F-SWE-5).
    page.evaluate("showFailure('gate probe', 'internal')")
    if source_line.is_visible():
        failures.append("an internal failure still showed an upstream source line")
```

- [x] **Step 8: Run the tests and the gate.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_heatmap.py tests/services/test_orchestrator_fetch_and_process.py -q`
Expected: pass.

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/python.exe" scripts/dev/frontend_gate.py`
Expected: exit 0.

Then prove the new gate lines can fail. Temporarily revert `showFailure` to its old ternary, re-run the
gate, and confirm it fails with "an internal failure still showed an upstream source line". Restore the
fix and re-run to green. Record both runs in the report.

- [x] **Step 9: Resolve F-SWE-5 and commit.** The canonical record's reason:

  > "both entry points publish `internal_error` from their outer handler (`heatmap._report_heatmap_failure`,
  > `orchestrator._report_album_failure`); `loading.js` names only a known upstream".

  The count rises by 3. No existing test changes. Then:

```bash
git commit -m "fix(jobs): Publish one honest terminal state for both pipelines"
```

### Task 8: The year gate reads the UTC calendar (F-B21-6)

**Files:**
- Modify: `scrobblescope/routes/__init__.py` (a new `_current_year`, and `inject_current_year`)
- Modify: `scrobblescope/routes/album_flow.py` (its two `datetime.now().year` sites, and the now-unused
  import)
- Test: `tests/test_routes.py` (append)

**Interfaces:** Produces `routes._current_year() -> int`, which `album_flow` reads through its existing
`_routes` module reference. This must land **before WP-4**, whose export route takes its year through
the same validator.

**Why a helper.** There are three identical sites, so the rule of three is met. Global rule 3 asks for
the abstraction at the third occurrence, not before.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_routes.py`:

```python
def test_current_year_reads_the_utc_calendar():
    """
    GIVEN a host clock still on 31 December while UTC is already on 1 January
    WHEN the year gate asks for the current year
    THEN it gets the UTC year, the calendar the fetch window is built in
    (F-B21-6). The two readings differ, so a naive read fails this test.
    """
    from datetime import datetime as real_datetime

    from scrobblescope import routes

    class _Clock(real_datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return real_datetime(2026, 12, 31, 19, 30)
            return real_datetime(2027, 1, 1, 0, 30, tzinfo=tz)

    with patch("scrobblescope.routes.datetime", _Clock):
        assert routes._current_year() == 2027


def test_results_loading_year_gate_uses_the_utc_year(client):
    """The submit-path gate's upper bound is routes._current_year()."""
    with (
        patch("scrobblescope.routes._current_year", return_value=2024),
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert b"Year must be between 2002 and 2024." in response.data
```

- [ ] **Step 2: Run them to verify they fail.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_routes.py -q -k "utc"`
Expected: 2 failed.
- The first fails with `AttributeError`: no `_current_year`.
- The second fails the same way at `patch`, since the target is missing.

- [ ] **Step 3: Add the helper.** In `scrobblescope/routes/__init__.py`:
  - change `from datetime import datetime` to `from datetime import datetime, timezone`;
  - add, directly above `inject_current_year`:

```python
def _current_year():
    """Return the current year in UTC, the calendar the fetch window uses.

    The orchestrator builds each year's window from UTC midnights, so a gate
    reading the host's local clock would disagree with it for the hours
    around New Year on any host not running UTC (F-B21-6). One helper, because
    three call sites asked the same question.
    """
    return datetime.now(timezone.utc).year
```

  Change `inject_current_year`'s body to `return {"current_year": _current_year()}`.

- [ ] **Step 4: Use it in `album_flow.py`.**
  - `year = int(request.values.get("year", datetime.now().year))` becomes
    `year = int(request.values.get("year", _routes._current_year()))`.
  - `current_year = datetime.now().year` becomes `current_year = _routes._current_year()`.
  - Delete `from datetime import datetime`, which no longer has a use.
  - Confirm with `git grep -n "datetime" scrobblescope/routes/album_flow.py`, which should find no hit.

- [ ] **Step 5: Run the tests to verify they pass.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_routes.py -q`
Expected: pass.

- [ ] **Step 6: Resolve F-B21-6 and commit.** The canonical record's reason: "every year gate reads
  `routes._current_year()`, which uses `datetime.now(timezone.utc)`". The count rises by 2. Then:

```bash
git commit -m "fix(routes): Read the year gate from the UTC calendar"
```

### Task 9: The capacity refusal states the configured cap (F-LOAD-1)

**Files:**
- Modify: `scrobblescope/routes/__init__.py` (a new `_capacity_message`, and an import from
  `scrobblescope.config`)
- Modify: `scrobblescope/routes/album_flow.py` and `scrobblescope/routes/heatmap_flow.py` (their two
  refusal strings)
- Modify: `.claude/SESSION_CONTEXT.md` Section 4 (`routes/__init__.py` gains a `config` edge; Anti-Pattern 2)
- Test: `tests/test_routes.py` (append)

**Interfaces:** Produces `routes._capacity_message() -> str`.

**Why no occupancy counter.** Triage C proposed an "N/cap in use" counter. The message is shown only
when `acquire_job_slot()` has just failed, and at that moment every slot is taken, so the count would
always read cap/cap. What the finding needs is the cap itself, read from configuration rather than
written as a literal.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_routes.py`:

```python
def test_album_capacity_refusal_states_the_configured_cap(client):
    """The cap comes from MAX_ACTIVE_JOBS, never a literal (F-LOAD-1)."""
    with (
        patch("scrobblescope.routes.MAX_ACTIVE_JOBS", 7),
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
    ):
        response = client.post("/results_loading", data=VALID_FORM_DATA)

    assert b"Too many requests in progress" in response.data
    assert b"all 7 search slots are busy" in response.data


def test_heatmap_capacity_refusal_states_the_configured_cap(client):
    """The heatmap's 429 carries the same configured cap (F-LOAD-1)."""
    with (
        patch("scrobblescope.routes.MAX_ACTIVE_JOBS", 7),
        patch(
            "scrobblescope.routes.run_async_in_thread",
            return_value={"exists": True, "registered_year": None},
        ),
        patch("scrobblescope.routes.acquire_job_slot", return_value=False),
    ):
        response = client.post("/heatmap_loading", data={"username": "flounder14"})

    assert response.status_code == 429
    assert "all 7 search slots are busy" in response.get_json()["message"]
```

- [ ] **Step 2: Run them to verify they fail.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_routes.py -q -k "configured_cap"`
Expected: 2 failed, with `AttributeError`: `scrobblescope.routes` has no `MAX_ACTIVE_JOBS`.

- [ ] **Step 3: Add the helper.** In `scrobblescope/routes/__init__.py`, add
  `from scrobblescope.config import MAX_ACTIVE_JOBS` in alphabetical position among the `scrobblescope`
  imports, and add, after `_current_year`:

```python
def _capacity_message():
    """Return the refusal shown when every job slot is busy (F-LOAD-1).

    The cap is MAX_ACTIVE_JOBS as configured, never a literal: a deployment
    that overrides the variable shows its own capacity, and a change to the
    default cannot leave this text stale. There is no occupancy count,
    because the message only appears when every slot is taken.
    """
    return (
        f"Too many requests in progress: all {MAX_ACTIVE_JOBS} search slots "
        "are busy. Please try again in a moment."
    )
```

- [ ] **Step 4: Use it at both sites.**
  - In `album_flow.py`, `error="Too many requests in progress. Please try again in a moment.",` becomes
    `error=_routes._capacity_message(),`.
  - In `heatmap_flow.py`, `"message": "Too many requests in progress. Please try again in a moment.",`
    becomes `"message": _routes._capacity_message(),`.

- [ ] **Step 5: Update the dependency graph.** In `.claude/SESSION_CONTEXT.md` Section 4, the
  `routes/__init__.py` line gains `config`:

```
routes/__init__.py     <- config, lastfm, repositories, spotify, unmatched, utils, worker; routes/album_flow, routes/api, routes/heatmap_flow, routes/pages (imported last, for re-export)
```

- [ ] **Step 6: Run the tests to verify they pass.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/test_routes.py -q`
Expected: pass, including the unchanged `test_results_loading_capacity_exceeded_returns_error`, which
matches the "Too many requests" substring the new text keeps.

- [ ] **Step 7: Resolve F-LOAD-1 and commit.** The canonical record's reason: "both refusals read
  `routes._capacity_message()`, which states the configured `MAX_ACTIVE_JOBS`". The count rises by 2.
  The frontend gate runs, because `templates/index.html` renders the album message. Then:

```bash
git commit -m "fix(routes): State the configured cap when every slot is busy"
```

### Task 11: Release checks run without the cache DB (F-B22-8)

Added by the owner on 2026-09-23, after Q0's runs; see "Owner answers". It runs after Task 9 and
before Stage 3, in its own commit.

**Files:**
- Modify: `scrobblescope/release_checks.py` (`run_release_checks`, `_check_candidate`)
- Test: `tests/services/test_release_checks.py` (replace one test, add one)

**Behaviour change.** With no cache connection the worker still checks the page's candidates against
MusicBrainz. It reads no cached finding, persists nothing, and closes no connection. Everything else is
unchanged: the job ends `done`, the per-result outcomes are the same, and the shared one-request-per-
second limiter still paces the requests. On Fly.io the DB wakes with the app, so only local development
reaches this branch.

**The one edited test.** `test_run_release_checks_marks_skipped_without_a_db_connection` asserts the
old behaviour (status `skipped`, no request made). The finding reverses it, so the test is replaced,
not kept alongside. Name it in the commit body.

- [ ] **Step 1: Replace the test and add the adversarial one.** In
  `tests/services/test_release_checks.py`, replace
  `test_run_release_checks_marks_skipped_without_a_db_connection` with:

```python
@pytest.mark.asyncio
async def test_run_release_checks_runs_without_a_db_connection(caplog):
    """
    GIVEN the cache DB is unreachable
    WHEN the worker runs
    THEN it still asks MusicBrainz and records the outcome on the open job,
    persisting nothing: the cache is how findings are reused, not a
    precondition for showing one (F-B22-8).
    """
    job_id = _job_with(results=[_result("Radiohead", "OK Computer")])
    lookup = AsyncMock(return_value=("rg-1", "1997-05-21"))
    persist = AsyncMock()
    with (
        caplog.at_level(logging.INFO),
        _worker_patches(lookup, conn=None, persist=persist),
    ):
        await run_release_checks(job_id)

    lookup.assert_awaited_once()
    persist.assert_not_awaited()
    assert get_job_progress(job_id)["stats"]["release_check"] == {
        "status": "done",
        "checked": 1,
        "total": 1,
        "moved_out": 1,
        "moved_in": 0,
    }
    result = get_job_context(job_id)["results"][0]
    assert result["release_check"] == "moved_out"
    assert result["original_release_date"] == "1997-05-21"
    assert "without the cache DB" in caplog.text


@pytest.mark.asyncio
async def test_run_release_checks_without_a_db_connection_survives_a_lookup_error():
    """
    GIVEN no cache connection and MusicBrainz raising part-way through
    WHEN the worker unwinds
    THEN the job still ends "done" and nothing tries to close a connection
    that was never opened.
    """
    job_id = _job_with(results=[_result("Radiohead", "OK Computer")])
    lookup = AsyncMock(side_effect=RuntimeError("boom"))
    with _worker_patches(lookup, conn=None):
        await run_release_checks(job_id)

    assert get_job_progress(job_id)["stats"]["release_check"]["status"] == "done"
```

- [ ] **Step 2: Run them to verify they fail.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/services/test_release_checks.py -q -k "without_a_db_connection"`
Expected: the first fails (status `skipped`, lookup never awaited); the second fails (status `skipped`,
not `done`).

- [ ] **Step 3: Run without the connection.** In `run_release_checks`, replace the `if not conn:`
  block with a log line only, and guard the three uses of `conn`:

```python
    conn = await _get_db_connection()
    if not conn:
        # The page that is open still gets its corrections; only their reuse
        # by the next job is lost. On Fly.io the DB wakes with the app, so
        # this branch is reached in local development only (F-B22-8).
        logging.info(
            "Release checks running without the cache DB: "
            "findings will not be saved."
        )

    state = _state(STATUS_RUNNING)
    try:
        cached = await _lookup_cached(conn, candidates) if conn else {}
```

  In the `finally`, close the connection only `if conn:`, keeping the existing `try`/`except` around
  `conn.close()`. In `_check_candidate`, wrap the persist `try`/`except` in `if conn:`, and change its
  leading comment to say a finding is persisted per check *when a connection exists*. Update the
  `run_release_checks` docstring's failure-mode sentence if it names the skip.

- [ ] **Step 4: Run the file to verify it passes.**

Run: `"C:/Users/peter/Python Projects/ScrobbleScope/.venv/Scripts/pytest.exe" tests/services/test_release_checks.py -q`
Expected: pass. `test_run_release_checks_closes_the_connection_when_a_lookup_raises` still passes
unchanged, which proves the connected path still closes.

- [ ] **Step 5: Resolve F-B22-8 and commit.** The canonical record's reason: "`run_release_checks` runs
  its candidates without a cache connection and skips only the cache read, the persist and the close".
  The count rises by 1: one test replaced, one added. The frontend gate does not run: no template or
  asset changes. Then:

```bash
git commit -m "fix(release-checks): Check releases even when the cache is down"
```

---

## Stage 3 -- the owner's rulings

### Task 10: Write each ruling into its finding

Runs after the owner answers. The records below are written for the recommended answers. A different
answer changes that finding's record and nothing else.

**Files:** `FINDINGS.md`, the findings archive (by `--fix`), `PLAYBOOK.md`, and this plan's rulings
table.

- [x] **Step 1: Mark this plan's rulings table** with each answer and its date. Done 2026-09-23 in
  "Owner answers, 2026-09-23" above.
- [ ] **Step 1b: Record F-B21-53 (Q10 = b).** Write `no action -- owner ruling 2026-09-23: the light
  card is delineated by its border, not lifted by its fill; the UI stays as it is`. Replace any claim
  in `docs/design/README.md` that cards are "elevated" in the light theme with "delineated by the
  border". F-B21-53 therefore leaves the frontend plan.

- [ ] **Step 2: Write the no-action records.** Each finding's `Status:` prose becomes a bare
  `- [x] **Status:** no action` line, then `**Completed:** <today>`, then the reason on its own line
  (Global Constraints "Resolving a finding": text after the outcome fails DOC015). The reasons:
  - **F-B21-15:** "owner ruling 2026-09-23: Batch 23 schedules no `GET /heatmap/<username>` route, and
    the split pays off only with it; reopen when a batch schedules shareable heatmap URLs."
  - **F-STYLE-1:** "owner ruling 2026-09-23: standing prose guidance with no fix state -- it cannot
    become a gate, and its one example was already rewritten in `14ba5705`; the guidance stands for
    future edits."
  - **F-STYLE-2:** "owner ruling 2026-09-23: no docstring convention is adopted -- a sweep of the
    undocumented-section definitions buys no test or gate; line length and the stale `.flake8` were
    settled earlier."
  - **F-WORKTREE-4:** "owner ruling 2026-09-21 (PR #169 review round 4): none of the three files
    approaches a monolith, and a split adds inventory drift for no gain; revisit when one next changes
    substantially."
  - **F-B21-24:** "Tasks 2-5 shipped; Task 6, the accessibility pass, is the same work as Batch 23
    WP-7's audit and runs there (owner ruling 2026-09-13)."
  - **F-MAS-2:** "owner ruling 2026-09-23: absorbed into F-B21-18, which covers the same untested
    JavaScript in more detail." Also add
    `- F-MAS-2: no automated JS tests -- absorbed into F-B21-18.` under "Deferred / future-batch
    candidates", so the old ID stays resolvable.

- [ ] **Step 3: Write the re-grades.**
  - Move **F-B21-48** and **F-B18-11** under "P2 -- Scaling roadmap", each with a `Status:` line of
    "open (P2), re-graded 2026-09-23 by owner ruling: a persistent scrobble cache is a feature, not a
    defect". F-B18-11's line adds "its only unrejected remedy is F-B21-48".
  - File the Codex/Copilot entry point from F-B21-25 item 3 as a new P2 finding. Take its number the
    same way Task 2 Step 1 does, with prefix `F-B21-`.

- [ ] **Step 4: Split the partly-ruled findings.**
  - **F-B21-4:** record items 1, 2 and 4 as settled, citing `templates/index.html` `.index-grid`,
    RECONCILIATION's loading override, and RECONCILIATION section 16. Record item 3 per Q13. With
    Q13 = a, the whole finding is `no action -- item 3 is folded into Batch 23 WP-6`.
  - **F-B21-19:** per Q12. With Q12 = a, add an override row to `docs/design/RECONCILIATION.md` for the
    width-driven mobile grid, then record the finding as no action, with day-detail named a future
    feature.
  - **F-DOCSYNC-6 and F-WORKTREE-3:** add a dated line recording which items were ruled no action. They
    stay open until the control-plane plan fixes their mechanical items.

- [ ] **Step 5: Run the gates and commit.** Then:

```bash
git commit -m "docs(findings): Record the owner's WP-0 rulings"
```

---

## After this plan

Each of these is its own plan, written once the rulings are in, so its code matches the answers.

1. **Control-plane plan.** It runs after the foundation plan's Tasks 4-10.
   - **F-DOCSYNC-11, -12 and -13** (one task, per Q3), which must land before anything else that
     touches `latest_test_count_authority`.
   - **F-DOCSYNC-7 together with F-MAS-3** (one commit: repoint `TestLatestTestCount`, then split the
     file).
   - **The new work-package finding** (Q4).
   - **F-DOCSYNC-6's two mechanical items**: exit 2 on an outside-root path, and case-consistent
     `BATCH*` discovery.
   - **F-WORKTREE-3's two bugs**: WT010 on a detached, dirty worktree, and the doubled base-ref label.
   - **F-B21-20** (Q5), **F-B21-25 items 1-2** and **F-B21-9** (Q15).
   Every change to a check is accepted only on a live probe: red on the planted defect, green on its
   near miss.
2. **Frontend plan.** It must precede WP-5, which rebuilds the index form.
   - **F-B21-18's harness** (Q14), first, so later fixes land with coverage. Then F-B21-14 (Q8) in the
     same `heatmap.js` region.
   - **F-B21-22** (Q9), **F-B21-23**, now unblocked, and **F-B21-60** part 1 (Q11).
   Each lands with a new frontend-gate check.
3. **Test-infrastructure and dependency plan.**
   - **F-LOAD-2:** a real-thread integration test with no new dependency.
   - **F-MAS-1** (Q7).
   - **F-B21-3's remainder** (Q6), with a live `pip-audit` recount.
   - While there, add `requirements-dev.txt` to the CI audit's inputs. Triage C noticed it is never
     audited.
   - Give the release-check worker `logging.info` lines (from the Q0 answer):
     - one when `_run_release_checks` starts, with its candidate count;
     - one when it finishes, with its checked and corrected counts;
     - one at `enqueue_release_check`'s silent skip when `MUSICBRAINZ_CONTACT` is unset.

WP-0 closes when Parts A, B and C each meet their acceptance in `BATCH23_DEFINITION.md`. One tagged
`(Batch 23 WP-0)` Section 4 entry then records it.

## Acceptance

- Each task's own acceptance holds. No existing test changed except where a task names it, and each
  such change is listed in its commit body. The only such tasks are 4 and 6.
- `pytest -q`, `pre-commit run --all-files`, `frontend_gate.py` and `doc_state_sync.py --check` all
  exit 0 on the final tree. The newest Section 4 entry carries the measured count.
- Every ID in the disposition table is fixed, confirmed already fixed, or carries a dated owner ruling.
  Check it member by member (`AGENTS.md` Anti-Pattern 13).
