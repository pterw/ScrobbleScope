<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0007

### 2026-08-12 - PR #170 round 6; reviewed, cross-references repointed (side-task)

- Scope: two visible review comments and four suppressed Copilot comments
  against the round-5 head `d8d3e0d`; one visible finding was already
  recorded, the other was a doc-currency correction.
- The F-WORKTREE-5 restatement (Copilot `r3766306027`). Valid mechanism:
  `parse_batch_branch` filters candidates through `is_display_safe_ref`
  before counting them, so a Section 3 naming one display-safe and one
  display-unsafe branch resolves to the safe one instead of raising the
  conflict error. Already recorded in the exact head being reviewed --
  `d8d3e0d` created F-WORKTREE-5 with the fix prescribed (count candidates
  before filtering). Reversing a deliberate round-2 ordering decision in a
  review round was declined then and still is; the finding stays the owner
  of that decision. Acknowledged on the thread rather than patched.
- The hardening-doc cross-references (Codex `r3766308198`). Verified valid
  against the live tree: the dated-entries pointer claimed all three
  `2026-08-11` entries lived in PLAYBOOK Section 4, but the round-1 and
  PR #169 round-6 entries had rotated to the monolith archive, and the
  open-gap list omitted F-WORKTREE-5, which `d8d3e0d` had just added.
  Repointed the pointer at the live plus archive locations and added
  F-WORKTREE-5 to the gap list, with the recorded-in commit named.
- Suppressed comments: the plan-doc observation (the Step 3 snippet
  prescribes filter-before-count) is a true statement about a historical
  implementation plan and is left as written -- the plan documents the
  as-shipped ordering and F-WORKTREE-5 carries the forward fix; the README
  badge claim (588 vs 589) was already resolved on the reviewed head, which
  shows 589.
- Plan vs implementation: doc-only change; no code and no test changed.
- Deviations: none.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. `doc_state_sync.py --check` -- passed with
  the expected root-BATCH warning.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1.
  F-WORKTREE-5 remains the owner's call to reverse or leave.

### 2026-08-12 - PR #170 round 5; a normalizer undid the check above it (side-task)

- Scope: three findings on the round-4 head, two acted on and one recorded.
- The one that mattered. `actual_branch` was normalized with a bare
  `strip()`, which removes Unicode whitespace, and Python counts U+00A0 as
  whitespace while Git accepts it in a ref name. So `wip/batch-21` plus a
  trailing U+00A0 -- a genuinely different ref -- folded onto the expected
  branch, matched the comparison, and produced no wrong-branch verdict at
  all. On a clean checkout that is an exit-zero run reporting alignment while
  HEAD sits on another branch. Round 4 had just closed the display half of
  this class; the normalizer one line above quietly reopened the identity
  half.
- Worth recording because the first reproduction attempt said the bug was not
  there. On this host the locale codec is cp1252, so the UTF-8 bytes arrive
  mojibaked as a non-whitespace character that survives `strip()` and trips
  the comparison by accident. Under a UTF-8 locale -- Linux, and therefore CI
  -- the decode is clean and the fold happens. A Windows-only check would
  have cleared it.
- Plan vs implementation: only Git's record terminator is trimmed now. Git
  rejects CR and LF inside a ref name, so trimming exactly those cannot
  damage a legitimate value, while every other codepoint reaches the
  comparison and the render check intact.
- The second finding was a stale count in a place the round-4 sweep did not
  know existed: the README project-structure tree carries its own per-file
  test inventory, separate from the SESSION_CONTEXT table. That sweep was
  scoped to the literal total and missed it. All 35 rows were checked this
  time, not just the row reported; one was wrong.
- Deviations: the third finding is real and not fixed. Section 3 candidates
  are filtered for display safety before the conflict check, so a document
  naming one safe and one unsafe branch resolves instead of failing closed.
  Reversing that needs its own reasoning rather than a review-round patch,
  and the round-2 justification for it is itself wrong, so it is recorded as
  F-WORKTREE-5 rather than patched here.
- Validation: `pytest -q` -- **589 passed** with the 3 existing
  aiohttp/Python 3.13 warnings. All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Re-verified end to end under a UTF-8 locale against a real trailing-U+00A0
  branch: WT003 now fires where the run previously reported the wrong branch
  as aligned.
- Forward guidance: unchanged -- land PR #170, then F-SWE-1, then Batch 21
  WP-1.

### 2026-08-12 - PR #170 round 4; the third rendered ref answered to no rule (side-task)

- Scope: one finding, reported independently by both reviewers against the
  current head, and confirmed from the code before either review was read.
  `actual_branch` was the last of the three refs these diagnostics render that
  no rule governed.
- Why it outranks its predecessors. The previous two rounds closed this class
  for the ref that comes from PLAYBOOK prose; this one comes from
  `git symbolic-ref --quiet --short HEAD`, so the attacker surface is a branch
  name rather than a document. Enumerating every `issue()` call in
  `scripts/dev/` by walking the syntax tree -- rather than trusting either
  review's list -- gives six codes that print it: WT000, WT003, WT004, WT005,
  WT006 and WT010. The dangerous one is WT000, which is only reached when the
  run is otherwise clean: between batches with no dirty files the guard exits
  zero and prints a subject the branch name controls, on the line the design
  document says a less capable agent may stop on.
- What Git actually permits, established with `git check-ref-format` and real
  branches in a disposable repository rather than assumed: ESC, DEL, CR, LF
  and the ASCII space are all rejected, so a fixture built from them describes
  a checkout that cannot exist. U+00A0, U+2028, U+202E, U+200B, U+3000 and
  U+0085 are accepted, and `symbolic-ref` returns them verbatim.
- A second, narrower fact decided the fixture. `run_git` calls
  `subprocess.run(..., text=True)` with no encoding, so Git output is decoded
  with the locale codec. Under cp1252 U+00A0 survives and pads the line while
  U+2028 arrives mangled; under a UTF-8 locale U+2028 survives and splits the
  diagnostic into two. Only U+00A0 asserts the same thing on both, so it is
  the payload the tests use.
- Plan vs implementation: `branch_label` joins `base_ref_label` in the
  diagnostics module, so all three rendered refs now answer to
  `is_display_safe_ref`. The four render sites call it; the wrong-branch
  comparison keeps the raw Git value, because labelling there would compare a
  display string against a branch name. Labelling happens at render time, not
  collection time -- the snapshot goes on naming whatever Git reported.
- Deviations: the predicate had no direct test, and a mutation matrix showed
  three of its four clauses were vacuous -- deleting the `..` rule, the `//`
  rule, or the trailing `/`, `.` and `.lock` rule each left the whole suite
  green. That is why this change adds predicate tests it did not strictly
  need: without them the new docstring's claim that those boundaries are
  covered would have been false. Every clause now fails at least one test,
  and each member of the suffix tuple fails exactly one.
- `_worktree_guard_inspection.py` remains over its directory peer cap
  (F-WORKTREE-4, accepted); this change is net zero lines there and adds no
  new deviation.
- Validation: `pytest -q` -- **588 passed** with the 3 existing
  aiohttp/Python 3.13 warnings, up 12 in one existing file, so the module
  count stays 35. All 10 pre-commit hooks pass. `doc_state_sync.py --check`
  -- exit 0 with the expected root-BATCH warning. Verified end to end
  afterwards: a real branch carrying U+00A0 was created in a scratch
  repository and the shipped CLI rendered `unnamed branch` and `worktree`,
  with no payload byte anywhere in its output.
- Forward guidance: this clears the last open PR #170 item. Land the PR, then
  F-SWE-1, then Batch 21 WP-1.

### 2026-08-12 - PR #170 round 3; the gate was ordered behind what it gates (side-task)

- Scope: two document defects found by an independent clean-room audit of the
  live repository, both still live on the current head. Neither changes code
  and neither moves the test count.
- The first is the wider one. PLAYBOOK Section 3 opened with the F-SWE-1 audit
  as the next action while its own closing sentence said PR #170 must land
  before that audit begins. Section 3 is the canonical bootstrap instruction,
  so an agent reading it top-down would start the audit against the guard and
  docsync sources this PR still changes. SESSION_CONTEXT Section 1 and
  FINDINGS already carried the correct order; `BATCH21_DEFINITION.md` carried
  a third one, naming WP-1 as next with no mention of either gate. All three
  now agree.
- The second is a false statement in the round-2 entry below. "Four cases were
  added and three trimmed" is a net increase of one, which cannot explain an
  unchanged count, and it does not describe what happened: the change swapped
  a single parametrized case for another -- the DEL payload for the U+00A0
  one -- leaving six test functions and fourteen cases on either side.
  Corrected in place rather than annotated. A dated entry is a point-in-time
  record, but that protects a claim which was accurate when written and later
  went stale; it does not preserve one that was wrong at the time. That
  distinction is the same one already applied to archived citations.
- Deviations: none.
- Validation: `pytest -q` -- **576 passed** with the 3 existing aiohttp/Python
  3.13 warnings; no test changed. All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
- Forward guidance: the remaining PR #170 item is the `actual_branch` display
  gap both reviewers reported against this head. It lands next, then the PR,
  then F-SWE-1, then Batch 21 WP-1.

### 2026-08-11 - PR #170 round 2; a denylist next door to an allowlist (side-task)

- Scope: six findings from a dispatched adversarial review of the round-1
  commit -- one blocking, four should-fix, one nit. All six were reproduced
  independently before any code changed. All six were valid.
- The blocking finding: the round-1 class `[^\x00-\x20\x7f-\x9f`]+` is an
  ASCII denylist, so everything from U+00A0 upward passed. Reproduced through
  the real parser: U+00A0, U+3000, U+2000, U+202E and U+200B all resolved to
  an `expected_branch`. A value padded with U+00A0 renders in WT003 exactly
  as one padded with the ASCII space that class excluded -- the same attack
  round 1 claimed to have closed, in a different codepoint. U+200B is worse
  than cosmetic: it renders as nothing, so WT003 demands a move to the branch
  already checked out, with no exit from that state.
- Root cause, and the part worth keeping: the guard already had the right
  control. `_SAFE_BASE_REF_RE` in `_worktree_guard_diagnostics.py` is an
  allowlist, and `base_ref_label` applies it to the other ref these same
  diagnostics interpolate. Round 1 wrote a second, weaker, differently shaped
  check in another module instead of reusing it. Two values reaching one
  rendered line answered to two rules, and only one of them had been thought
  through. This is a DRY failure that produced a security defect, not a
  style complaint.
- Plan vs implementation: the shared rule is now `is_display_safe_ref`,
  extracted from the body of `base_ref_label` so both call sites share one
  definition rather than one copying the other. `BRANCH_RE` returns to
  delimiting a candidate; `parse_batch_branch` discards candidates that fail
  the predicate before the duplicate check, so an unusable value never
  becomes a branch. No dependency-graph change: lineage already imported from
  diagnostics.
- Corrections to the round-1 entry below, which stands as written because
  dated entries are point-in-time records. Two claims in it are false. The
  class was never "what Git actually permits in a ref name": Git rejects
  `..`, `^`, `:`, `?`, `*`, `[`, `\`, `@{`, a `.lock` suffix and a trailing
  `/`, all of which that class accepted, and Git accepts non-ASCII names the
  new alphabet rejects. The current alphabet is deliberately narrower than
  Git's rule because the property enforced is display safety, not ref
  validity. Separately, "all four documented Section 3 branch styles" names a
  set that does not exist; the suite pins three, and the fourth shape the
  pattern admits is documented nowhere.
- Deviations: replacing the denylist with one shared allowlist collapsed the
  test distinctions round 1 had established. Under a single control, DEL is
  indistinguishable from the escape sequence, and U+3000, U+202E and U+200B
  from U+00A0 -- every mutation that leaks one leaks its whole group. Adding
  a case per vector would have reinstated the near-duplicate rule breach the
  review had just cleared, so the parametrization keeps one representative
  per boundary the allowlist draws and names the rest in the docstring. The
  line-break case now carries no other rejected character, which is the fix
  the review asked for and which round 1 documented as a knowing breach
  rather than repairing.
- Validation: `pytest -q` -- **576 passed** with the 3 existing
  aiohttp/Python 3.13 warnings; the count is unchanged because the
  parametrization swapped one case for another -- the DEL payload was
  replaced by the U+00A0 one -- and no test function was added or removed.
  All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Every previously bypassing codepoint was re-run against the shipped parser
  and now resolves to no branch, while `wip/batch-21` still resolves and the
  live PLAYBOOK still parses.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  narrative of this remediation, including why each round produced the next,
  is written up in `docs/history/GUARD_HARDENING_2026-08-11.md` rather than
  as new rules, since three rounds of evidence is a thin basis for amending
  a ruleset every agent follows.

### 2026-08-11 - PR #170 round 1; the forgery class was wider than the line break (side-task)

- Scope: three findings from two independent reviewers on the open PR -- two
  from Copilot review `4902230481`, raised against the current head rather
  than an earlier one, and one from Codex (`r3754609766`). All three were
  reproduced before any code changed, and all three were valid.
- The fix shipped earlier the same day was incomplete. Excluding CR and LF
  stopped a forged *second line*, but WT003 renders the captured value into a
  terminal, and an escape sequence repaints the existing line without ever
  needing one: `ESC[2J ESC[H` clears the screen and redraws a clean verdict.
  DEL erases what was already written, and padding spaces push a fake result
  across the visible line. Reproduced directly: the previous pattern returned
  an `expected_branch` still carrying a raw `\x1b`. The commit message claimed
  PLAYBOOK prose could no longer forge guard output, and that claim was
  broader than the fix behind it.
- Plan vs implementation: rather than enumerate control characters, the value
  is now restricted to what Git actually permits in a ref name -- no control
  characters, no DEL or C1 range, no spaces. That subsumes the line-break case
  instead of sitting beside it, and every rejection still fails closed to
  WT002. Verified against all four documented Section 3 branch styles and the
  live PLAYBOOK, so the narrowing costs no legitimate form.
- The second finding was a test-quality defect in the same commit. The three
  parametrized line endings were near-duplicates: `parse_batch_branch` splits
  and rejoins the section, so LF, CRLF, and CR arrive at the pattern already
  normalized to LF, and deleting `\r` from the pattern left all three green.
  That is the prohibited near-duplicate pattern, shipped in the very change
  that added an adversarial test. Replaced with one parser-level line-break
  case plus three cases that survive normalization.
- The third finding was a blast-radius miss in the previous commit, and the
  more instructive one. Step 3 of the guard implementation plan still
  prescribed the original `[^`]+` value class as a normative instruction, so
  the plan remained a working recipe for rebuilding the vulnerability the
  production fix had just closed. The earlier commit had edited that same
  plan file -- for the `debug` parameter -- without sweeping it for the
  pattern actually being changed. The snippet now carries the shipped class
  plus a note saying why it must not be relaxed, so the reason travels with
  the instruction rather than living only in production code.
- Deviations: the first attempt at the DEL case did not isolate what it
  claimed. Its payload also contained spaces, so the space rule blocked it and
  a mutant permitting DEL still passed. Found by running a mutation matrix
  over the exclusion ranges rather than by rereading the test, and corrected
  by removing the spaces from that payload. Recorded because it is the same
  defect class the finding reported, reintroduced while fixing it.
- Validation: `pytest -q` -- **576 passed** with the 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Each new case was
  mutation-checked: permitting the space boundary leaks only the padding case,
  permitting the DEL/C1 range leaks only the DEL case, and the previously
  shipped pattern leaks all three non-newline cases. The retained line-break
  case adds no unique range coverage and is kept only as the single
  parser-level case the review asked for.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  lesson generalizes the one recorded below: a fix aimed at the reported
  instance rather than the class leaves the class open, and here the reported
  instance was a line break while the class was anything a terminal
  interprets.

### 2026-08-11 - PR #169 round 6 landed after the merge; the guard could be made to lie (side-task)

- Scope: four findings from Copilot review `4877974867`'s successor,
  `4888134055`. The review was submitted 2026-08-08 04:38 UTC against head
  `6ed9d7c`; the PR merged at 07:57 UTC with no commit in between. All four
  were re-verified as still live on `main` before any work started -- the
  merged head is tree-identical to `main`, so nothing had superseded them.
- Why one of them mattered more than its "suppressed" label suggested:
  `BRANCH_RE` captured `[^`]+`, a negated class that matches newlines, while
  Section 3 is parsed as one newline-joined block. A backticked Branch value
  spanning lines was therefore captured whole, and WT003 prints that value
  verbatim. Ordinary PLAYBOOK prose could forge a second diagnostic line in
  the guard's own output -- the output the design document says a less
  capable agent can stop safely on, knowing only the exit status and the
  remediation text. Reproduced before fixing, for all three line endings.
- Plan vs implementation: the label and value are now pinned to one line
  (`[ \t]*` for the separator, `[^`\r\n]+` for the value). A rejected value
  leaves no branch to resolve, which `classify_lineage` already reports as
  WT002 -- so the fix fails closed rather than silently skipping the branch
  comparison. That mattered to the choice: making malformed metadata mean
  "no branch declared" would have repeated round 4's defect, where an
  ambiguous state switched a check off instead of blocking on it.
- The other three were documentation currency: the `inspect_worktree`
  interface in the guard plan omitted the shipped keyword-only `debug`
  parameter, and SESSION_CONTEXT and FINDINGS both carried a
  `Last updated: 2026-08-06` that predated their own 2026-08-07 content.
  PLAYBOOK Section 3 was additionally stale on its own terms: it still
  directed the reader to merge PR #169, three days after the merge, and
  carried a pre-merge caveat about a missing Quality Gate run that now
  exists and is green for `5bc6294`.
- Deviations, recorded rather than taken silently:
  - **`wip/batch-21` was realigned with an owner-authorized force-push.**
    It sat 39 ahead / 39 behind `origin/main` with an identical tree -- the
    WT004 rebase-merge artifact this guard was built to catch, and the first
    live instance of it. `git cherry` confirmed zero commits without an
    equivalent patch on `main`, so the reset was lossless. Done before any
    work so the Pre-Work Checklist could pass honestly rather than be waived.
  - The session ran in a linked worktree under `.claude/worktrees/`, already
    covered by the `.claude/*` ignore rule, reusing the primary checkout's
    sole `.venv` through the qualified paths the guard printed. This is the
    first live exercise of the F-WORKTREE-2 path: the guard reported WT000
    and resolved all three tools from the primary checkout.
- Validation: `pytest -q` -- **575 passed** with the 3 existing
  aiohttp/Python 3.13 warnings (572 before; the three new cases are the
  line-ending variants). All 10 pre-commit hooks pass.
  `doc_state_sync.py --check` -- exit 0 with the expected root-BATCH warning.
  Mutation-checked: the new test was watched failing on all three variants
  before the pattern was narrowed, and the existing bold-label and
  prose-tolerance cases still pass, so the pattern was not over-narrowed.
- Submitted as PR #170 against `main` after owner instruction to push and
  open one. Both Quality Gate triggers fired on the new head, `push` and
  `pull_request` -- the dropped-dispatch gap recorded against `8463ca4` did
  not recur.
- Forward guidance: land PR #170, then F-SWE-1, then Batch 21 WP-1. The
  process lesson is narrower than round 5's: every remediation round here is
  triggered by a push, so a review submitted after the final push falls
  outside all of them and reaches the merge unswept. This entry records the
  gap; it does not create a rule, because round 5 established that a rule
  living in a dated entry has no force. Whether the pre-merge check belongs
  in the canonical ruleset is an owner decision, still open.

### 2026-08-07 - PR #169 round 5; contradicting a claim is itself a change (side-task)

- Scope: five suppressed findings, all valid, all self-inflicted. Four were
  caused by round 4 recording F-WORKTREE-4 without sweeping for the claims
  that finding contradicts; the fifth by round 4 repointing a resolver name at
  one site while an identical literal sat 300 lines earlier in the same file.
- Root cause, and the reason it recurs: the pre-push sweep had no pinned base,
  so each round swept only its own commits and inherited nothing. Round 2
  diagnosed this and fixed it by sweeping `git diff origin/main...HEAD`, but
  recorded the fix only in a dated log entry, which this repository treats as
  non-normative. Rounds 3 and 4 duly regressed. Both rules are now in the
  pre-push checklist rather than in a log entry: pin the sweep base to the
  branch, and treat recording a deviation as a change whose blast radius must
  be swept -- grepping the vocabulary of the property being deviated from, not
  the words of the new finding, which appear nowhere else.
- Plan vs implementation: five affirmative peer-cap claims repointed across
  the plan, the spec, and FINDINGS; the DOC003 description corrected to
  describe the check that shipped rather than a bare regex the implementation
  deliberately avoids; the interface inventory repointed to the authority API.
- Deviations, logged rather than silently taken:
  - **Round 3 shipped without a Section 4 entry.** Commits `14b3eac` and
    `1c783a9` carried no dated log entry, breaching the missing-log-entries
    anti-pattern in the very PR that ships a documentation-integrity gate.
    Recorded here retroactively rather than back-dated: round 3 fixed seven
    findings across the plan, the spec, AGENTS, and FINDINGS, and narrowed
    F-WORKTREE-3 after re-verifying its remaining clauses.
  - `_latest_test_count_from_entries` is left in place though no production
    caller remains, because deleting it rewrites eight test call sites --
    a refactor, not a review fix. Tracked as F-DOCSYNC-7.
- Peer-agent correction: a concurrent session had staged a partial fix that
  introduced two new false statements -- a docstring naming `_build_candidates`,
  which exists nowhere in the repository, and an attribution of the
  `_cross_validate` removal to round 2 when `a3c923f` did it in round 1. Both
  corrected here. Worth recording because it is the same defect class the
  round was fixing, produced independently by a different writer.
- Validation: `pytest -q` -- **572 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning.
- Forward guidance: merge. Round 5 was entirely documentation currency, and
  the remaining backlog is scoped as a hygiene batch rather than another round.

### 2026-08-07 - PR #169 round 4; the integrity gate could be switched off (side-task)

- Scope: eight findings from review round 4 -- one visible, seven suppressed.
  Six valid and fixed, one declined as an accepted deviation, one refuted.
- The material defect was self-inflicted by round 2. Making ambiguity an
  explicit state fixed the renderer but left `None` meaning two things at the
  integrity boundary, and DOC006 skips its comparison on `None`. Reproduced
  before fixing: with an unambiguous authority a stale dashboard value raises
  DOC006; with an ambiguous newest entry the same stale value passes and the
  gate exits 0. Writing one ambiguous log entry therefore disabled the check
  that exists to catch exactly that state.
- Plan vs implementation: the resolver now returns `TestCountAuthority`
  (count plus whether the newest entry was ambiguous) so the reason travels
  with the value instead of each consumer re-deriving it. DOC006 treats an
  ambiguous authority beside a named numeric field as blocking. Its
  remediation no longer names PLAYBOOK unconditionally, because the authority
  may be a rotated archive entry, and says to record an unambiguous result
  when there is no number to agree with. The status block distinguishes "no
  bold count" from "several counts without a `pytest -q` result", which sends
  the reader to the entry that caused it rather than to a missing number.
- Deliberate non-action: three guard files now exceed their directory peer
  caps (256/236 for the collector, 270/184 and 192/184 for two guard test
  modules). All were compliant before the review rounds and crossed while
  fixing confirmed defects. Splitting them was declined -- the rule prevents
  unmaintainable monoliths and none of these approaches that -- and recorded
  as F-WORKTREE-4 rather than left implicit, since Section 3 had described
  the guard as peer-sized and that had stopped being true.
- Refuted: the review claimed the SESSION_CONTEXT per-file table sums to 573
  against a stated 568. It sums to 568 across 35 rows, verified two ways and
  reconciled row-by-row against `pytest --collect-only` with no drift. First
  incorrect finding in four rounds; the others were all valid.
- Validation: `pytest -q` -- **572 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Both new behaviours were
  mutation-checked: neutralizing the ambiguity branch in the gate and in the
  renderer each fails its own regression.
- Forward guidance: merge. Four rounds in, the findings are now generated by
  the previous round's fixes rather than by the original work, and this round
  produced the first refuted item -- both are diminishing-returns signals.

### 2026-08-07 - PR #169 round 2; ordering, discovery, and a diff-derived sweep (side-task)

- Scope: thirteen findings from Copilot review 4877974867 -- one visible,
  twelve suppressed, all verified valid. Eleven were caused by the previous
  round's own fixes, so the round was treated as a remediation of that
  remediation rather than as new review traffic.
- Cause, established before fixing: the round-1 checklist was generated from
  the reviewers' findings, which by construction described the pre-change
  tree. Nothing was ever swept against the branch's own diff, so every
  citation that round 1 invalidated survived. Three local patches to one
  ordering question produced three interacting defects for the same reason.
- Plan vs implementation:
  - Test-count authority. Three findings were one defect: authority was
    decided by scanning three sources independently and reconciling the
    winners, so each rule was restated per source and their interactions were
    never modelled. Replaced by one total ordering -- clamped date, then
    source precedence -- walked once. Ambiguity became an explicit state
    rather than `None`, so it suppresses older candidates instead of falling
    through to them; a live side-task entry now outranks a same-date archived
    one; and the legacy sole-bold-count pass walks the same ordering, so such
    a count survives rotation. Heading dates are clamped to a running minimum
    within each source because position, not the date, is the authority on
    recency there -- which is what the existing append-convention tests
    already pinned.
  - Guard discovery. `--git-common-dir` names shared Git metadata, not a
    checkout, so deriving the primary root from its parent is wrong under
    `git clone --separate-git-dir`; the collector now asks Git directly with
    `worktree list --porcelain`. On POSIX a file without an execute bit is
    not a runnable tool, but existence was the whole test, so WT000 could
    advertise unusable paths; the doubles hid it by building tools with
    `touch()`. The base ref is no longer consulted at all between batches,
    where the contract says ancestry is not enforced.
  - Citation sweep, derived from `git diff origin/main...HEAD` rather than
    from the findings list. That derivation is what found the class the
    findings only sampled: nineteen further copies of the broken
    primary-checkout derivation sat in per-step snippets across both
    implementation plans, and the documented `resolve_venv` signature had
    drifted from production. Also repointed the WT-code location claim, both
    test inventories, and F-MAS-3.
- Deviations: added `workflow_dispatch` to `.github/workflows/test.yml` (two
  lines, urgent, logged here rather than deferred). GitHub created no Quality
  Gate run for the push of `8463ca4` although the push event was delivered
  and recorded, Actions was enabled, the workflow was active, its triggers
  matched, no path filter or skip-ci marker applied, and Copilot's own
  workflow ran on that same SHA eight seconds later. Evidence points to a
  one-off dispatch drop rather than a configuration fault, so the trigger is
  a durable escape hatch, not the fix. It cannot help this PR -- GitHub
  resolves dispatchable workflows from the default branch -- so the unblock
  is this push itself, which re-arms both `push` and `synchronize`.
- Numbers were re-measured from a live collection run, not transcribed: the
  README tree and the SESSION_CONTEXT table were regenerated mechanically
  from `pytest --collect-only`. A host-dependent skip introduced during this
  round was removed rather than kept, because it made the canonical test
  count differ between Windows and Ubuntu CI and would have desynchronized
  the documents permanently.
- Validation: `pytest -q` -- **568 passed** with 3 existing aiohttp/Python
  3.13 warnings. All 10 pre-commit hooks pass. `doc_state_sync.py --check` --
  exit 0 with the expected root-BATCH warning. Coverage 89% via
  `pytest --cov=scrobblescope`.
- Forward guidance: the review-fix loop on this PR is at the point where
  findings come from the fixes rather than from the original work, so merge
  rather than iterate. Confirm a Quality Gate run exists for the new head
  before merging; if none appears, close and reopen the PR to fire
  `pull_request` again.
