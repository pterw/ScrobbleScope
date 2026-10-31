<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0024

### 2026-09-24 - The architecture diagrams are re-verified against source

Side task, no batch tag: walking every `docs/architecture/*.md` diagram
against current source, part of Batch 23 WP-0 Part B. Untagged by owner
ruling 2026-09-23 until the whole of WP-0 lands.

- **Step 1:** `runtime-system.md` gained `api_logging.py` as a runtime node
  (`Utils --> ApiLogging`), a sixth "Five things" bullet on the shared
  `aiohttp.TraceConfig` trace hook and per-provider call summary (F-B23-6,
  `433120c`/`e7e076b`/`5bfb997`), and its `config.py` importer count
  corrected from ten to eleven: `routes/__init__.py`'s module-level
  `MAX_ACTIVE_JOBS` import (landed at `e552956`, before this diagram's own
  last edit, and missed until now) joins the list, and `app.py` is renamed
  the twelfth (deferred-only) importer.
- **Step 2:** `top-albums-sequence.md`, `heatmap-sequence.md`,
  `development-cycle.md` and `documentation-tooling.md` needed no change.
  Walked against `de8c2d8` (`domain.release_window`), `4cbb9b1` (release
  checks run without the cache, guarded per use rather than skipped),
  `e552956` (the capacity message), `82557fd` (the UTC year gate), the
  logging commits above, the `_frontend_gate_*` slice split, `a25d187`
  (the check manifest), `a87e6058` (ruff BLE gate on broad catches),
  `c611f721` (`_validate_api_keys` in `create_app`) and `bd7ffef0` (the
  `.githooks/` CRLF rule) -- each fact these four files already state
  still matches current source.
- **Step 3:** `docs/ARCHITECTURE.md`'s "Last verified" date moved from
  2026-09-20 to 2026-09-24, after every file above was walked.

No test changes; no count site changes (R3).

Validation: `pytest -q` -- **1833 passed**.

### 2026-09-24 - AGENTS.md points at the full docsync CLI and records the installer decision

Side task, no batch tag: `AGENTS.md` pointers and the installer decision,
part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23 until the
whole of WP-0 lands.

- **Step 1:** `AGENTS.md` "Doc Sync Rules" -> "How to run" now points at
  `docs/architecture/documentation-tooling.md` "CLI surface added by the
  close-out and bounded-archives plan" for `--close-batch`,
  `--paginate-archives` and `--cold-storage`, without restating the modes.
- **Step 2:** `AGENTS.md` "Agent skills" gained a "Global rules" pointer to
  `docs/agents/global-rules.md`, in the same shape as its three siblings.
- **Step 3:** `AGENT_NOTES.md` "Architectural Constraints" records the
  installer decision: no live `--install --yes` has run in this repository,
  and either install order fails loudly rather than silently. Wrapper
  first, then `pre-commit install`, moves the wrapper to `pre-commit.legacy`
  and re-enters it through `hook_impl.py`'s `_run_legacy`; the wrapper's own
  non-recursive delegation to `python -m pre_commit hook-impl` then
  inherits `PRE_COMMIT_RUNNING_LEGACY` and hits pre-commit's own "installed
  in migration mode" `SystemExit` on every future commit -- confirmed
  against `install_uninstall.py` and `hook_impl.py` in the installed
  `pre_commit` package, matching the plan's "Errors in the earlier draft".
  `pre-commit install` first, then the wrapper, fails the other way:
  pre-commit's own generated hook file carries no `GENERATED_MARKER`, so
  `install_docsync_hook.py`'s `classify_existing_hook` reads it as
  `"unknown"` and `install()` refuses to overwrite it (exit 2). The wired
  path already runs the checker without the wrapper: `doc-state-sync-check`
  is first in `.pre-commit-config.yaml`, and CI's own explicit preflight
  step backs it up.
- **Step 4:** `AGENTS.md` measures **487** lines (`wc -l AGENTS.md`),
  under the 500-line limit.

No test changes; no count site changes (R3).

Validation: `pytest -q` -- **1833 passed**.

**Follow-up (2026-09-24, owner change).** The owner added one line to the
top of `.github/copilot-instructions.md` and asked for it to be committed:
GitHub's coding agents are to follow `AGENTS.md` and its bootstrap, not
duplicate its rules, and use the existing Graphify guidance for
architecture questions. It is the agent-facing counterpart of this entry's
pointers. The same line, with its curly apostrophe straightened (`AGENTS.md`
Markdown Authoring Rules: ASCII only), is also on PR #242
(`chore/repo-assist-workflow`); the two copies are byte-identical, so the
branches merge cleanly. Docs only.

### 2026-09-24 - The frontend gate selects checks from a manifest

Side task, no batch tag: adding `frontend_gate_checks.toml` so the frontend
gate selects which checks run by name, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Steps 1-2: manifest and selection.** `frontend_gate_checks.toml` (root)
  declares `required` (the four load-bearing checks) and `disabled` (empty
  today). `scripts/dev/frontend_gate.py` loads it with `tomllib` at import,
  validates every named check against `CHECKS`, and refuses -- with a clean
  `[frontend_gate] ERROR:` line, before `main` ever runs -- an unknown name
  or a required check disabled. Selection is by name only: `CHECKS` stays
  the full registry, so the three existing tests in
  `tests/scripts/dev/test_frontend_gate.py` that patch it directly are
  unmodified. `run_checks` and `PLANNED_RUNS` filter by the disabled-name
  set, and the startup line states the enabled count and names every
  disabled check. New test module
  `tests/scripts/dev/test_frontend_gate_manifest.py` (8 tests).
- **Deviation from the brief:** Step 1 says disabling `divider contrast`
  lowers the planned run count by one; measured, it drops by **two** -- the
  check runs on one profile (DESKTOP) but belongs to the `STATIC_ASSETS`
  group, which Firefox also runs as its canary. The test asserts the drop
  is 2, with a comment saying why.
- **Step 3: live probe**, throwaway corpus at `/c/ssprobe` (`git ls-files`
  plus the two new files, since the change is uncommitted), deleted after.

  | probe | expected | exit | evidence |
  |---|---|---|---|
  | faithful copy | same selection as the worktree | 0 | `30 of 30 checks selected; disabled: none`, `PLANNED_RUNS 52` |
  | red: required check disabled | refused before a browser launches | 1 | `[frontend_gate] ERROR: check manifest ... disables required check(s) stylesheet isolation ...`; no launch line in the output |
  | red: unknown name (typo) | refused, not ignored | 1 | `[frontend_gate] ERROR: check manifest ... names 'divider kontrast', which is not a check in CHECKS ...`; no launch line in the output |
  | near-miss green | committed manifest, `disabled = []` | 0 | the worktree's own `frontend` gate run below |

- **Step 4:** `documentation-tooling.md` records the manifest as landed and
  states the decomposition's goal was isolating what executes, not
  shrinking `_frontend_gate_layout.py`.

`frontend` gate run locally (this task changes the gate itself, so its
near-miss green is that run; section 2b's path-prefix `when` condition does
not match `frontend_gate.py`, so it is not implied by other changed paths):
`30 checks passed in 52 runs across chromium, firefox (static assets &
tokens canary on firefox); profiles: desktop, mobile, wide touch`.

Validation: `pytest -q` -- **1833 passed**.

**Fix round 1 (2026-09-24, review finding).** `DEVELOPMENT.md` still stated
the exact fact Step 4 reversed: "the `frontend_gate_checks.toml` registry
stays a deferred candidate" (line 539), next to a stale facade line count
("535 lines", line 532; actual 619 at `a25d187`) -- a live architecture
document, not a dated log, so it is not point-in-time and it directly
contradicted the sentence this same commit wrote into
`documentation-tooling.md`. Fixed: `DEVELOPMENT.md` now says the manifest
landed too, in the same words `documentation-tooling.md` uses, and states
the facade's size only as "under the decomposition plan's 700-line
threshold" rather than restating an exact count -- a second copy of a
number is exactly what went stale here. A second copy of the same stale
count turned up on re-sweep: this Section 3's own "Side task complete: the
frontend gate split (F-B21-51)" bullet also said "measures 535 lines";
fixed the same way. Re-swept the whole tree for both claims, every spelling
(`git grep -n "deferred candidate"`, `git grep -n "535 lines"`,
`git grep -n "frontend_gate_checks.toml"`): every remaining hit is inside a
dated log entry, an archived finding, or the decomposition plan's own dated
worked example -- point-in-time and exempted, consistent with the review's
own sweep.

Validation: `pytest -q` -- **1833 passed**; no test added, docs only.

### 2026-09-24 - The docsync close-out plan's Progress block is closed

Side task, no batch tag: closing the docsync close-out plan's Progress
block, part of Batch 23 WP-0 Part B. Untagged by owner ruling 2026-09-23
until the whole of WP-0 lands.

- **Progress block closed.** Task 4 (`491e61a4` code, `3d8a42a5` docs) and
  the final whole-branch review (engine reviewed alone as `a07f5761`; DOC023
  built as `fa923305`/`28a8527`/`fcfe8d4e`) are ticked, both reaching `test`
  through PR #233 (`2ccf0ddb`) and PR #234 (`88f6e27`). New deviation
  bullets record the review split, DOC023's id-allowlist departure, and
  where the ledger's untriaged Minors went.
- **Owner ruling 2026-09-24 widened this task**: the docsync close-out
  ledger's final review never worked its own carried-over triage list of
  "minor (deferred)" items from Tasks 1, 2, 3 and 4a. Checked individually
  against the code and tests at HEAD: two were already fixed (the
  `run_docsync_check` uncaught `OSError`, and `CONTROL_PLANE_FILES`'
  exact-vs-prefix filename matching -- both folded into `491e61a4`'s fix
  round); three from Task 1 are too terse in the record to check and are
  marked not reproducible; the remaining eleven are still true and filed as
  one finding, F-DOCSYNC-20 (foundation plan DoD row 32).

Validation: `pytest -q` -- **1825 passed**.

**Follow-up (2026-09-24).** The owner ruled one of F-DOCSYNC-20's eleven
items intended behaviour: `--cold-storage` may repaginate a never-paginated
monolith. The item is dropped from the finding, which says why, and ten
remain; the finding stays open at P2. `docs/history/reports/HANDOFF_2026-09-24.md`
had not caught up with this task: sections 1, 3 and 5 now record Task 7 done
and Tasks 8-10 next, section 6 carries both 2026-09-24 rulings, and its Task
11 line no longer cites an untracked workspace file.
Validation: `pytest -q` -- **1825 passed**; docs only.

### 2026-09-24 - Findings hygiene repoints pre-split citations and files four defects

Side task, no batch tag: findings hygiene, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Step 1: pre-split citations repointed by name.** `FINDINGS.md`'s
  F-SWE-3 and `docs/history/findings/FINDINGS_ARCHIVE.md`'s F-B21-6,
  F-SWE-5 (two citations) and F-SWE-2 (context.md's "second `:70-71`
  citation") each named their `orchestrator.py:NNN` line by the function
  it pointed at (`_run_spotify_search_phase`, `fetch_top_albums_async`,
  `background_task`'s outer handler, `_fetch_and_process`'s inner
  handler), confirmed by reading `scrobblescope/orchestrator.py` at the
  commit nearest each finding's date (`bb8681b` for the three 2026-08-20
  SWE-audit findings, `319134e` for F-B21-6, filed 2026-08-22), and naming
  the module both as it was (`orchestrator.py`) and as it is now
  (`scrobblescope/orchestrator/__init__.py` or `_search.py`). No resolved
  record's account of what was wrong or how it closed changed, only its
  citation.
- **The broader `git grep -n "orchestrator\.py:\|routes\.py:"` over the
  live corpus** found 100 hits in 14 files beyond the findings files. Left
  as written, point-in-time: five files under `docs/history/reports/` and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` (named exemptions);
  `docs/history/definitions/BATCH21_DEFINITION.md` (same archive tier as
  `logs/` and `reports/` per `AGENTS.md`'s `docs/history/` table row); and
  five `docs/superpowers/plans/*.md` files, including this plan's own
  Task 6 text, which quotes the citations as the problem statement rather
  than reporting current code. `.codacy.yml`, `docs/SWE_AUDIT_CHARTER.md`
  and `scripts/dev/_frontend_gate_shared.py` were checked and carry none
  of these citations under this grep's pattern; their stale `routes.py`
  citations (a different spelling) stay deferred to WP-0 close-out,
  unedited, per context.md.
- **Step 2: four findings filed**, IDs taken as the next free number per
  tag across both files. `F-DOCSYNC-17` (opening-state defect, resolved
  `aad26e5`, foundation Task 3) and `F-DOCSYNC-18` (archive page target
  had no reader and the cold rule's all-dated condition was undocumented,
  resolved `d499e3a`, foundation Task 4) filed resolved in `FINDINGS.md`'s
  "Resolved this batch" section, each with its `**Completed:**` line.
  `F-DOCSYNC-19` (`--check` has no diagnostic for an interrupted
  publication; DoD row 29) and `F-WORKTREE-6` (the worktree guard's
  `--base-ref` defaults to `origin/main` rather than a fact PLAYBOOK
  declares, sharper since PR #241: WT006 then WT005 against `origin/main`
  with an empty merge-base diff, `docs/history/reports/HANDOFF_2026-09-24.md`
  section 2) filed open (P2) under P2 -- Scaling roadmap. Checked
  F-WORKTREE-6 against F-WORKTREE-3 first: its three open items (the
  between-batch ancestry skip, WT010 missing on a dirty detached worktree,
  the doubled base-ref label) are a different defect, so this is a
  separate finding.
- **Owner ruling, 2026-09-24 (mid-task):** the foundation plan's Task 11
  (F-SWE-5) is recorded done, not left unticked -- F-SWE-5 was resolved by
  the reconcile plan's Task 7 (`ffbee0e`) before this plan reached Task 11.
  Task 11's five step boxes are ticked and a done-by-reference line added
  under its heading; nothing else in Task 11 changed. This supersedes
  context.md's original "do NOT edit Task 11" note.
- **Step 3.** `doc_state_sync.py --fix` then `--check`, both at exit 0.
- **Deviations:** none from the brief's Step 1/2 text; the point-in-time
  scope for `docs/history/definitions/` and `docs/superpowers/plans/` is
  this task's own reading of context.md's "list any hit you leave, with
  the reason" allowance, not an enumerated exemption -- reasons are above.
- Validation: `pytest -q` -- **1825 passed**. No test added; the three R3
  count sites are unchanged.
- **Next:** the foundation plan's Task 7.

**Follow-up (2026-09-24).** `docs/history/reports/HANDOFF_2026-09-24.md` had
not caught up with this task: its Section 1 WP-0 status bullet still read
"Tasks 4 and 5 done; Tasks 6-10 remain," Section 5 item 2 still described
Task 6 as upcoming work with a pre-flight instruction, Section 3's reading
order still pointed a cold session at "Task 6 onward," and Section 6 named
no ruling for Task 11. All four now record Task 6 done (Section 5 item 2
points at this entry), Section 3 points at Task 7 onward, and Section 6
carries the Task 11 (F-SWE-5) done-by-`ffbee0e` ruling beside the other
2026-09-24 rulings. Validation: `pytest -q` -- **1825 passed**; no test
changes, so the three R3 count sites are unaffected.

**Correction (2026-09-24).** The task review reproduced the broader sweep
above as 95-98 hits in 12 files, not 100 in 14; the categorization of what
was left as point-in-time is unchanged.

### 2026-09-24 - The provider summary states its span and its time in calls

Side task, no batch tag: the provider summary log line states its span
alongside its time in calls, part of Batch 23 WP-0 Part C. Untagged by
owner ruling 2026-09-23 until the whole of WP-0 lands. It follows up
F-B23-6's provider-call logging (Task 13); ruled by the owner 2026-09-24,
source `docs/history/reports/HANDOFF_2026-09-24.md` section 5 item 1.

- **Scope.** `scrobblescope/api_logging.py`'s per-session summary read
  `MusicBrainz: 17 calls in 2.6s -- 16x200, 1x503`; the `2.6s` is the sum of
  per-call durations, not how long the provider was being called. Read
  naively it says MusicBrainz ran faster than its 1 request per second,
  which the owner did. MusicBrainz is compliant: the global throttle in
  `scrobblescope/utils.py` spaces request starts one second apart, and the
  owner's log timestamps confirm it. The line now states both:
  `MusicBrainz: 17 calls over 12.1s (2.6s in calls) -- 16x200, 1x503`.
  `_record` gains the earliest call start and latest call end seen per
  provider (`span_start`, `span_end`); `_on_request_end` and
  `_on_request_exception` each read `time.monotonic()` once per end event
  and pass that one reading to both the per-call line and the tally, so the
  per-call milliseconds and the summary's figures never drift apart. Counts
  and outcomes are unchanged; the line still never carries a query string,
  a name, a body or a header.
- **Two existing tests changed** (`tests/services/test_api_logging.py`):
  `test_closing_the_session_logs_one_summary_per_provider`'s
  `message.startswith(...)` assertion moved from `"127.0.0.1: 3 calls in"`
  to `"127.0.0.1: 3 calls over"`, plus a new regex asserting the full shape
  (span, in-calls, outcomes); `test_a_session_that_made_no_calls_logs_no_summary`'s
  filter string moved from `"calls in"` to `"calls over"`, since every
  summary line now carries the new wording and the old filter would have
  passed vacuously.
- **New tests:** span is not the sum of per-call durations (the owner's
  case, driven deterministically through `_record`/`_emit_summaries` against
  a stand-in session object); overlapping calls make time-in-calls exceed
  the span; an exception ending after the last success extends the span and
  is counted under its class name; and one end-to-end test against the real
  session and trace hook, asserting only a lower bound on the span (no
  upper bound -- timing-based upper bounds flake).
- **Deviations:** none.
- Validation: `pytest -q` -- **1825 passed**.
- **Next:** the foundation plan's Task 6.

**Fix round 1 (2026-09-24, review finding).** The review's one Important
issue: `docs/history/reports/HANDOFF_2026-09-24.md` section 2's setup
block still read `# expect 1821 passed`, a second copy of the test count
inside the very file this task's commit had already updated, contradicting
section 1's `**1825 passed**` two screens above it. Fixed by removing the
second copy rather than restating it: the comment now reads `# expect the
count section 1 records`, so there is exactly one number in the file to
keep current. Grepped the whole file again for `1821`/`1825`: the only
remaining hit is section 1's own count. No test changes; no other count
site affected.

- Validation: `pytest -q` -- **1825 passed**.

### 2026-09-24 - The handoff schedules a truer provider summary line

Side task, no batch tag: a handoff revision, part of Batch 23 WP-0 Part C.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Why.** The owner read `MusicBrainz: 17 calls in 2.6s` as MusicBrainz
  running faster than its 1 request per second. The calls were compliant:
  their log timestamps are one second apart, as the global throttle in
  `scrobblescope/utils.py` enforces. The summary's time is the sum of
  per-call durations, not the session's span.
- **Change.** `docs/history/reports/HANDOFF_2026-09-24.md` section 5 now
  opens with a side task, ruled by the owner on 2026-09-24 to run before
  foundation Task 6: the summary states both the span and the time in calls.
  Section 7 withdraws the per-album Spotify item (the owner's log lines came
  from `/api/artist_spotlight` and the token fetch, not the album fetch). It
  also notes that `scrobblescope/musicbrainz.py` puts album and artist names
  in its retry log label, for the WP-3/WP-4 Data handling check.
- **Section 3** names the side task as next, before Task 6.
- Validation: `pytest -q` -- **1821 passed**; the untracked mutation-runner
  tests were excluded, since they are not repository state. Docs only.

### 2026-09-24 - The cloud handoff is revised after the first cloud session

Side task, no batch tag: revise the session handoff at the end of the first
cloud session, part of Batch 23 WP-0 Part B. Untagged by owner ruling
2026-09-23 until the whole of WP-0 lands.

- **Scope.** Documentation only. `docs/history/reports/HANDOFF_2026-09-24.md`
  is revised in place rather than superseded by a second file with the same
  date, so Section 3, the cloud kit and this log keep one entry point.
  `.superpowers/cloud-kit/constraints.md` gains Lessons L11-L13 and a header
  that names Tasks 6-10. Section 3's handoff bullet says the file was
  revised.
- **What the handoff now records.** Foundation Task 5 is done (`9ea79f5`,
  `aa6a867`, `e913f89`, `4ae0dc3`, three review rounds, the last approved
  with no findings). PR #241 merged into `main` as `92f7d6a`, and no PR is
  open for the branch. Three cloud-sandbox limits: the Tailwind artifacts
  must be fetched with `curl` (Python 3.13 rejects the proxy CA), the
  frontend gate cannot run, and Codacy's API is blocked. The guard fails
  against `origin/main` since the merge (WT006 while the branch has nothing
  past it, WT005 once it does) with an empty merge-base diff, so it runs
  with `--base-ref origin/test`. The owner's Task 5 rulings and the
  push rule (hold until a review is recorded clean).
- **Lessons.** L11: check a task's plan checkboxes before recording it done;
  the owner caught Task 5's. L12: ask the first review to sweep the whole
  task range for stale copies of every changed fact; Task 5 needed three
  rounds without it. L13: every code a gate-runner summary quotes must be
  found in its logs.
- **Deviations.** None. No code or test changed. The first commit said the
  guard reads WT006 against `origin/main`; its own pre-commit run printed
  WT005, because the branch had moved past the merge. Both statements now
  name both codes.
- **Validation:** `pytest -q` -- **1821 passed**. `pre-commit run --all-files`
  and `doc_state_sync.py --check` pass, with the expected WT005, DOC024 and
  root-BATCH warnings.
- **Next.** Foundation Task 6, findings hygiene, from the handoff's section 5.

### 2026-09-24 - Stop stating a DOC code range the catalogue owns

Side task, no batch tag: replace every live prose statement of a `DOC001-DOC0NN`
range with wording that states no range, part of Batch 23 WP-0 Part B.
Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

- **Scope: the foundation plan's Task 5.** Six live sites stated a stale
  contiguous range (`AGENTS.md` x3, `DEVELOPMENT.md`, and
  `docs/architecture/documentation-tooling.md` x2, one of them the heading).
  Both `DOC001-DOC023` and `DOC001-DOC024` are false today: DOC021 and DOC022
  are reserved by
  `docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`
  but not raised, so no contiguous span from `DOC001` is true. Each site now
  says "the DOC diagnostic catalogue" (owner: `documentation-tooling.md`)
  instead of restating a range; the catalogue's own heading is renamed
  "The DOC code catalogue" and its one explicit list reads "`DOC001`-`DOC020`,
  `DOC023` and `DOC024` issues". `FINDINGS.md`'s F-B21-61 note ("a new
  invariant for this finding starts at DOC023") is repointed at the catalogue,
  since DOC023 is itself now taken (the finding-lifecycle grandfathered-finding
  count, `scripts/docsync/findings.py`).
- **Tests repointed, controller ruling 2026-09-24 (the one sanctioned
  existing-test edit).** `tests/test_docsync_integrity.py::
  test_stated_docsync_range_matches_the_highest_code_raised` and
  `test_stated_range_helper_rejects_a_stale_range` read `AGENTS.md`'s stated
  range, which no longer exists. Both are renamed
  (`test_stated_docsync_catalogue_matches_the_codes_raised`,
  `test_stated_catalogue_helper_rejects_a_mismatched_list`) and repointed at
  `documentation-tooling.md`'s explicit list; their helpers become
  `CATALOGUE_SENTENCE_RE`, `_stated_codes`, `_raised_codes` and
  `_catalogue_matches_raised_codes`. The comparison is now set equality
  (parsing "DOC0AA-DOC0BB" spans and single codes) rather than a maximum, so
  a listed-but-unraised code (DOC021) is caught, which comparing only the
  upper bound could not catch. The proof test mutates the real catalogue
  sentence in place (drop DOC024; add DOC021) rather than a synthetic
  fixture, so it exercises the same parsing the corpus test relies on.
- **`.docsync.toml`** gains a fourth `[[retired]]` declaration, modelled on
  its "the docsync integrity range ends at DOC011" sibling: it matches the
  bare literal `DOC001-DOC023` or `DOC001-DOC024`, either spelling
  (contiguous or backtick-split), needs no verb-prefix guard because the
  valid list never contains either substring, and leaves `DOC001-DOC020`
  alone.
- **Discovered and filed as F-DOCSYNC-16.** The three pre-existing
  `[[retired]]` declarations' `allow_after` marker for `PLAYBOOK.md` was the
  literal string `"## 4. Execution log"`, but `check_retired` compares a raw
  line by exact equality and the real heading is `"## 4. Execution log (for
  agent handoff)"` -- confirmed by reproducing the mismatch directly against
  `check_retired`. Their Section 4 exemption was therefore non-functional
  against the live document, latent only because no dated entry restated one
  of their three retired phrases. This task's own new declaration used the
  full, correct heading text from the start so it was not affected.
- **Live probe** (`/tmp/ssprobe`, `git archive` of `git stash create`,
  deleted after):

  | probe | expected | got |
  | --- | --- | --- |
  | faithful copy `--check` | same summary as the worktree | match, exit 0 |
  | red: add "the DOC001-DOC023 catalogue" to `AGENTS.md` | DOC011, exit 1 | DOC011, exit 1 |
  | red: add `` returns typed `DOC001`-`DOC024` issues `` to `DEVELOPMENT.md` | DOC011, exit 1 | DOC011, exit 1 |
  | near-miss: same text struck through in `AGENTS.md` | silent, exit 0 | silent, exit 0 |
  | near-miss: same text in a dated Section 4 entry below the marker | silent, exit 0 | silent, exit 0 |
  | near-miss: "DOC001-DOC020" in `AGENTS.md` prose | silent, exit 0 | silent, exit 0 |
  | mutate `documentation-tooling.md`'s list to drop DOC024 | corpus test red | red |
  | mutate `documentation-tooling.md`'s list to add DOC021 | corpus test red | red |

- Validation: `pytest -q` -- **1821 passed**. No test added or removed, so
  the three R3 count sites are unchanged.

**Fix round (2026-09-24, review finding).** The review's one Important
issue: the three pre-existing `allow_after` markers were left broken
next to the fourth, freshly-corrected one in the same commit and same
file, instead of being corrected outright (Anti-Pattern 11). Owner ruling:
correct all three in `.docsync.toml` (touching nothing else in those
declarations); reword F-DOCSYNC-16 to name the mechanism gap -- docsync
silently ignores an `allow_after` marker that matches no line, rather than
erroring -- and record that the three markers are corrected in this fix
commit; drop its priority to P2 (the fix shape becomes a future check that
errors on a dead marker, not built here); status stays open.

- **`.docsync.toml`:** all three `[retired.allow_after] "PLAYBOOK.md" =
  "## 4. Execution log"` lines corrected to `"## 4. Execution log (for
  agent handoff)"`, the real heading, matching the fourth declaration this
  task already added. Nothing else in the three declarations changed.
- **`FINDINGS.md`:** F-DOCSYNC-16 retitled "docsync silently ignores an
  `allow_after` marker that matches no line," its body names the general
  mechanism gap ahead of the specific instance, records that the three
  markers are now corrected, keeps the reproduction evidence, and states
  the not-yet-built fix shape (a declaration check erroring on a dead
  marker). Priority dropped P1 -> P2; status line unchanged (`open`).
- **Live probe, reproduced in a fresh `/tmp/ssprobe`** (`git archive
  9ea79f5`, `git init`, deleted after): a dated Section 4 entry quoting
  "limit_results goes inside the thresholds disclosure" gives `ERROR
  DOC011`, exit 1, with the unfixed markers; correcting all three markers on
  that same scratch tree makes it silent, exit 0; and `--check` on the
  unmodified corpus (no injected quote) is byte-identical before and after
  the marker fix -- same four DOC024 + root-BATCH warnings, exit 0.

  | probe | expected | got |
  | --- | --- | --- |
  | unfixed markers, dated entry quoting the retired `limit_results` phrase | DOC011, exit 1 | DOC011, exit 1 |
  | corrected markers, same quote | silent, exit 0 | silent, exit 0 |
  | corrected markers, unmodified corpus vs. before | identical `--check` output | identical |

- Validation: `pytest -q` -- **1821 passed** (unchanged; no test touched
  in the fix round).

**Fix round 2 (2026-09-24, re-review + owner catch).** Two Important issues
and one owner catch, all in the same commit (`aa6a867` -> next): the
`.docsync.toml` comment above the fourth declaration's `allow_after` still
described the three siblings' pre-fix state in the present tense, false as
of `aa6a867` -- rewritten to state only what is true now (the exemption
needs the real heading text; F-DOCSYNC-16 records the silent-ignore
mechanism), with no other live present-tense claim found by corpus grep.
F-DOCSYNC-16 carried its new P2 priority but was still filed under the
`## P1 -- Next batch candidates` heading -- moved, unchanged, to the top of
`## P2 -- Scaling roadmap`. Owner catch: this task's own Step 1-6 checkboxes
in the foundation plan were never ticked in the first commit -- ticked now,
nothing else in the plan changed.

- Validation: `pytest -q` -- **1821 passed** (unchanged; no test touched).

**Fix round 3 (2026-09-24, re-review).** `DEVELOPMENT.md:559`'s portability
ties table still quoted the pre-fix `allow_after` marker literal as a
worked example; corrected to the real heading text, the only change in
that row.
