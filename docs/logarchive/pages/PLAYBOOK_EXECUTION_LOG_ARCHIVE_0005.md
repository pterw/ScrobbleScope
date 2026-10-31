<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0005

### 2026-08-03 - PR #168 pre-merge canonical-doc audit (side-task)

- Scope: audited the PR head against the canonical documentation and
  handoff rules before rebase merge; found and fixed two P1 operational
  documentation defects that could misdirect the next agent.
- Plan vs implementation:
  - Removed the superseded `fa61716` fork point from the active Batch 21
    definition. Branch lineage is volatile during review-remediation
    rebases, so the definition now delegates that state to PLAYBOOK
    Section 4 instead of pinning another copy.
  - Corrected the live side-task archive header from obsolete PLAYBOOK
    Section 10 to Section 4 and repointed all three read helpers from the
    `docs/history/` tombstone to `docs/logarchive/`.
  - Recorded the resolved P1 issue as FINDINGS.md F-DOCSYNC-5 under the
    repository's source-tag nomenclature and refreshed the file's
    last-updated date.
  - Replaced the SWE audit charter's fixed F-DOCSYNC numeric range with
    a FINDINGS-owned category pointer so new or resolved F-DOCSYNC items
    remain in the do-not-re-report baseline.
- Deviations: none. PR #168 contains no runtime behavior change, and no
  GitHub thread or PR state was changed.
- Validation: targeted documentation regression check -- pass.
  `pytest -q` -- **390 passed** with 3 existing aiohttp/Python 3.13
  warnings. `pre-commit run --all-files` -- all 10 hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected active-root
  `BATCH21_DEFINITION.md` warning.
- Forward guidance: after PR #168 merges, realign `wip/batch-21` with
  `main`, then continue Batch 21 WP-1. F-SWE-1 remains a separate,
  chartered audit whose execution is still pending.

### 2026-08-03 - PR #168 Copilot review round 1 (side-task)

- Scope: assessed both Copilot review comments on PR #168; both were
  technically valid and addressed.
- Plan vs implementation:
  - Replaced the canonical `Registry entries 4 and 5` example in
    `AGENTS.md` with symbolic placeholders. The numeric example matched
    the expanded sweep it was explaining, so the rule created its own
    violation and made the related no-current-hits claim false.
  - Corrected the prior side-task's forward guidance. The branch was
    level with `main` immediately after realignment, but applying the
    review-fix commit left it directly based on `main` and one commit
    ahead, not equal to it.
- Deviations: none. Dated point-in-time log references remain unchanged
  under the canonical rule's explicit historical-record exception.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: wait for the next PR #168 review round before WP-1.

### 2026-08-02 - Post-merge branch realign; PR #166 review fixes (side-task)

- Scope: PR #165 was rebase-merged (main tip `458f9ad`). The rebase
  produced the usual 23/23 ahead-behind artifact with an identical tree,
  and PR #166 was opened from it in the reverse direction
  (`main` -> `wip/batch-21`); #167 was opened from a separate Copilot
  branch to fix review comments. The owner closed both.
- Plan vs implementation:
  - `wip/batch-21` reset to `origin/main` and force-pushed with lease;
    ahead-behind is 0/0. Commit history on `main` is intact -- all 23
    commits landed individually. The apparent bunching is rebase
    rewriting committer dates while author dates stay distinct.
  - Reapplied the three valid PR #166 findings here so they arrive
    validated and on one lineage: the `MAX_ACTIVE_JOBS` comment no
    longer claims arrival-order serialization (`threading.Lock` gives no
    FIFO guarantee -- it now says each throttle serializes reservations
    behind a shared lock with no ordering guarantee); the canonical
    numeric-citation sweep covers plural and alternate forms, since a
    pattern written as `Registry #\d` cannot match
    `Registry entries 4 and 5`; and the round-9 entry's "returns
    nothing" claim is qualified to exclude dated point-in-time records,
    which legitimately contain such citations.
  - Third occurrence of a countermeasure scoped to the instance that
    prompted it rather than the class. The rule now says explicitly to
    match plural and alternate forms.
- Deviations: none. PR #167 additionally proposed merging #166; that was
  wrong -- #166 pointed `main` at `wip/batch-21`, so merging it would
  have produced the merge commit the rebase-merge workflow exists to
  avoid.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: branch is directly based on `main`, with this one
  review-fix commit ahead, and is ready for WP-1 after PR review.

### 2026-08-01 - PR #165 round 9; new rules are not retroactive (side-task)

- Scope: three suppressed comments, all valid -- numeric citations into
  ordered lists (`Anti-Pattern Registry entries 4 and 5`, two
  `acceptance criterion 8` references) that the registry's own
  name-based citation rule prohibits.
- Cause, established from history rather than assumed: the citations
  were written in the SSOT pass and the FINDINGS refresh; the rule
  banning them was written two commits later. Nothing swept the
  existing corpus against the new rule, so the rule shipped with a
  backlog of its own violations. The pre-push checklist greps the blast
  radius of *the change*; when the change is a rule, the blast radius is
  the whole repository, and that leap was never made.
- Plan vs implementation: all three citations repointed by name. A
  repo-wide sweep for `entries N`, `Registry #N`, `criterion N`,
  `step N`, `rule N`, `item N` across every canonical doc returns no
  matches outside dated point-in-time log records, which stay as
  written. The lesson was folded into the existing blast-radius
  anti-pattern as one sentence rather than becoming a fifteenth
  registry entry -- see the verbosity note below.
- Deliberate non-action: folded into an existing entry rather than added
  as a fifteenth, because rule text has begun causing findings as well
  as preventing them -- the registry grew long enough to need numbers,
  and the numbers became the defect.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: merge rather than iterate further.

### 2026-08-01 - PR #165 round 8; over-broad claims narrowed (side-task)

- Scope: three suppressed comments, all valid, all fixed.
- Plan vs implementation:
  - The Section 2 note claimed close-out entries for *each* batch live
    in the monolith archive. False: `BATCH18_LOG.md` holds its own
    close-out because that heading carried a `(Batch 18 WP-5)` tag;
    only the `(Batch N close-out)` spelling misroutes. Narrowed here
    and in F-DOCSYNC-3, which carried the same over-broad framing.
  - The Section 2 subsection heading still read "Completed batches
    (definitions archived)" while the table lists the active batch with
    a root definition. Retitled to cover both.
  - `AGENT_NOTES.md` asserted a batch was active and where its
    definition sits in the same breath as declaring that the file does
    not track batch state -- self-contradictory, and false between
    batches. Reduced to the pointer alone.
  - Anti-Pattern Registry, assertions entry: broadened from the one
    phrasing that had failed before (`all N`, ranges) to the full
    quantifier vocabulary, since the narrow sweep is what let "each
    batch" through.
- Assessment of the review loop: none of these three were caused by the
  previous round's fixes -- the fix-causes-finding chain that drove
  rounds 5 through 7 did not repeat. What remains is pre-existing
  over-broad wording in text the sweep touched. On that basis the
  pre-push checklist is working and mechanical enforcement is not yet
  warranted; a consistency-lint hook stays a docsync-WP candidate rather
  than scope creep into this PR.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: findings have narrowed to wording precision rather
  than correctness; this is the diminishing-returns point. Recommend
  merging rather than requesting another round.

### 2026-08-01 - PR #165 round 7 + review-loop pattern sweep (side-task)

- Scope: owner asked for the round-7 findings to be verified but not
  fixed until a sweep across every review round on PRs #163/#164/#165
  identified why fixes keep producing new findings. Corpus: ~40
  findings over 12 rounds.
- Round 7 findings (all three valid):
  - `AGENTS.md` close-out step 3 said "add a row" to PLAYBOOK Section 2,
    but the active batch already has one -- following it literally
    duplicates the row. Now says repoint the existing row, add only if
    absent.
  - The sufficiency gate required agreement with "the batch definition"
    while bootstrap step 3 states no definition exists between batches,
    so the gate was unsatisfiable in that state. Both states now
    stated.
  - `docs/SWE_AUDIT_CHARTER.md` labelled its differential baseline
    "Open findings" while including F-DOCSYNC-4, resolved earlier in
    this same PR. Relabelled as already-tracked regardless of status,
    with an instruction to check each `Status:` line.
- Sweep results -- four recurring classes, now in the Anti-Pattern
  Registry. Two were already logged; two are new:
  - *Fixing the instance instead of the class* (logged previously): the
    dominant cause. Rounds 6 and 7 findings were created almost
    entirely by rounds 5 and 6 fixes.
  - *Lossy or contradictory consolidation* (new): collapsing duplicated
    rules to one owner while leaving copies, dropping a specific
    prohibition (the `git add -A` ban nearly vanished this way), or
    contradicting another section of the same file.
  - *Assertions over sets, ranges, and citations* (new): "all seven CSS
    files", "F-DOCSYNC-1 through F-DOCSYNC-4", citing a gitignored
    file, citing an anti-pattern that does not cover the case.
  - *Happy-path-only procedures* (new): steps that break in an edge
    state -- row already present, no definition between batches, gate
    ordered before the work it validates.
- Why the loop exists, and the structural fix: the validation gates
  check mechanics only -- nothing verifies that one document still
  agrees with another, so each fix's damage is discoverable only by the
  next review round. Added a "Pre-push self-review" block to Commit
  Rules: read changed files whole rather than as diffs, run the
  blast-radius greps, walk procedures through edge states, and prefer
  deletion to addition because every added sentence is new surface area.
- Deviations: none. The new checklist caught its own first violation --
  the draft cited registry entries by number, which the same registry
  forbids; now cited by name.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the honest test is round 8. If it finds fresh
  self-inflicted drift, the checklist is not enough and the next step is
  mechanical enforcement (a consistency-lint hook) rather than more
  prose.

### 2026-08-01 - PR #165 review round 6; self-inflicted-drift anti-pattern (side-task)

- Scope: round 6 returned three suppressed comments, zero visible. All
  three verified valid -- and all three were created by round 5's own
  fixes, which is the finding that matters more than the fixes.
- Plan vs implementation:
  - Acted: `AGENTS.md` Side-Task Handling and `HANDOFF_PROMPT.md` both
    cited "Commit Rules step 4" for the documentation requirement; the
    round-5 reorder moved it to step 1. Repointed **by name** ("the
    documentation step", "Missing log entries") rather than by number,
    so a future reorder cannot re-stale them.
  - Acted: `AGENT_NOTES.md` load-testing bullet still asserted the
    per-job guarantee and single-throttle model that round 5 corrected
    in `config.py`. Rewritten to match and to point at `config.py` as
    the single owner of the rationale.
  - Declined (precedent): PLAYBOOK Section 4 entries at :163 and :262
    also contain "step 3/4/6" references that no longer match the
    current numbering. They are dated point-in-time records of what was
    true when written; retro-editing rotated log content was declined
    and accepted in PR #162 round 3 and PR #163 round 3.
  - Root-cause fix: new Anti-Pattern Registry entry 11, "Fixing the
    instance instead of the class" -- requires a blast-radius grep
    before the gates (references to anything renumbered/renamed, and
    sibling copies of any corrected claim), and prefers name-based
    cross-references over numeric ones.
  - Swept beyond the three findings: verified the remaining numeric
    references (`AGENTS.md` close-out step 2, charter bootstrap step 1)
    still resolve correctly, and that the `req/s` claims in F-B18-11 and
    F-B18-10 are accurate because the heatmap and album pipelines are
    both Last.fm-only.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: pushed under the standing review-fix exception with
  a batched reply.

### 2026-08-01 - PR #165 Copilot review round 5 (side-task)

- Scope: round 5 returned "not ready to approve" with four suppressed
  comments and zero visible ones. All four verified valid against the
  code; all four acted on.
- Plan vs implementation:
  - `config.py`: the MAX_ACTIVE_JOBS rationale claimed "one global
    10 req/s API throttle". Wrong -- `utils.py:81-82` builds separate
    `_LASTFM_THROTTLE` and `_SPOTIFY_THROTTLE`. Comment now names the
    Last.fm scrobble-fetch phase as the binding constraint.
  - `AGENTS.md` commit procedure: the docsync `--check` gate sat at
    step 3 while the PLAYBOOK update was step 4, so the gate ran before
    the documentation it validates (and `pre-commit` carries the
    `doc-state-sync-check` hook). Reordered: write docs, `--fix`, then
    the three gates on the final state. This matches what sessions
    already do in practice; only the written rule was wrong. Fixed a
    duplicate step number introduced by the renumber.
  - `FINDINGS.md` F-DATA-1 open question 2 proposed grouping
    `spotify_cache` by `artist_norm + album_norm` -- which is the
    primary key (`init_db.py:42`), so every group holds exactly one row
    and the upsert has already overwritten any rival date. Replaced
    with the two methods that can actually work (re-run the Spotify
    search and compare against the earliest fresh candidate, or
    cross-check MusicBrainz).
  - `docs/SWE_AUDIT_CHARTER.md`: prescribed commit subject was a noun
    phrase, violating the imperative-subject rule the charter tells
    executors to follow. Now imperative.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: pushed under the standing review-fix exception with
  a batched reply. PR #165 remains merge-ready pending the next
  auto-review.

### 2026-07-31 - FINDINGS: record reissue cache-key collapse (side-task)

- Scope: capture a data-quality mechanism found while discussing the
  DEVELOPMENT.md rewrite, before the reasoning was lost to chat. No code
  change -- this is a finding, not a fix.
- Plan vs implementation: added `F-DATA-1` under P2.
  `normalize_name()` strips `deluxe`/`edition`/`remastered` and eight
  more words, so a reissue and its original normalize identically; since
  the `spotify_cache` PK is `artist_norm + album_norm`, they share one
  row and whichever populated it first serves its `release_date` for 30
  days. Owner observed this with Viagra Boys "viagr aboys" (2025)
  surfacing under 2026 via the JP deluxe released 2026-01-09, on an
  account that never played it.
- The finding records why the collapse is nonetheless correct (Last.fm
  scrobbles the same record under inconsistent album strings; keying
  editions apart would split one album into several leaderboard rows
  with divided playcounts), the candidate fix (decouple counting from
  dating -- keep the collapse for aggregation, take the *earliest*
  candidate release date when resolving the year, no schema change), the
  rejected boolean discriminator and why, three questions answerable by
  querying the cache, and the note that Spotify exposes no
  original-release-date field at all.
- Deviations: earlier in the session an agent claim that release-date
  drift was a systemic risk was walked back. The owner has ~14 years of
  scrobbles and one recalled instance; the claim had been reasoned from
  a plausible mechanism rather than measured. Filed P2 with low user
  impact stated explicitly, and `release_scope: all` already bypasses
  date filtering. Recording the correction so the finding is not read as
  more urgent than the evidence supports.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: question 2 (which other albums) is a cache query, not
  an investigation -- run it before designing any fix. Sequenced behind
  Batch 21, the F-B20-2 orchestrator split, and the test/docstring pass
  per owner priority.

### 2026-07-31 - DEVELOPMENT.md: correct HANDOFF_PROMPT description (side-task)

- Scope: DEVELOPMENT.md described `HANDOFF_PROMPT.md` as a condensed
  checklist of rules, gates, read order, and commit discipline. That was
  accurate until this branch, which reduced the file to post-read
  verification plus the handoff checklist and replaced everything else
  with pointers. The description was left describing the architecture
  this PR removed.
- Plan vs implementation: two passages corrected -- the architecture
  overview and the per-file section, which was also retitled from
  "Bootstrap Procedure" to "Session Start and Handoff" to match what the
  file now contains. Both now state why the summaries were removed
  (each restatement drifted from its source), which is the reasoning the
  rest of the document uses.
- Deviations: scope-limited on purpose. Only the passages this branch
  made wrong were touched. DEVELOPMENT.md has other known staleness --
  the `gemini-pr-triage` skill is now `pr-bot-triage`, the
  review-suggestions section predates repo-aware review tooling, and the
  closing paragraph needs a rewrite -- all deferred to a post-merge
  documentation pass, per the same in-scope test applied to
  `concurrent_users_test.py` in review round 1.
- Note: this class of staleness is invisible to diff-scoped review.
  Copilot reported "13/13 changed files" across four rounds and
  DEVELOPMENT.md was never among them, so a file made wrong by the diff
  but not part of it cannot be flagged. Worth remembering when relying on
  automated review for consistency.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: the post-merge pass should reframe the review section
  around how the tooling changed rather than around rejection, and
  `README.md:492` must move with it -- it currently promises a section on
  suggestions "evaluated and rejected".

### 2026-07-31 - Push rule: standing exception for review-fix commits (side-task)

- Scope: owner-directed policy change, not a review finding. During PR
  #165 triage the owner granted a standing authorization to push
  review-driven commits without asking per round, on the reasoning that
  the agent reaches the diminishing-returns point on its own and a
  per-round approval round-trip only stalls the loop.
- Plan vs implementation: encoded in AGENTS.md Commit Rules step 6 rather
  than left as an agent-side preference, because AGENTS.md is the rules
  SSOT and a spoken rule that contradicts the written one is exactly the
  defect this PR spent four rounds removing. Scoped per owner: **Claude
  Code and Codex sessions only.** GitHub Copilot task sessions and their
  subagents, Jules, and any other agent follow the unmodified rule --
  the owner does not extend equal trust to agents of varying quality
  that it cannot inspect per-invocation. Step 6 already carried a
  Copilot-specific clause, so per-agent scoping had precedent.
- Deviations: the exception is deliberately narrow. Review-fix commits on
  an open PR only; batch and WP commits still pause, and force-pushes,
  history rewrites, and anything touching `main` still require explicit
  instruction.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: if the agent roster changes, this clause names
  specific agents and will need revisiting -- it is an allowlist, not a
  capability test.

### 2026-07-31 - PR #165 Copilot review round 4 (side-task)

- Scope: zero visible comments, two suppressed, both valid and both real
  defects rather than the judgement-call trade-offs round 3 predicted.
  The convergence call made after round 3 was wrong; recorded here
  because the wrong prediction is the useful part. Tally 18/18.
- Plan vs implementation:
  - **A rule was silently deleted by this PR, and round 1 removed the
    last copy.** The prohibition on `git add -A` / `git add .` lived in
    two places before this branch: AGENT_NOTES.md Owner Preferences and
    the old HANDOFF_PROMPT anti-pattern list. The PR's HANDOFF_PROMPT
    rewrite dropped its copy, and the round-1 dedup replaced the
    AGENT_NOTES copy with a pointer to AGENTS.md Commit Rules -- which
    never contained the prohibition. Step 5 only said "stage only files
    changed for this work package", which `git add -A` can satisfy when
    every changed file happens to belong to the WP. Restored explicitly
    in Commit Rules step 5, the canonical location the pointer targets.
  - Lesson: verifying that a pointer's target "covers it in substance"
    is not enough. Round 1 checked AGENTS.md:167 and accepted a
    paraphrase as equivalent when it dropped a prohibition. Before
    deleting a rule copy, diff the *specific obligations*, not the topic.
  - `scripts/testing/concurrent_users_test.py` promised queuing in three
    places. `acquire_job_slot()` uses `acquire(blocking=False)` and both
    call sites (`routes.py:460`, `routes.py:570`) return an error
    immediately, so excess submissions are rejected and never queued.
    Round 1 edited one of those lines for the cap change without
    questioning the surrounding claim. Now describes rejection, matching
    README's "capacity rejections" wording.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: do not call convergence from the *shape* of a round's
  findings. Rounds 2 and 3 returned zero visible comments and were still
  productive; round 4 found a deleted rule. Stop when a round returns
  nothing, not when the findings look minor.

### 2026-07-31 - PR #165 Copilot review round 3 (side-task)

- Scope: round 3 again returned zero visible comments and three
  suppressed ones. Two acted on in full, one acted on in part.
  Suppressed-block tally now 16/16 across #163, #164, and #165.
- Plan vs implementation:
  - `docs/SWE_AUDIT_CHARTER.md` Section 3 copied the ten principle names
    from AGENT_NOTES.md and **had already drifted**: the copy dropped the
    definitions for Dependency Inversion, Least Knowledge, and Fail Fast,
    and truncated SRP from "single responsibility per module/function".
    This is the rare case where the drift was demonstrable rather than
    hypothetical, so the copy is gone. The section now points at
    AGENT_NOTES.md and keeps only the two audit-specific methods (Clean
    Architecture via the SESSION_CONTEXT Section 4 acyclic graph, Boy
    Scout via git history).
  - `docs/SWE_AUDIT_CHARTER.md` Section 6 restated side-task entry
    placement that AGENTS.md Side-Task Handling owns -- and round 2 had
    just renumbered that section, so the charter was already a rewrite
    away from being wrong. Delegated.
  - `HANDOFF_PROMPT.md` Section 1 restated the bootstrap-conflict rule
    verbatim from AGENTS.md:64-65 inside a paragraph that claims rules
    "are not restated here". Removed.
- Deviations: **partially declined** the reviewer's request to also strip
  "Do not push without owner instruction" from the charter's commit step.
  Verified AGENTS.md:171 owns it, so the SSOT argument is technically
  right, but that line sits at the point of action for a cold-start
  executor (the charter is written so Codex can run it without prior
  context) and a push is not reversible. Deliberate safety redundancy is
  worth one line. Removed the same sentence from HANDOFF_PROMPT Section 1
  by contrast, because there the reader is being sent to AGENTS.md in the
  very same paragraph, so the copy buys nothing.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: watch for diminishing returns. Rounds 1-3 were all
  genuine, but the remaining duplication is increasingly load-bearing
  context for cold-start executors; judge each on whether the copy can
  drift *and* whether losing it costs a reader who cannot see the source.
  Batch 21 WP-1 remains the next action.

### 2026-07-31 - PR #165 Copilot review round 2 (side-task)

- Scope: round 2 returned **zero visible comments and five suppressed
  ones**. All five were valid. The suppressed-block hit rate is now 13/13
  across PRs #163, #164, and #165 while the visible stream has gone dry
  twice; treat that block as the primary signal, not an appendix.
- Plan vs implementation:
  - `AGENTS.md` Side-Task Handling read as an ordered procedure whose
    step 1 was "commit" and step 2 "add the log entry", contradicting
    Commit Rules step 4 and Anti-Pattern Registry #9, which require the
    entry to be in the same commit. Since AGENTS.md is now the rules
    SSOT, an internal contradiction there is load-bearing. Reworded so
    side-tasks inherit the commit rules unchanged and differ only in
    entry placement and tagging; the remaining steps renumbered.
  - `HANDOFF_PROMPT.md` Section 5 told agents to document completion
    *after* committing and to commit the docs separately -- the same
    conflict, one level down. Now states that docs land in the commit.
  - Resolution was evidence-based, not a judgement call: registry #9
    forbids a commit without its entry, and all four recent side-task
    commits (`2559f39`, `2b9b095`, `98cc50c`, `900d0e6`) bundle
    PLAYBOOK + archive with the change. Docs were wrong; practice was
    right.
  - `FINDINGS.md` F-LOAD-1 proposed an "N/5 slots in use" hint, which
    hard-codes a value that is env-configurable. This PR had changed it
    from "N/10" -- swapping one literal for another. Now specifies
    reading the cap from `MAX_ACTIVE_JOBS` at render time.
  - `.claude/SESSION_CONTEXT.md` header said 2026-07-28 while the body
    recorded a 2026-07-31 runtime change. Header updated.
  - `docs/SWE_AUDIT_CHARTER.md` cited "AGENTS.md registry #10" for
    silent scope reduction; #10 is about re-measuring canonical figures
    and says nothing about audit coverage. The charter was added in this
    PR, so this was a sourcing error at write time, not staleness --
    corrected rather than left as a point-in-time record. Now states the
    requirement directly.
- Deviations: round 1 split its fixes across two commits, and `07c4f5b`
  therefore landed without its own Section 4 entry -- a violation of
  Anti-Pattern Registry #9, the rule this round clarifies. Not rewritten:
  both commits were already pushed and history rewrites need owner
  instruction. Round 2 is a single commit. Standing lesson: this repo's
  #9 outranks the generic "prefer small atomic commits" heuristic, and
  the one-commit-per-review-round precedent from PR #163 was correct.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all 10 hooks pass. `doc_state_sync.py --check` -- exit 0.
- Forward guidance: Batch 21 WP-1 remains the next action. `gh` writes
  are still unavailable this session, so the round-2 reply is unposted.
