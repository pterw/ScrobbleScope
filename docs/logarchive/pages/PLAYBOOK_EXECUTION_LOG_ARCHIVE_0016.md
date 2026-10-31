<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0016

### 2026-09-13 - Legacy framework stack retired (Batch 21 WP-8 sweep)

- Scope: the WP-8 sweep, run before the backend batches on the owner's ruling
  of 2026-09-13. The frontend and accessibility audit is not here; it moved to
  Batch 23's close-out so it runs once over the final UI.
- Removed: the default-on `legacy_css` block and the `bootstrap_js` block in
  `templates/base.html`, the eight per-page opt-outs that answered them, and
  `static/css/global.css`. WP-8's deterministic check,
  `git grep -nE "bootstrap|data-bs-|bs-(toggle|target|dismiss)" -- templates static`,
  now returns nothing. No other stylesheet is unreferenced: every file in
  `static/css/` is loaded by a template or compiled by the build.
- The theme is written once. `static/js/theme.js` no longer writes
  `.dark-mode` on `<body>`; `data-theme` on the root element is the only
  signal.
- **A regression the sweep would have shipped.** `static/js/heatmap.js`
  observed `<body>` for that class to repaint zero-count cells, because a cell
  carries its colour as an SVG `fill` attribute and a presentation attribute
  does not resolve a custom property. Retiring the class silently froze the
  cells at their light colour on a dark page, and the whole gate stayed green:
  every other theme check reads CSS. `docs/architecture/runtime-system.md` had
  recorded this dependency and named the fix; reading it is what caught this.
- Guards added, each seen to fail first: the gate's
  `check_heatmap_zero_cells_follow_theme` toggles the theme and compares each
  zero cell against `--heatmap-empty` (it failed with `#c8bfad` in both themes
  before the observer moved), and two tests in `tests/test_template_shell.py`
  pin the retired stack and the single theme write.
- Linting disposition recorded: `BATCH21_DEFINITION.md` WP-8 carries the
  decision, and the `AGENT_NOTES.md` gap entry now points at it instead of
  reading as an open commitment.
- Docs: README's status section, `docs/architecture/runtime-system.md` (both
  bullets this change falsified), and the `tests/test_template_shell.py`
  docstring.
- Validation: `pytest -q` -- **1034 passed**. `python scripts/dev/frontend_gate.py`
  -- **27 checks passed in 49 runs** across chromium and firefox.
- Forward guidance: what remains before Batch 21 closes is the owner's
  end-to-end pass in Firefox, including the saved image in both themes, and
  the close-out commit. Batch 22 opens on its own branch, named in Section 3
  first.

### 2026-09-12 - Documentation reconciled to the shipped unmatched page

- Scope: the documentation-first step the owner chose before the WP-7 table
  repair. Corrected claims that contradicted the shipped unmatched page, by class
  rather than by instance, using two subagents on disjoint file sets.
- The approved spec: its Outcome and Verification paragraphs still described
  full-width stacking, and the second credited the frontend gate with proving
  it; its disclosure paragraph described one button and no step. All now state
  side-by-side panels, the 25-row step and the collapsing back-to-top control.
- `PLAYBOOK.md` Section 3 carried two stale live test counts, 1022 and "the
  925-test suite"; the second now defers to the next-action bullet. Its conflict
  note pointed at the one spec sentence already corrected, not at the two stale
  sites; it now records the conflict as closed.
- `BATCH21_DEFINITION.md`: the stacked-layout prescription, "is next" for shipped
  work, "two reason cards" where three ship, and a false claim that
  `unmatched.css` hardcodes `--header-bg: #6a4baf`. `README.md`: two passages
  telling readers the unmatched report still runs Bootstrap. `FINDINGS.md`:
  F-B20-4's stale status, and F-B21-52's grep instruction, which could not find
  whole-number dead steps.
- `docs/design/RECONCILIATION.md`: section 11 still said `results.css` and
  `unmatched.css` were unconverted to rem; sections 13 to 15 record the frozen
  snapshot's 1180px measure, card styling and two-state expander as overrides,
  since `docs/design/` is byte-frozen apart from that file.
- Plans under `docs/superpowers/plans/`: normative "must report 1020 passed"
  baselines now defer to SESSION_CONTEXT Section 1; the WP-7 plans and the
  unverified gemini plan carry supersession records for the side-by-side ruling
  and the 25-row step. Dated log excerpts inside them were left as records.
- Deviation: F-DOCSYNC-11 filed. Same-date precedence ranks this morning's live
  side-task entry above the WP-7 entry written after it, so the WP-7 entry's
  count could not become authoritative and DOC006 and DOC008 failed. This entry
  carries the working tree's full-suite result instead.
- Validation: `pytest -q` -- **1028 passed**, on the working tree that also holds
  the WP-7 table repair and the F-B21-52 guard.
- Forward guidance: dated Section 4 entries and log excerpts quoted inside plans
  are point-in-time records and stay as written.

### 2026-09-12 - Planning records preserved, and the ignored scratch root cleaned

- Scope: preserve the untracked planning record ahead of Phase 2 in
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`,
  and empty the `scratch/` root. No product code changed in this entry.
- Committed: the four untracked plans under `docs/superpowers/plans/`, plus the
  Progress corrections on the reconciliation plan itself. Keeping
  `gemini_implementation_plan_unverified.md` here closes that plan's open
  question 2 in favour of keeping.
- Deviation, owner-directed: live mode was repaired mid-session, then reverted.
  The skill's pinned engine `0.1.0` is quarantined by Windows Defender; the
  published `0.1.2` release is not, and its hash matches the release's own
  `.sha256` sidecar. The two template edits made under live are reverted, and
  the helper, poll and session are stopped and discarded.
- Cleaned, owner-directed: `scratch/` held 499 files and 31.05 MB of session
  debris and is empty now. The `deeper-reading-batch21-plan/` run root went
  with it. The durable summary of that run is the tracked
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`, which states in
  its own text that the run root is untracked and is not committed.
- Validation: `pytest -q` -- **1026 passed**; `pre-commit run --all-files` with
  every hook passing; `doc_state_sync.py --check` exit 0, with the root
  `BATCH21_DEFINITION.md` warning expected while Batch 21 is active.
- Owner rulings recorded: the eyebrow labels are intended; any reference
  placing an eyebrow above its headline is stale; headline emphasis stays and
  is scoped to the index hero and `results.html`.
- Forward guidance: begin Phase 2 at step 11 (`DESIGN.md`), not at the
  spec-versus-ruling conflict, which is already closed.
  `static/js/heatmap.js:176` is the one stale eyebrow-above comment and is
  corrected inside that unit. Two harness notes: this shell runs with
  `$ErrorActionPreference=Stop`, so a tool that writes to stderr looks like a
  hard failure until that is set to `Continue`; and the git `pre-commit` hook
  resolves `pre-commit` from `PATH`, so the primary venv must be on `PATH` or
  every commit is blocked.

### 2026-09-11 - Artwork restored in the below-threshold panel

- Scope: a review observation that the artwork container is excluded for
  `below_threshold` items, contradicting the spec's "consistent 40px mobile or
  44px desktop artwork" and breaking the side-by-side rhythm.
- Root cause, verified: `templates/unmatched.html` wrapped the whole artwork block
  in `{% if reason_key != 'below_threshold' %}`. The stylesheet was correct all
  along -- `.unmatched-artwork` is 2.5rem, and 2.75rem at >=768px. The guard
  conflated "these albums have no album image" (true: they are partitioned before
  Spotify) with "these rows get no artwork"; the block's fallback branch needs only
  the artist name, which the payload carries (`unmatched.py:79-80`).
- Plan vs implementation: a below-threshold branch now renders the sized monogram
  placeholder. Variant chosen by the owner: no `data-artist-image`, so the panel
  adds no network call and partitioned albums stay at zero cost. The change is
  additive -- nine lines above the existing guard, nothing removed.
- Why no gate caught it: `frontend_gate.py` asserted the cover on `rows[0]` of ONE
  group, the release_scope panel. It now asserts a sized `.unmatched-artwork` in
  EVERY `.unmatched-group`, which is the class fix rather than the instance.
- Evidence, both guards proved to fail before passing: with the new branch removed,
  `tests/test_routes.py::test_unmatched_view_renders_artwork_in_every_reason_group`
  fails, and the frontend gate reports "unmatched group 0 renders no artwork
  container" for desktop and mobile. Restored, the test passes and the gate reports
  26 checks passed in 47 runs. `pytest -q` -- **1026 passed**.
- Deviation: none. This is a defect the PR review round surfaced and fixed inside
  the same round.

### 2026-09-11 - Deterministic tie-breaks on the three cap-path sorts


- Scope: a PR review comment on `scrobblescope/orchestrator.py:131` and `:703`
  asked for a stable tie-breaker on the sorts that choose albums for the
  `_MAX_ALBUM_CAP` safety cap, so tied play counts cannot let insertion order
  decide which albums are kept.
- Plan vs implementation: all three cap-path sorts now order by descending play
  count and then by normalized key. The reviewer named two; the third is the
  playcount pre-slice in the same function, added as the same class. The
  now-unused `cast` import was removed.
- Evidence: the fix's failure mode was OBSERVED, not assumed. With the three keys
  reverted to `reverse=True`, all three new tests fail; restored, all three pass.
  `pytest -q` -- **1025 passed**, up from 1022 with the three new tests.
- Deviation: none in scope, and one correction to record. The determinism the
  reviewer worried about was not reachable before this change: the cap's input is
  built by iterating page results in order, `partition_albums_by_threshold`
  preserves that order, and the sort is stable. So this makes the guarantee
  structural instead of inherited from a four-link chain nothing pinned, rather
  than fixing a live bug. Recorded so a later reader does not overstate it.
- Forward guidance: two same-class sibling sorts remain at `orchestrator.py:538`
  and `:540`, in `_build_results`' user-visible ordering. They were NOT fixed
  here: the review did not name them, their input order derives from `cache_hits`
  and was not established as nondeterministic, and every further site costs its
  own fixture and its own claim. Bounded deliberately rather than chased -- the
  same reasoning that parked the dated-record policy sites. A future pass wanting
  the class closed should do all remaining sites in one edit.

### 2026-09-11 - Approved spec reconciled with the owner's side-by-side ruling


- Scope: the approved spec
  `docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md`
  still directed "stacked, full-width reason sections" while the owner ruled
  side-by-side on 2026-09-11 and both the shipped page and three frontend-gate
  assertions implement side-by-side. A PR review comment raised it; it was the
  last stale voice on that conflict.
- Plan vs implementation: the directive now reads as side-by-side panels and
  records the supersession, the owner's words and the date. The rest of the spec
  is unchanged and still accurate.
- Deviation: none. This is the reconciliation the design-system plan's Phase 2
  named ("Record that the owner superseded its ... line with the side-by-side
  ruling"); it sits outside the document-orderliness series' declared scope and is
  logged here rather than folded silently into that series.
- Validation: `pytest -q` -- **1022 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0 with
  only the expected root `BATCH21_DEFINITION.md` warning.
- Forward guidance: the design-system plan's Phase 2 still lists this edit among
  its work. It is now done, so that entry can be retired when Phase 2 runs;
  `RECONCILIATION.md` gains a pointer to the same ruling in that pass.

### 2026-09-11 - Two siblings closed, and the dated-record policy scoped


- Scope: the scoped re-review of the fix wave `50cffdd` ruled that two
  same-class siblings belonged to that wave, and the owner directed it be
  extended by one follow-up commit. Three document edits: a rationale reworded
  in a dated entry, the work order's retired provenance pin, and the policy
  clause in the side-task archive.
- Owner ruling on the policy fork: a dated entry's recorded measurements are
  frozen -- a test count, a date, an observed result stands as written, because
  editing one falsifies the record rather than correcting it -- while its
  rationale prose may be corrected when it is shown false. `50cffdd` had
  replaced the archive's rationale with an absolute clause that condemned that
  wave's own edit of a dated entry, so it contradicted itself; the clause is
  now scoped to the ruling.
- Sibling (a), precision rather than retraction: the re-review classified the
  stale-range bullet in the dated entry "Architecture rebuild landed, and its
  stale docsync range corrected" as the same falsified claim finding 2
  corrected. The controller disproved that on authorship timing: the rebuilt
  `docs/architecture/documentation-tooling.md` was authored at 2026-09-11
  23:15:13, and `501a7b6` corrected the range in `AGENTS.md` at 2026-09-12
  00:57:38, one hour forty-two minutes later, so at write time the document
  agreed with the range's authority. The dated records finding 2 left alone are
  the opposite case: DOC012's 2026-08-26 enforcement had already made them
  stale on their own dates. The sentence is true as written, so nothing was
  retracted; it now reads "It matched `AGENTS.md` when written", which removes
  the ambiguity about what "correct" meant.
- Sibling (b): the work order's Task 2 Step 3 still reproduced the retired
  sha256 and byte-count pin for a plan revision that was never committed, so no
  contributor could check it. It now names `c277728`, the commit that published
  that plan, and records that the traversal bound the pre-publication revision
  -- the precedent the traversal report already sets.
- Validation: `pytest -q` -- **1022 passed**. `pre-commit run --all-files` --
  all 10 hooks passed with no files modified. `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (3), recorded as the actual set: `PLAYBOOK.md` (this entry
  and the sibling (a) reword), the work order
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`,
  and `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which carries the
  scoped policy clause and the rotation this entry forced -- the oldest
  non-current entry, the one sibling (a) lives in, moved into the archive, so
  the correction travels with it. docsync demanded no further path: this entry
  carries the 1022 claim the corpus already held, so `FINDINGS.md` and
  `.claude/SESSION_CONTEXT.md` needed no change.
- Forward guidance: a future agent correcting a dated entry changes rationale
  only, and leaves every measured figure, date and observed result as written.
  One absolute statement of the old form survives, in this file's entry "Task 8:
  the guard's own spelling, a false rationale, a live count", which gives the
  same reason as "editing one falsifies the record rather than correcting it".
  That entry is a dated record of the wave's own reasoning, so it was left as
  written; a pass that wants one form in the corpus should scope it by the same
  ruling.

### 2026-09-11 - Task 8: the guard's own spelling, a false rationale, a live count

- Scope: the six items of the final whole-branch review of this series -- three
  Important findings and three one-line recommendations, all of them documents
  except one test assertion. No application behaviour changed. One gate
  behaviour moved: Guard A's pattern now blocks on a second spelling of the
  retired range. The review's verdict was "ready to merge with fixes" over the
  23 commits from `b5b2c89` to `0c87eaa`.
- Important 1: Guard A's pattern -- the `[[retired]]` declaration named "the
  docsync integrity range ends at DOC011", at `.docsync.toml:616` -- could not
  match the spelling of the instance it was built for. The declaration was
  written for `docs/architecture/documentation-tooling.md:93`'s backtick-split
  `` `DOC001`-`DOC011` ``, and the pattern required the contiguous literal. The
  pattern now reads `(?:reports|returns|states).{0,40}DOC001`?-`?DOC011`, so
  both spellings match and nothing else does. The declaration's comment claimed
  the pattern "requires the literal `DOC001-DOC011` phrase", which the widening
  falsifies; it now names both spellings and says why the backticks are
  optional.
- NO LIVE RED STATE WAS AVAILABLE for that widening, and none was manufactured
  to produce one. Task 6 corrected the backtick-split instance in `cc987f5`,
  before Task 7 designed the guard, so at calibration time the only surviving
  example of the defect was the plain form inside a plan's spent before-block --
  which is why the pattern was fitted to the wrong spelling. The evidence is a
  five-case probe rather than a red-then-green cycle. Measured through
  `docsync.declarations._declared_matches`, old pattern then new: backtick-split
  `` It reports typed `DOC001`-`DOC011` issues `` False then True; the plain
  `It reports typed DOC001-DOC011 issues` True then True; a corrected
  `` `DOC001`-`DOC012` `` line False then False; the true
  "**DOC009 to DOC011 are declared, not hard-coded.**" False then False; and a
  past-tense record naming the old range False then False.
- Important 2: the entry named "DocSync integrity range corrected to DOC012"
  justified leaving two dated records alone by saying they "were correct when
  written", and the ledger falsified it: DOC012 has been enforced since
  2026-08-26 (`1c78aa0`), so `docs/history/reports/GRAPHIFY_AUDIT_2026-09-04.md`
  and the archive entry that carries the same range already stated a retired
  range on their own dates. The decision to leave them stands. The reason is now
  the policy -- a dated record is a point-in-time entry, so editing one falsifies
  the record rather than correcting it -- which holds whether or not the range
  it states was stale on the day it was written.
- Important 3: `PLAYBOOK.md:189`, in Section 3's live next-action bullet, read
  **1020 passed** while the suite is 1022. A live bootstrap field that no gate
  reads, which is why it drifted: DOC006 and DOC008 cover the named
  SESSION_CONTEXT fields and the `FINDINGS.md` header, and DOC012 reads only
  below the execution-log heading. It now reads **1022 passed** with the
  measurement date beside it.
- The three recommendations. The traversal report's provenance header no longer
  pins the traversed revision by sha256 and byte count: that revision was never
  committed, so no contributor could ever check the pin, which is the
  unreachable-citation shape Anti-Pattern 11 names. It now records that the
  traversal bound the pre-publication revision that `c277728` published. The
  facade test at `tests/scripts/dev/test_frontend_gate_colour.py:194` asserts
  `is` identity rather than `callable()`, so a facade exporting an unrelated
  function of the same name fails it; the test is parametrized, so extending it
  added no test function and the suite count did not move. And the
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`
  work order gained a section after its task list naming Task 6 and Task 7 as
  the owner-directed additions, so it stops understating the series.
- Validation: `pytest -q` -- **1022 passed**. `pre-commit run --all-files` --
  all 10 hooks passed with no files modified. `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning. The probe
  above was re-run after the widening, with the pattern read back from
  `.docsync.toml`, and returned the new column unchanged.
- Committed paths (6), recorded as the actual set: `.docsync.toml` (the widened
  pattern and the comment above it), `PLAYBOOK.md` (this entry and the Section 3
  count), `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`,
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`,
  `tests/scripts/dev/test_frontend_gate_colour.py`, and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which this entry's arrival
  pushed over the four-entry window: the reworded Important 2 rationale rides in
  the rotated entry, so the correction is preserved in the archive rather than in
  Section 4. docsync demanded no further path: this entry carries the 1022 claim
  the corpus already held, so `FINDINGS.md` and `.claude/SESSION_CONTEXT.md`
  needed no change.
- Forward guidance: Guard A now covers both spellings of the retired range, so
  the live coverage gap it had is closed -- but it still matches *wording*, and
  a document stating a fresh-phrased range behind the code passes it; Guard B is
  the check for that, and the two do not subsume each other. Two residuals the
  review did not name are reported rather than fixed here, because the brief
  scoped this wave to its six items: the Task 6 entry named "Architecture rebuild
  landed, and its stale docsync range corrected" still carries the same "correct
  when written" rationale about a document, and the work order's Task 2 Step 3
  still reproduces the report's old provenance pin in its instruction block.

### 2026-09-11 - The docsync code range is guarded, and its stale copy removed

- Scope, four parts in one owner-directed task: declare the retired DOC011
  range in `.docsync.toml` and remove the one live site it exposed; add a
  derived test comparing the range `AGENTS.md` states with the highest code the
  package raises; close the design-system plan's commit table; record it here.
  No application behaviour changed, and the docsync gate gained one check.
- Two guards, because there are two failure modes and neither subsumes the
  other. Guard A is a `[[retired]]` declaration whose pattern matches the
  PRESCRIPTIVE phrasing, so a stale range re-appearing in any live document
  blocks. The pattern was widened during review from the `typed` form alone to
  any of the three present-tense verbs it lists, which is what caught Task 5's
  preamble in the remediation plan; a still wider form had been measured and
  rejected for flagging true sentences instead. It catches stale
  *wording* only: a document stating a range merely behind the code, in fresh
  wording, passes it. Guard B is
  `test_stated_docsync_range_matches_the_highest_code_raised`, which asserts
  through a shared `_ranges_agree` predicate that `AGENTS.md`'s stated upper
  bound equals the highest code literal in
  `scripts/docsync/*.py`; it catches a documented range that is behind the
  code. Guard B is the one that would have caught the original drift, and it
  already catches a `DOC013` added without the documentation following -- a
  case Guard A cannot see, because such a document quotes no retired range.
- Red state observed before the fix. With the declaration in place and the plan
  untouched, `doc_state_sync.py --check` exited 1 with ERROR DOC011 against
  `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md:602`,
  the spent before-block of Task 5's Step 3. The narrow pattern matched exactly
  one live site, which is what its calibration predicted; a broader form had
  been measured and rejected for flagging true sentences instead. Replacing that
  block with a note naming the commit that applied the correction, `501a7b6`,
  and quoting neither wording, returned `--check` to exit 0. Widening the
  pattern during review put it back to exit 1 with a second live diagnostic, on
  Task 5's preamble in the same plan; a past-tense rewrite of that sentence
  cleared it, and `--check` returned to exit 0 again.
- Guard B's mutation proof, `test_stated_range_helper_rejects_a_stale_range`,
  asserts both failure modes through the same `_ranges_agree` predicate the
  corpus test uses: a fixture document still stating the retired range beside a
  source raising `DOC012`, and the real `AGENTS.md` beside a source raising
  `DOC013`. Without them the corpus test would still pass if both helpers
  returned one constant. The fixture is assembled at runtime, because a literal
  copy of the retired range sits outside the declaration's `scan` list by file
  type alone, and widening that list would otherwise make guard A fail on the
  fixture that proves it works.
- The design-system plan's commit table gained three rows -- `c277728`,
  `95e0896`, `cc987f5` -- the commits its own progress section already tracked
  as dischargeable items. Rows for commits that merely touch that plan were not
  added, so the table stays bounded to its window.
- Validation: `pytest -q` -- **1022 passed**. `pre-commit run --all-files` --
  all 10 hooks passed with no files modified. `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning. The two
  new tests are why the count moved from 1020, so `.claude/SESSION_CONTEXT.md`
  Section 1 and the `FINDINGS.md` header moved with it.
- Committed paths, in `d41f05c` (8): `PLAYBOOK.md` (this entry), `.docsync.toml`,
  `tests/test_docsync_integrity.py`, both plan documents
  (`docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`,
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`),
  `.claude/SESSION_CONTEXT.md`, `FINDINGS.md`, and the rotation this entry
  forced in `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. The review round
  that widened the pattern committed six of those same paths -- this entry,
  `.docsync.toml`, `tests/test_docsync_integrity.py`, `FINDINGS.md` and both
  plans -- and its `--fix` run rotated nothing. The three
  untracked plan and design files owned by other efforts stayed untracked.
- Forward guidance, all of it still open. Guard B compares the upper bound
  only, so the lower bound the same sentence states is unchecked, and the
  retired-range pattern assumes the range is stated in the present tense. Guard
  B's literal scan covers `scripts/docsync/*.py` alone, so a code first raised in
  another module would need that glob widened. Nothing in the toolchain parses
  Mermaid, so a diagram's labels stay unchecked prose. `F-B21-57` records a
  latent index shadowing in `check_retired`, where a declaration-shaped
  diagnostic survives on statement order alone. The `--fix` run rotated the
  oldest non-current entry into the archive to hold the window at four.

### 2026-09-11 - Task 6 review fixes: diagram claims and the handoff list

- Scope: the five findings of the Task 6 review of `cc987f5` and `29486d8`, all
  documentation, none touching behaviour or a gate. (1) The design-system plan's
  handoff list still presented three landed commits as staged or unstaged,
  contradicting its State line twenty lines above. (2) A Mermaid node in
  `docs/architecture/documentation-tooling.md` named pre-commit's code checks
  `ruff, flake8, bandit`, when this repository runs ruff alone. (3) The Task 6
  entry immediately below counted "the four citing edits" over a list of three.
  (4) That entry cited "the six architecture documents above" without naming one
  of them. (5) The same tooling document put pip-audit before the frontend gate
  in CI and omitted CI's deliberate `worktree-alignment` skip.
- Toolchain evidence, read from the configuration rather than assumed:
  `.pre-commit-config.yaml` defines ten hooks -- ruff-check, ruff-format,
  trailing-whitespace, end-of-file-fixer, check-yaml, check-merge-conflict,
  detect-private-key, doc-state-sync-check, tailwind-css-drift and
  worktree-alignment -- and its own comment records that ruff replaces black,
  isort, autoflake and flake8. Neither flake8 nor bandit is pinned in
  `requirements-dev.txt`, defined as a hook, or named in a workflow step; the
  surviving mentions are prose records and one comment in
  `scrobblescope/spotlight.py`. The node now reads `ruff check, ruff format`.
- CI order, read from `.github/workflows/test.yml`: pre-commit with
  `SKIP: worktree-alignment`, then pytest with coverage, then the Playwright
  install, then the frontend gate, then advisory pip-audit last. The prose now
  states that order and the skip.
- The contradicted list, repaired with discharge markers rather than a retitle:
  each of its three items names the commit that discharged it, which is what
  "Where to pick up" already does. A retitle alone would have left "Unstaged:"
  standing with no outcome beside it, the defect the Task 3 review raised for
  the sibling Section 3 bullet.
- Validation: `pytest -q` -- **1020 passed**; `pre-commit run --all-files` --
  all 10 hooks passed with no files modified; `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (4), recorded as the actual set: `PLAYBOOK.md` (this entry),
  `docs/architecture/documentation-tooling.md`, the design-system plan
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`),
  and the rotation this entry forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the Section 3
  commit-debt entry out of the active window.
- Forward guidance: nothing checks a diagram against the workflow it describes,
  so an edit to the hook set or to the CI step order has to move both this
  document's Mermaid node and its CI sentence by hand.

### 2026-09-11 - Architecture rebuild landed, and its stale docsync range corrected

- Scope, three parts in one owner-directed task: correct the stale integrity
  range in the rebuilt `docs/architecture/documentation-tooling.md`; commit the
  owed architecture-diagram rebuild, unstaged in this worktree since 2026-09-11;
  and sweep the two documents that still tracked that rebuild as uncommitted
  work, so nothing claims owed work that has landed.
- Owner direction, outside the remediation plan: this task is not one of the
  plan's WPs, and the plan excluded the rebuild as owed work owned by another
  document. Landing it had to precede the docsync-range guard, because that
  guard cannot ship while a live stale instance exists, and the instance lived
  inside this uncommitted work -- correcting the line alone would have dragged
  52 unstaged lines into a guard commit. Owner ruling, 2026-09-11.
- The stale range: the rebuilt `documentation-tooling.md:93` read "reports typed
  `DOC001`-`DOC011` issues". It matched `AGENTS.md` when written and a later
  correction made it stale: `501a7b6` corrected the same range in `AGENTS.md`, and this
  file had not yet entered the repository. The sweep measured the class in four
  spellings (`DOC001-DOC011`, `` `DOC001`-`DOC011` ``, `DOC001 to DOC008`, and
  the short form `DOC009-011`); this was the only live statement of the range
  with a wrong upper bound, and every other hit is true as written, a quotation
  of the old text, or a dated record.
- Deviation, forced by commit identity: the brief staged the plan's State line
  and Section 3's owed-work bullet in the same commit as the rebuild, each
  citing the rebuild's SHA. A commit cannot cite its own SHA, because the
  citation is part of the tree that SHA hashes. The rebuild therefore landed as
  the first commit of this task, and the citing edits -- the plan's State line,
  its previously-owed item 2, and Section 3's bullet -- landed in the
  immediately following commit, which names the rebuild. No brief text was
  reworded; only the commit boundary moved.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  10 hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0
  with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (9), recorded as the actual set: the six architecture
  documents -- `docs/ARCHITECTURE.md`,
  `docs/architecture/development-cycle.md`,
  `docs/architecture/documentation-tooling.md`,
  `docs/architecture/heatmap-sequence.md`,
  `docs/architecture/runtime-system.md`,
  `docs/architecture/top-albums-sequence.md` -- this entry in `PLAYBOOK.md`, the
  design-system plan whose owed-work notes this task discharged
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`),
  and the rotation this entry forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. docsync demanded no
  further path: this entry carries the 1020 claim the corpus already held, so
  `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no change. The nine
  paths span two commits, per the deviation above; the six architecture
  documents and this entry are in the first.
- Forward guidance: the rebuild is the last owed commit before Phase 2, so
  Section 3 now reads "none". The docsync-range guard can land unexempted,
  because no live stale instance remains in the corpus.
