<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0015

### 2026-09-11 - DocSync integrity range corrected to DOC012

- Scope: `AGENTS.md` stated the integrity range as `DOC001-DOC011`, while
  `scripts/docsync/integrity.py` defines and raises `DOC012` -- a pass claim in
  the log must carry the bold form the count authority reads. The range drifted
  for the same reason it drifted the first time: nothing in the corpus asserts
  that the stated range equals the codes the code raises.
- Plan vs implementation: both `AGENTS.md` edits landed as written. The list
  item now reads `DOC001-DOC012`, and its parenthetical records the second
  drift, so the sentence that already held the first instance of this class now
  holds both. The added paragraph sits after the DOC009 to DOC011 bullet list
  and records that DOC012 is implemented directly rather than declared, which
  keeps the paragraph above it -- "DOC009 to DOC011 are declared, not
  hard-coded" -- true as written.
- Sweep, per Anti-Pattern 11: exactly one live document stated the range
  wrongly, and it is the one corrected here. Left deliberately, with reasons:
  `FINDINGS.md` records that `AGENTS.md` *used to* say `DOC001-DOC006` and
  remains true as history; the dated records in
  `docs/history/reports/GRAPHIFY_AUDIT_2026-09-04.md` and
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` are exempt by policy -- a
  dated record's recorded measurements are frozen, because editing one
  falsifies the record rather than correcting it, and that holds whether or
  not the range it states was already stale on the day it was written, while
  its rationale prose may be corrected when it is shown false, as this wave's
  own edit of a dated entry did; and three sites that describe
  the declared mechanism rather than the range -- the WP-3 plan's "DOC009 to
  DOC011 exist and are declared", the comment at
  `scripts/docsync/integrity.py:1017`, and the `declarations.py` line in
  `.claude/SESSION_CONTEXT.md` -- all remain true, because DOC012 is
  implemented in `integrity.py` and is not declared.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` --
  all 10 hooks passed with no files modified. `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning. The
  guard, `Select-String -LiteralPath 'AGENTS.md' -Pattern 'DOC001-DOC012'`,
  returned 0 matches before the edit and 1 after.
- Committed paths (3), recorded as the actual set: `AGENTS.md`, this entry in
  `PLAYBOOK.md`, and the rotation it forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the
  exhaustive-traversal entry out of the active window. docsync demanded no
  further path: this entry carries the 1020 claim the corpus already held, so
  `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no change.
- Forward guidance: the range is still unchecked. A guard asserting that the
  stated range equals the codes the code raises would have caught both drifts,
  and remains the fix for the class rather than for this instance.

### 2026-09-11 - Agent-session analysis trees ignored

- Scope: `.agent/`, `.impeccable/`, `.qlty/` and `scratch/` were untracked and
  also unignored, so every `git status` carried 500-odd paths and the only
  guard against sweeping them into a commit was the ban on `git add -A`.
- Plan vs implementation: the four patterns landed with a comment recording why
  each is untracked, and why the singular `.agent/` is deliberate beside the
  vendored `.agents/`.
- Deviation: the owner was offered this task as optional because it does not
  come from the traversal; it was taken.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0.
  The untracked sweep fell from 500-odd to 0, and the tracked file list was
  unchanged.
- Committed paths (3), recorded as the actual set: `.gitignore`, this entry in
  `PLAYBOOK.md`, and the rotation it forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the Task 1
  and Task 1b review-repair entry out of the active window. docsync demanded no
  further path: this entry carries the 1020 claim the corpus already held, so
  `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no change.
- Forward guidance: the traversal run root now lives under an ignored path. Its
  report was committed first, so the record survives even if the run root is
  deleted.

### 2026-09-11 - Section 3 now carries the commit debt

- Scope: the commits owed before Phase 2 were recorded only in the design-system
  plan's Progress section, so an agent bootstrapping from `AGENTS.md` reached the
  specification conflict Section 3 already carries but never learned that
  commits were owed. Section 3 now names the debt, points at the traversal
  record, and the remediation plan's Task 3 Step 3 was corrected so it stops
  instructing the stale wording.
- Plan vs implementation: both Section 3 bullets landed as written, inserted
  directly after the existing "Next action:" bullet. The bullets name the
  outstanding architecture-diagram rebuild and record the two already-landed
  commits, `95e0896` for the F-B21-51 slice-1 refactor and `c277728` for that
  plan's own move. The traversal-record citation resolves because Task 2
  committed the report.
- Deviation, controller-directed: the brief's Section 3 bullet text was written
  before `95e0896` and `c277728` landed, so it still described the F-B21-51
  slice-1 refactor as staged and the design-system plan's own move as
  uncommitted. Following it verbatim would have written a false statement into
  the live bootstrap section, so the corrected wording was used, and the same
  correction was applied to the remediation plan's Task 3 Step 3 so the plan no
  longer mandates the stale text. Nothing else in that plan changed.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  10 hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0
  with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (3), recorded as the actual set rather than a smaller claimed
  one: `PLAYBOOK.md`, the remediation plan whose Task 3 Step 3 this commit
  corrected
  (`docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`),
  and the rotation this entry forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the
  design-system plan's own path-correction entry out of the active window.
  docsync demanded no further path: this entry carries the 1020 claim the corpus
  already held, so `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no
  change.
- Forward guidance: keep Section 3's bullets free of counts. Name each owed
  item, so the next addition cannot make the section silently wrong.

### 2026-09-11 - Traversal record tense repaired after the Task 2 review

- Scope: the review of Task 2's commit `106f941` found two tense defects in
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`, both of one
  class. Its Section 7 asserted as current three passages of the design-system
  plan that `c277728` and `9cb3662` had already rewritten, and its Section 9
  past-tensed the heatmap-fill limitation the plan still states.
- Plan vs implementation: both edits landed as written. Section 7's framing
  sentence and its closing narration now report what the traversal found at the
  revision it bound, plus the one controller-authorised sentence naming
  `c277728` and `9cb3662` and recording that the finding no longer holds at
  HEAD. Section 9's limitation is present-tense again, matching the plan and
  the report's own Section 8. The three quoted passages, every chunk ordinal
  and the provenance header are unchanged.
- Deviation: none. No other section of the record was touched.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0,
  with the expected root `BATCH21_DEFINITION.md` warning.
- Forward guidance: the report records a traversal bound to the plan's
  pre-repair revision, so its findings describe that revision and not HEAD. A
  reader who needs current state must re-check the plan; Section 7 now names the
  two commits that answered it.

### 2026-09-11 - Exhaustive plan traversal recorded

- Scope: an exhaustive traversal of the Batch 21 design-system plan
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`)
  was run with the `deeper-reading` skill on 2026-09-11. Its findings are
  recorded at `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
- Plan vs implementation: 70 of 70 canonical chunks carried a byte-anchored
  evidence verdict, 192 assertions in total, with zero `non_match` verdicts and
  70 ordered `chunk_verified` events. One assertion failed its span check on the
  first attempt and was repaired by re-quoting it from the chunk; the failure,
  its diagnosed cause and the recovery are recorded in the report and in the
  run root's failure ledger.
- Deviation: none. The report is a durable copy of a working artifact, not new
  analysis.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0.
  The report is ASCII-only, measured at 0 bytes above 0x7F.
- Committed paths (3), recorded as the actual set: the report
  `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`, `PLAYBOOK.md`, and
  the rotation this entry forced in
  `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved the
  architecture-diagrams entry out of the active window. docsync demanded no
  further path: this entry carries the 1020 claim the corpus already held, so
  `FINDINGS.md` and `.claude/SESSION_CONTEXT.md` needed no change.
- Forward guidance: the machine proof stays in `scratch/`, which is untracked.
  If the run root is deleted, the report remains the record and its chunk
  ordinals stop being checkable against the manifest. Delete it only knowingly.

### 2026-09-11 - Document repairs from the Task 1 and Task 1b reviews

- Scope: two task reviews of the document-orderliness remediation found
  defects that are all documentation, and the owner approved repairing them in
  one pass rather than two fix loops, because none of them touches the code
  committed in `95e0896`. Four families: (1) the design-system plan's Progress
  section contradicted itself, still naming work that `95e0896` and `c277728`
  had discharged; (2) the remediation plan's own defects -- Task 1's guard
  expectation, Task 1's impossible staging step, Task 4's unbolded validation
  template, and a new Task 5 for the undocumented `DOC012` range; (3) two
  `PLAYBOOK.md` entries that denied behaviour their own commits had landed;
  (4) `.claude/SESSION_CONTEXT.md` Sections 3 and 4, which never listed
  `scripts/dev/_frontend_gate_colour.py`.
- Plan vs implementation: every quoted replacement landed as written, with one
  word corrected. The brief's replacement State line read "the six documents
  under `docs/architecture/`"; that directory holds five files, all modified,
  so the line names `docs/ARCHITECTURE.md` and the five documents under
  `docs/architecture/`, the same five-file scope this file's architecture entry
  and the plan already state.
- Deviation, owner-approved: this commit edits dated Section 4 entries
  committed earlier the same day -- the F-B21-51 slice-1 entry's "no behaviour
  change" claim, and WP-7's scope list. Both were wrong as written, and
  AGENTS.md keeps dated entries as point-in-time records, so the correction is
  recorded here rather than made quietly.
- Deviation, consequential: inserting Task 5 falsified two statements in that
  plan, and this commit repoints both -- the Architecture line's task count,
  and Task 4's "This is the final task" pause line, which now reads "before
  Task 5".
- Validation: `pytest -q` -- **1020 passed**; `pre-commit run --all-files` --
  all 10 hooks passed with no files modified; `doc_state_sync.py --check` --
  exit 0 with only the expected root `BATCH21_DEFINITION.md` warning.
- Committed paths (5), recorded as the actual set rather than a smaller
  claimed one: the two plans
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`
  and `docs/superpowers/plans/2026-09-11-batch21-document-orderliness-remediation.md`),
  `PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md`, and the rotation this entry
  forced in `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`, which moved
  the F-B21-51 slice-1 entry out of the active window and carried its
  correction with it. docsync demanded no further path: these entries keep the
  1020 claim the corpus already carried, so `FINDINGS.md`'s header needed no
  change.
- Forward guidance: three residual defects in the remediation plan stay,
  because this task's owner-ruled scope capped it at the reviewed findings.
  Task 1's Step 1 still says the literal "must exist in none of them afterwards"
  beside the sentence added here, which says the compliant end state is 2
  matches; Task 4 still says "Tasks 1 to 3 stand alone" without mentioning
  Task 5; and Global Constraints and Task 1's Step 7 still cite `PLAYBOOK.md`
  lines 882, 904 and 1016, which were already stale at HEAD -- the two
  `implementation_plan` references they intend sat 27 lines lower, at 909 and
  931 -- and this commit moved the marker itself from 878 to 880. Repoint those
  citations by name in that plan's next pass: a line number cannot survive the
  next entry inserted above the marker.

### 2026-09-11 - Design-system plan corrected to name its own path

- Scope: the Batch 21 design-system plan
  (`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`)
  still described itself by its pre-move repository-root name in three places,
  and its Progress "State" line counted its uncommitted work items rather than
  naming them. Both defects came from an exhaustive traversal of the plan; the
  evidence is `docs/history/reports/BATCH21_PLAN_TRAVERSAL_2026-09-11.md`.
- Plan vs implementation: all four edits landed as written. The State line now
  lists the uncommitted items instead of counting them, because a count goes
  stale the next time one appears (Anti-Pattern Registry item 13). The
  open-decision entry was rewritten in place rather than deleted, so the
  numbering of the decisions below it stays stable for any citation.
- Deviation: this commit stages the plan itself, discharging that plan's own
  "Where to pick up" item 3, which its Progress had recorded as a separate
  commit. A content correction to an untracked file is observable only once the
  file is committed, so the reorder is recorded rather than silent.
- Validation: `pytest -q` -- **1020 passed**. `pre-commit run --all-files` -- all
  hooks passed with no files modified. `doc_state_sync.py --check` -- exit 0,
  with the expected root `BATCH21_DEFINITION.md` warning. The target guard fell
  from 3 matches to 2; the two survivors name the old root path
  as history beside the new one.
- Forward guidance: the three dated references to the old root name stay as
  written -- two in this file's Section 4, one in the archive after this run's
  rotation. They record what the document said on the day it was written, and
  editing them would falsify a dated record.

### 2026-09-11 - Implementation plan moved into the plans directory and given progress tracking

- Scope: the root-level `implementation_plan.md` became
  `docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`.
  Documentation only; no code, test, or generated asset changed.
- Why: the plan was untracked and sat at the repository root, so nothing
  guaranteed it survived a session boundary, and it recorded no state at all. A
  reader could not tell which phases were done, what Phase 1 had actually
  changed, or where to resume. The plans directory is where every other plan
  lives, and the document is worth keeping: it carries the audit's repo-side
  disposition table and the reasoning behind each phase.
- Added a **Progress** section that owns the status: a per-phase state table,
  the commits landed, the uncommitted work in the order it should be committed,
  a numbered pick-up list, and the four deviations between the plan as written
  and what Phase 1 actually did. The most important of those is recorded plainly
  -- the layout was refined rather than rebuilt, because the owner's side-by-side
  ruling superseded the plan's stacked step and three frontend-gate assertions
  defend the shipped arrangement.
- The step list now points at that section instead of repeating status, so the
  two cannot disagree.
- Validation: `doc_state_sync.py --check` -- exit 0. The file now lives inside
  `docs/`, so the DOC001 path, DOC010 anchor and DOC011 retired-claim scans cover
  it; it passes all three.
- Forward guidance: the untracked
  `docs/superpowers/plans/gemini_implementation_plan_unverified.md` sits in the
  same directory and is still undecided. Resolve it when this move is committed.

### 2026-09-11 - Architecture diagrams rebuilt against the shipped system

- Scope: `docs/ARCHITECTURE.md` and the five owners under `docs/architecture/`.
  Documentation only; no code, test, or generated asset changed. This entry is
  unstaged on purpose -- it belongs with its own commit, not with the gate-slice
  commit staged ahead of it.
- Trigger: the index read "Last verified against the tree on 2026-08-15", so the
  whole set predated the later half of the Tailwind migration.
- `runtime-system.md`: `spotlight.py` and `unmatched.py` were missing entirely,
  as were the canonical routes and the JSON APIs. Added both modules and their
  import edges, route and API nodes, a `Theme` node for the `data-theme` plus
  `.dark-mode` dual write, and prose for three silent-failure facts -- one
  framework stylesheet per page, the theme dual write whose observer WP-8 must
  move in the same change, and the `_MAX_ALBUM_CAP` plus
  partition-before-Spotify cost boundary.
- `documentation-tooling.md`: `docsync.declarations` and `.docsync.toml` were
  absent, so the diagram showed no route by which a declared fact reaches
  integrity checking. Also added `FINDINGS.md` and its rotation, `docs/agents/`,
  `docs/history/`, the `ARCHITECTURE.md` index, the ten pre-commit hooks, and the
  frontend-gate toolchain with its facade and two extracted modules. The prose
  now names the DOC codes that actually bite.
- `development-cycle.md`: an annotation read "Current Batch 21 order: F-SWE-1
  audit, then WP-1", which stopped being true at WP-2. Replaced with the
  side-task path, the session-close handoff, and a pointer that the active order
  lives in PLAYBOOK Section 3 rather than in a diagram. The validation gate now
  names docsync `--check` and the frontend gate.
- `top-albums-sequence.md`: added the threshold partition and its persistence
  before Spotify, corrected the cap line to `_MAX_ALBUM_CAP` for every sort
  mode, and named the reason order on `/unmatched`.
- `heatmap-sequence.md`: added the canonical `/heatmap` page against the
  transient `/loading`, and the cached-saved-job path that keeps the loading
  panel hidden and fades the result in directly.
- Deviation, caught in this pass: the first draft put a `;` inside a mermaid
  `Note over` statement, which the Mermaid instruction file records as a parse
  failure that has shipped once already. Replaced with a full stop. Every file
  was then re-checked: no semicolon inside any fenced block, and every block
  opener has a matching `end`.
- Validation: `pytest -q` -- **1020 passed**; `doc_state_sync.py --check` -- exit
  0 with only the expected root BATCH warning; all six files ASCII-only; Mermaid
  block balance `opens == ends` in each file, 28/28 and 15/15 in the two
  sequences.
- Forward guidance: no Mermaid tooling was reachable in the session that made
  these edits, so validation was structural rather than a render. A renderer
  pass is still worth doing, and `.mmd` files remain the authoring surface.

### 2026-09-11 - Frontend gate: colour maths extracted as F-B21-51 slice 1

- Scope: `scripts/dev/_frontend_gate_colour.py` (new),
  `scripts/dev/frontend_gate.py`, `tests/scripts/dev/test_frontend_gate_colour.py`
  (new), and `FINDINGS.md`. The seven helpers moved unchanged and new tests
  were added. The same commit also lands Batch 21 WP-7's two gate assertions --
  the `data-step` 25 check and the back-to-top collapse check -- which are
  recorded in the WP-7 entry titled "Unmatched disclosure refined: 25-row step
  and collapse on return".
- F-B21-51 records that the gate is roughly ten times its largest sibling --
  4,073 lines against `tailwind_build.py` at 404 -- and prescribes a split along
  the existing check groups while `frontend_gate.py` stays a facade. This is its
  first slice. The finding now also carries the agreed module map and the
  `frontend_gate_checks.toml` registry design.
- The seven pure helpers -- `_parse_rgb_string`, `_composite_over`,
  `_relative_luminance`, `_contrast_ratio`, `_clamp_px`,
  `_worst_divider_contrast`, `_divider_contrast_failure` -- moved to the new
  module and are re-exported through the gate, so no caller has to know. That
  follows `_frontend_gate_results.py` for the module shape and
  `worktree_guard.py` for the stable facade.
- They were chosen first because they take no `page`. The browser gate is the
  artefact being moved, so it cannot be the thing that verifies its own
  refactor; these are provable with pytest alone.
- Parity: 29 tests, three of which a careless rewrite would fail -- the
  `clamp()` `vw` term must not scale with the root font size while the rem
  bounds must; worst-contrast must be the minimum across the surface list; and
  every moved name must still resolve through `frontend_gate`.
- Deviation, recorded: this commit also carries the browser assertions added
  for the WP-7 disclosure refinement (`data-step` must be 25, and back-to-top
  must collapse the panel to 10 rows with `aria-expanded="false"`). They live in
  `frontend_gate.py`'s unmatched check and belong to that work package, but the
  file is touched by both changes and separating them inside one file would need
  partial staging that the gate itself cannot verify. Flagged so the pairing is
  a recorded choice rather than a later discovery.
- Validation: `pytest -q` -- **1020 passed** (991 before the split, plus 29);
  the two-engine frontend gate -- 26 checks passed in 47 runs across chromium
  and firefox; all pre-commit hooks passed.
- Forward guidance: the remaining groups are the browser-coupled ones and still
  need the gate runnable to prove parity.

### 2026-09-11 - Agent-skills scaffolding configured; issues recorded as FINDINGS.md

- Scope: a new `## Agent skills` section in `AGENTS.md`, a narrowed
  `docs/agents/` rule in `.gitignore`, and two new files,
  `docs/agents/issue-tracker.md` and `docs/agents/domain.md`. No production
  code, test, or other document changed.
- Context: the owner ran the setup-matt-pocock-skills skill. The skill assumes a
  root context file plus a decision-record directory, and keeps its vendor
  templates under `docs/agents/`. This repo already owns that ground in the
  "Document Roles (SoC contract)" table and the anti-duplication rule, so
  `domain.md` points at those owners instead of seeding a second rule source.
- Owner decision: issues are findings. `issue-tracker.md` records `FINDINGS.md`
  as the tracker and links to `AGENTS.md` "Finding-Writing Rules" for the format
  rather than restating it. The `triage` skill is not installed, so no label
  vocabulary is written.
- Deviation, recorded rather than silent: `docs/agents/` was already gitignored,
  and its comment said adoption "belongs in its own commit". This is that
  commit, and the change is narrow -- `docs/agents/*` still hides the vendor
  seed templates, and only the two repo-authored files are trackable.
  Un-ignoring the templates would put a layout this repo rejects back into the
  repository as a second source of truth.
- Implementation note: docsync's DOC001 resolves backticked `.md` references
  against `git ls-files`, so an ignored path can never resolve and the two files
  must be staged before `AGENTS.md` links to them. Neither file names a literal
  root context path.
- Validation: `pytest -q` -- **990 passed**; `pre-commit run --all-files` -- all
  hooks passed; `doc_state_sync.py --check` -- exit 0 with only the expected
  root `BATCH21_DEFINITION.md` warning.
- Forward guidance: the design-system plan at `implementation_plan.md`
  (untracked) consumes these files. Its Phase 1 needs revision, because the
  owner's layout ruling for the unmatched report is side-by-side rather than
  stacked; Section 3 carries the refinement still owed.

### 2026-09-10 - Add isolated Results script regression coverage

- Scope: owner-requested coverage review and tests for Spotlight and leaderboard
  interactions. Sampling is server-owned and already covered by the route test.
- Implementation: six isolated Chromium tests run unmodified production scripts
  with a controlled clock. Cover rotation wraparound, late and failed hydration,
  reduced motion, numeric sorting with absent metrics, ranks and accessible
  selection, and hover delay/cancellation plus keyboard tooltip dismissal.
  CI runs this suite after installing browsers and before the frontend gate.
- Validation: six browser tests passed; `pytest -q`: **974 passed**;
  all pre-commit hooks passed. Documentation integrity and whitespace checks
  passed after the final log update.
  No application changes or dependency additions. Owner authorized committing
  this coverage and the README refresh together; pushing is not part of this step.
- **Later same-day test-count addendum:** the WP-7 current-batch entry above
  records the subsequent code change and owns its implementation details. Its
  full-suite result is `pytest -q` -- **986 passed**. The earlier 974 result
  in this entry remains point-in-time evidence; this pointer supplies the
  later same-date count to docsync's live-side-first authority order.

### 2026-09-10 - Refresh the product README against the current implementation

- Scope: owner-requested README refresh while the owner handles PR #227
  integration. No application changes or Git history operations.
- Implementation: describe current navigation, Results/Spotlight, Heatmap
  statistics and export limits, progress UI, and the remaining Bootstrap
  Unmatched report. Replace stale test/coverage figures with the live CI badge;
  shorten the file inventory and link to maintained architecture and work orders.
  Correct virtualenv installs and the init_db.py environment requirement.
- Related pointers: DEVELOPMENT now accurately distinguishes the Chromium
  matrix from the Firefox canary; CONTRIBUTING delegates setup to README.
- Validation: source-checked against templates, routes, frontend scripts,
  dependency pins, workflow configuration and deployment files. All 42 local
  Markdown links and anchors, pre-commit hooks, documentation integrity and
  whitespace checks passed.
  Owner subsequently authorized committing this refresh with the Results tests.

### 2026-09-10 - Refine Heatmap contrast and Results interaction motion

- Scope: owner follow-up on Heatmap styling, duplicate Results Top control,
  delayed Spotify hints, sorting motion and page-loading jank.
- Implementation: owner-refined sunken light-mode Heatmap frame with darker
  warm-neutral empty cells (`#c8bfad`); uppercase Input Mono
  Narrow toolbar with primary New search; supporting label grows from 12px
  to 15px in Input Mono. Results retains only the side-rail Top control.
  Spotify links reveal a shared hint after 450ms hover, immediately on focus,
  and dismiss on Escape, blur or scrolling. Ranking changes interpolate row
  positions for 280ms, with immediate reduced-motion updates. Export clones
  clear transient row animations.
- Diagnosis: delayed page_motion.js reproduced a visible-to-transparent flash
  in Chromium and Firefox before DOM readiness. CSS now starts entry at first
  styled paint; the delayed-script probe no longer reproduces the opacity dip.
  The initial header clarification was interpreted as viewport-fixed. The
  owner's later screenshot identified that persistent visibility as the
  unwanted behavior. The header now occupies document flow and scrolls out of
  view; duplicate body clearance is removed and the sticky rail uses its own gap.
- Export inspection: Heatmap uses a separate hand-drawn canvas with older
  headline/layout rules. That visual mismatch remains; the working export is
  preserved in this pass. Results export is unchanged apart from suppressing
  temporary row motion in its clone.
- Validation: `pytest -q` -- **974 passed**. The full frontend gate passed
  25 checks in 45 runs. Additional Chromium and Firefox probes covered hover
  delay, dismissal, rapid sorting, reduced motion, scroll stability, header
  scroll-away, both-theme empty-cell fills and responsive Heatmap geometry.
  Firefox CSV/JPEG checks passed at desktop and mobile widths in both themes.
  Evidence: `scratch/pressure-verify-final.txt`, `scratch/pressure-extra-final.txt`
  and screenshots. Final staged validation passes every hook, including
  generated-CSS drift and documentation sync. Owner visual
  review approved the result and authorized a safe push to PR #227. The pre-push
  sweep reconciled stale design overrides with the shipped composition. This
  remains an owner-directed side-task, not a new work package.

### 2026-09-09 - Refine Results consistency and restore navigation continuity

- Scope: owner-requested UI consistency and remediation of local Heatmap
  edits. Preserve the larger headline, sans preview labels and tighter loading
  parameters; correct the undefined legend font token. Remove the intentional
  duplicate Heatmap counter rail and its unused hydration and layout checks.
- Implementation: Results panels use an equal sRGB page/sunken mix. Sort and
  outside-filter headings use smaller uppercase sans type than Spotlight,
  centred without changing text colours. Sort labels use weight 400. The
  three toolbar actions use uppercase Input Mono Narrow with one larger gap
  step; New search retains the theme primary fill. Secondary Results actions
  and Heatmap result buttons share sans type and control fill, retaining
  proportional Results dimensions.
- Index follow-up: measured form placement lifts the composition up to 2.5rem
  from centre, bounded by 0.25rem of header clearance. Reclaiming excess
  vertical well padding removes the decade-state scrollbar at 1920x900 and
  1536x730 in both engines, with thresholds collapsed and scale unchanged.
  Mobile retains its existing padding. `scratch/index-offset-evidence.json`
  records five desktop window sizes per engine.
- Motion: browser samples confirmed existing entrances and a fixed header.
  Shared keyframes make page entry independent of first-paint timing; normal
  internal links fade content out before navigation, and Back restores it.
  Reduced motion remains immediate. Heatmap loader/result stages overlap
  during their existing opacity handoff. The header remains independently fixed.
- Export: the browser resolves the mixed surface to RGB in the JPEG clone
  because html2canvas cannot parse modern computed colour functions. The live
  page retains its theme-derived mix. Export clones suppress entry animation.
- Validation: `pytest -q` -- **974 passed**. Focused Chromium and Firefox
  probes cover desktop/mobile, both themes, scaling, header scroll position,
  button and heading consistency, navigation, Back and Heatmap completion.
  Evidence: `scratch/ui-consistency-evidence.json` and accompanying screenshots.
  Full frontend gate: 25 checks passed in 45 runs. Additional Firefox checks
  pass for both-theme desktop/mobile exports and the complete layout/state
  matrix. All hooks pass except committed-CSS drift: the regenerated file
  intentionally differs from the index while this work remains unstaged.
  A second build produces identical bytes. Docsync and whitespace checks
  pass. No commit or push.
- Deviation: an editing helper briefly misdecoded existing UTF-8 punctuation.
  Tests caught it; original bytes were restored before the passing suite.
- Forward guidance: owner visual review before publication. WP-7 remains
  next batch work; Task 6 stays deferred until Bootstrap removal.
