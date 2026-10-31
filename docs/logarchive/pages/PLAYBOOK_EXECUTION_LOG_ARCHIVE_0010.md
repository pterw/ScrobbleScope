<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0010

### 2026-08-25 - DOC009 to DOC011: facts written down more than once (side-task)

- Scope: closed the buildable half of `F-B21-17`. Three declared integrity
  checks in a new `scripts/docsync/declarations.py`, driven by a new
  `.docsync.toml` at the repository root. No new dependency; the declarations
  are TOML read with `tomllib` from the standard library.
- Why: six of the nineteen Codex comments across PR #216 and PR #218 were not
  logic defects. They were one fact recorded in several places where the
  copies had drifted. The clinching case was a cross-reference that named its
  target by heading, exactly as `F-STYLE-1` asks, and broke in the same commit
  that moved the heading. A written rule cannot catch that; only something
  that resolves the reference can.
- Plan vs implementation: DOC009 compares a value across its sites, DOC010
  resolves a citation shape against the document it names, DOC011 keeps a
  retired claim out of anything that still prescribes. Four behaviours were
  added after the first run reported false positives on real documents, and
  each is a property of how this repository actually writes: bold lead-ins
  count as citable places, a heading cited without its trailing parenthetical
  resolves, a label's trailing sentence is not part of its name, and
  struck-through text is already marked as not current.
- What the first run found, before any test was written:
  - **`static/css/shell.css` used `max-width: 860px`** where every other
    stylesheet uses `859.98px`. Both the mobile and the desktop rules
    therefore applied at exactly 860px. Fixed.
  - **`AGENTS.md` described the integrity codes as DOC001-DOC006**, four
    checks after that stopped being true. Fixed, and the line now says when
    it went stale, because that is the same class the new checks exist for.
  - Two stale citations, one of them inside the finding that proposed the
    check.
- Deviations: the declarations file is at the repository root as
  `.docsync.toml` rather than under `docs/`. It is configuration, it sits
  beside `.pre-commit-config.yaml` and `.gitattributes`, and keeping the
  repository-specific half out of `scripts/docsync/` is what lets that
  package be lifted into another repository unchanged.
- Validation: `pytest -q` -- **771 passed**, 3 warnings, 22 of them new. All
  11 pre-commit hooks pass with an identical `git write-tree` either side.
  Each of the three checks was proved against the real defect it was built
  for, by restoring that defect and watching the check name it. Five
  mutations of the module each killed exactly one test and no others.
  `doc_state_sync.py --check` exits 0. The frontend gate is unaffected and
  still reports 8 checks in 13 runs.
- Forward guidance: add a declaration when a fact starts living in two
  places, not after it drifts. `F-B21-18` is the other half and is not
  started -- browser JavaScript with no unit runner, to be reached through
  a guarded seam onto the Chromium the frontend gate already pays for, not
  through npm.

### 2026-08-24 - F-B21-13 docsync bootstrap gate remediated (side-task)

- Scope: closed `F-B21-13` with DOC007 and DOC008 on
  `wip/f-b21-13-docsync-gate`, branched from `origin/main` at `658bdb2`;
  WP-3 remains on `wip/batch-21`.
- DOC007 now has one next-WP calculation. The managed SESSION_CONTEXT
  renderer owns `_next_wp_number()`, the integrity check calls that helper,
  and the CLI supplies the active definition's finite plan. Absorbed,
  dropped and merged WP headings are skipped; a fully completed plan
  terminates with no next package instead of looping forever, while any stale
  numeric next-WP claim left at close-out is blocking. The definition Status
  line, PLAYBOOK Section 3's actual Next action bullet, and SESSION_CONTEXT
  Section 1's sole active Batch status row are checked for the same active
  batch and next WP. Historical claims outside the bullet and earlier claims
  superseded inside it cannot steal the comparison.
- DOC008 applies `latest_test_count_authority()` to the FINDINGS.md header
  with findings-specific remediation. Authority includes live entries, the
  side-task archive and per-batch logs; a same-date tie between batch logs is
  resolved by numeric batch chronology rather than filename insertion order.
- Review remediation also repaired two misleading DOC007 fixtures so their
  asserted WP ranges really sit inside the current-batch markers, and made
  DOC008's error invariant say the header count "must agree" instead of
  claiming that a detected mismatch already agrees. Every new edge case was
  observed failing before its minimal fix.
- Deviations: the owner authorized expanding the original PR file set on
  2026-08-24 after the audit proved DOC007 and the renderer computed different
  next-WP values. The expansion is limited to the renderer/sync/CLI data path
  and its directly related docsync tests; no unrelated refactor was taken.
- Validation: `pytest -q` -- **717 passed**, 3 warnings (was 682; 35 new
  tests across the docsync integrity, renderer, logic, CLI and count suites).
  The focused docsync suite is **219 passed**.
- Forward guidance: WP-3 should still update the definition Status line as
  an explicit task. The gate proves agreement; it does not replace writing
  the canonical status correctly.

### 2026-08-23 - PR #216 review round three applied (side-task)

- Scope: two review comments on `e9bac27`, both real rendering defects in
  WP-2's own shell commit. Both were verified in a browser before any edit.
- **The header wordmark ignored `prefers-reduced-motion`.** The lockup
  carried five SMIL `<animate>` elements with `repeatCount="indefinite"`.
  No CSS can pause SMIL, so the media query in `shell.css` never reached
  them. WP-2 made the exposure much worse: the mark moved from per-page
  hero content that scrolls away into a fixed header that is on every page
  and never leaves the viewport. `docs/design/README.md` already prescribed
  the remedy and says the SMIL must be stripped and the bars animated from
  CSS. Done, with the keyframes taken from `docs/design/tokens/base.css`.
- **A wrong assumption was caught by measuring.** The origin looked like it
  needed a 7-unit correction, because this lockup's viewBox starts at y=7
  where the full mark starts at y=0. It does not: `view-box` resolves
  `transform-origin` in the SVG user coordinate system, not from the
  viewBox corner. At `scaleY(3)` the proposed 56.5px slid each bar bottom
  8.4px and the canonical 63.5px held it to 0.2px. Under the shipped 1.10
  scale the gap is under half a pixel, so eyeballing would have missed it.
- **The back-to-top control lost its layout.** `base.html` used to wrap the
  theme toggle and `page_footer_extra` together in `.page-footer-bar`. WP-2
  moved the toggle into the header and removed the wrapper with it, but
  `results.html` still fills that block and `#back-to-top` has no CSS of its
  own anywhere. Centring, gap, padding and entrance all came from the
  wrapper, so the control shipped bare and left-aligned. Restored in
  `shell.css` rather than `global.css`, which only reaches unmigrated pages.
- Both guards were proven able to fail. Putting one `<animate>` back fails
  five tests, reflowing the wrapper onto three lines fails four, and
  dropping the reduced-motion `opacity: 1` fails one.
- Deviations: the frontend gate gained no reduced-motion check. Its checks
  take a page rather than a browser, so a second context needs a signature
  change, and that is a refactor rather than a review fix. The template
  tests cover the markup and the CSS; the computed behaviour was verified
  by hand this round.
- Findings: `F-B21-5` updated rather than closed. The header instance is
  resolved; the pinwheel and the index hero wordmark still carry SMIL and
  belong to WP-3.
- Validation: `pytest -q` -- **682 passed**, 3 warnings. All 11 pre-commit
  hooks pass. The frontend gate reports `5 checks passed`.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: strip the SMIL from the remaining two assets the same
  way. Do not reach for `svg.pauseAnimations()` -- the CSS route is what the
  design contract asks for and it needs no JavaScript.

### 2026-08-23 - PR #216 review round two applied (side-task)

- Scope: two review comments on `4105aef`, both documentation. Both were
  verified against the files and both were valid.
- **The batch definition still said WP-2 was next.** PLAYBOOK Section 3 and
  `SESSION_CONTEXT.md` Section 1 both said WP-3. `AGENTS.md` makes those
  three agreeing the condition for bootstrap to complete, so the next agent
  would have stopped on the disagreement. `git log -S` puts the line's last
  edit in `7c00754`, the WP-1 commit. WP-1's plan listed updating it as a
  task and WP-2's did not.
- **The findings header still published 666 tests.** The round-one commit
  moved PLAYBOOK and SESSION_CONTEXT to 671 and left that copy behind. It is
  the instance-not-class anti-pattern `AGENTS.md` names, committed inside the
  commit that was fixing stale documentation.
- Every other `666` in a tracked document was checked rather than assumed.
  The remaining three are dated log entries that were accurate when written,
  so they stay.
- **`F-B21-13` filed for the class.** Neither line is read by any gate.
  `doc_state_sync.py` derives the next work package from PLAYBOOK and never
  reads the batch definition, and the test-count enforcement in
  `scripts/docsync/integrity.py` covers SESSION_CONTEXT only. The definition
  status line has now gone stale twice -- PR #170 corrected it once for
  WP-1 -- which is the point at which `AGENTS.md` prefers a mechanical check
  over another written rule.
- Deviations: the gate was not extended in this round. It is a change to the
  integrity checks every work package depends on, and scope discipline puts
  that in a finding rather than in an open UI PR.
- Validation: `pytest -q` -- **671 passed**, 3 warnings. All 11 pre-commit
  hooks pass. `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: WP-3 should carry updating the definition status line as
  an explicit task, the way WP-1 did, until `F-B21-13` closes.

### 2026-08-23 - PR #216 review round one applied (side-task)

- Scope: three review comments Codex left on `45fbbe8`. All three were
  verified against the code and all three were valid. None was declined.
- **Tailwind was pruning tokens the handwritten CSS reads.** Tailwind v4
  emits a theme variable only when a generated utility uses it.
  `static/css/error.css` reads `--font-figure`, `--font-weight-bold`,
  `--spacing-8`, `--radius-sm` and `--radius-lg` directly, no utility used
  them, and none reached `static/css/tailwind.css`. An undefined `var()`
  with no fallback voids the whole declaration, so the error page shipped
  with no card rounding and no page padding, and its status number took
  neither the bold weight nor the Gotham face. Nothing failed and nothing
  logged. `@theme static` fixes it and adds 16 declarations to the compiled
  file. A browser now reports 14px card rounding and 32px 16px page
  padding.
- **No page set `font-family` on `body`.** Neither `global.css` nor
  `shell.css` carried one, so the four unmigrated pages downloaded the
  Adobe kit and then rendered in the Bootstrap system stack. The batch
  definition lists the body font as a WP-2 deliverable, so this was a
  missed one rather than a new idea. The declaration went into `shell.css`
  behind a new `--shell-font-sans` token, because an unmigrated page never
  loads the compiled stylesheet and `var(--font-sans)` resolves to nothing
  there.
- **`SESSION_CONTEXT.md` sections 3 and 4 were stale.** They said 9 css and
  7 js files, still listed a deleted `error.js`, and omitted `shell.css`,
  `frontend_gate.py` and the lockup SVG. Real counts are 10 and 6.
- Two gaps closed while in the same files. `tests/test_template_shell.py`
  gains a test that renders each page, reads back the stylesheets it loads,
  and asserts every `var()` without a fallback resolves in one of them.
  Nothing checked that invariant before. The gate gains a fifth check for
  the body font, reading computed style rather than stylesheet text,
  because the failure is a cascade one and only a browser can settle it.
- Deviations: the dependency graph also gained `dev/tailwind_build.py`,
  which WP-1 added and never recorded. It was a one-line omission in the
  block being corrected, so leaving it was worse than fixing it.
- Both fixes were proven able to fail. Reverting `@theme static` fails two
  tests, and removing the body declaration fails the gate on `/` and names
  the system stack it fell back to.
- Validation: `pytest -q` -- **671 passed**, 3 warnings. All 11 pre-commit
  hooks pass. The frontend gate reports `5 checks passed`.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: the compiled stylesheet is 1,650 lines now, so every
  line citation into it is stale again. Cite the block, not the number.

### 2026-08-23 - Node 20 CI deprecation filed as F-B21-12 (side-task)

- Scope: recorded a warning the Quality Gate has started printing. No
  workflow change, no dependency change, no code change.
- Plan vs implementation: `F-B21-12` filed. Four pinned actions in
  `.github/workflows/test.yml` -- `actions/cache`, `actions/checkout`,
  `actions/setup-python` and `actions/upload-artifact` -- target Node 20,
  which GitHub deprecated. Runs are forced onto Node 24 and pass, so nothing
  is broken today.
- Why file it: all four sit in one file and fail together on the day the
  forced fallback is withdrawn. That break would land on whichever work
  package is open, would look unrelated to its diff, and would block every
  PR at once. The finding says to bump them in their own commit and to read
  each action's releases rather than guess the major that carries the new
  runtime.
- Deviations: none.
- Validation: `pytest -q` -- **666 passed**. All 11 pre-commit hooks pass.
  `doc_state_sync.py --check` exits 0 with the expected active
  root-definition warning.
- Forward guidance: not urgent, but the deadline belongs to GitHub rather
  than to this repository. Do it as a standalone commit, not folded into a
  UI work package, because every other work package depends on that gate.

### 2026-08-22 - Tailwind citations renamed after the rescope (side-task)

- Scope: 13 line citations in `FINDINGS.md` and
  `docs/design/RECONCILIATION.md`. No code changed.
- Codex caught this on PR #173. It is correct.
- The `source(none)` comment moved `tailwind.src.css` down five lines. The
  rescope cut `tailwind.css` from 2,289 lines to 1,576. Every citation into
  either file broke at once. `:root:not([data-theme])` moved from 2042
  to 1335.
- The citations now name the block or the declaration: the two
  `@plugin "daisyui-theme.mjs"` blocks, `--spacing-*`, `--radius-*`,
  `--font-sans`, `--font-mono`, `--font-weight-medium`,
  `@custom-variant dark`, `prefersdark: true`. Named anchors do not drift.
- Checked the citations Codex did not flag. `heatmap.js:14-22`,
  `heatmap.js:25-26`, `theme.js:17`, `base.html:26` and `index.css:158` all
  still resolve. Those files did not change.
- This is `F-STYLE-1` happening again. The rule already exists for
  `AGENTS.md`. It applies to every file. Cite a name, not a number.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**.

### 2026-08-22 - Open findings mirrored to GitHub issues (side-task)

- Scope: created issues #174-#215. Rephrased two rules in `AGENTS.md`. Filed
  `F-B21-9`. No code changed.
- Why: Codex raised `F-B21-7` on PR #173 although the PR body listed it.
  Reviewers do not read `FINDINGS.md`. Issues are cheaper to search.
- 42 open findings are now mirrored: 28 P1, 10 P2, 3 Info, 1 Feature. Seven
  resolved findings were skipped. Labels are `finding` plus the severity.
- Each issue body says `FINDINGS.md` is the source of truth and that the
  issue is a read-only mirror. Nothing writes back to the file.
- `AGENTS.md` changes are rephrases, not additions. Bootstrap item 7 already
  said "read on demand"; it now names the three reasons to open the file and
  says a recorded defect is known and owned. The Markdown log-entry bullet
  now also asks for plain English. No new rule was added.
- `F-B21-9` records the gap. The mirror is manual and will drift. The owner
  accepted that on 2026-08-22 and asked for it to be written down rather
  than built now. A sync script is code and needs its own work package.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**.

### 2026-08-22 - PR #173 review answered, two import defects fixed (side-task)

- Scope: moved `docs/design/styles.css`. Fixed one claim in
  `docs/design/RECONCILIATION.md`. No code changed.
- Codex raised four threads. All four are correct. Claude disputed none.
- `styles.css` went into `docs/design/tokens/`. It belongs one level up.
  The file imports `tokens/fonts.css`. From inside `tokens/` that path does
  not exist. So the entry point loaded no tokens.
- The source project keeps `styles.css` at its root. `DesignSync list_files`
  confirms this. `git mv` fixes the path. The content does not change.
- `RECONCILIATION.md` said every colour in the README tables matches the
  theme. That is wrong. Three tokens match: `--surface-page`, `--text-strong`
  and `--accent`. Four are absent. Dark `--surface-sunken` is `#181520`, not
  `#1a1622`. The status colours are still Bootstrap's.
- A per-token table now replaces the claim.
- This is the second false claim of this shape in that file. `F-B21-8`
  records the first. Both came from a spot check.
- The other two threads repeat `F-B21-7`. Codex found them on its own. They
  stay with WP-2. WP-2 owns that code next.
- Checked this pass: only `RECONCILIATION.md` changed under `docs/design/`.
  The imported files match `fa56cd6`. Claude's Markdown has no non-ASCII.
- Validation: `pytest -q` -- **633 passed**. `doc_state_sync.py --check`
  exits 0. `pre-commit run --all-files` passes.
- Next: **WP-2**. It inherits `F-B21-7` and `F-B21-8`.

### 2026-08-22 - Tailwind source scope corrected after PR #173 went red (side-task)

- Scope: `static/css/tailwind.src.css` (one directive plus a comment), the
  regenerated `static/css/tailwind.css`, `FINDINGS.md` (`F-B21-8`), and the
  false claim in `docs/design/RECONCILIATION.md` section 2. Owner chose the
  fix and the recording from two options each.
- Trigger: PR #173's Quality Gate failed on "Verify committed Tailwind CSS".
  Not a flake. The rebuild added 30 lines the committed file did not have.
- Cause: `@source` **adds** to Tailwind v4's automatic detection instead of
  replacing it, so the whole repository was scanned, not just `templates/`
  and `static/js/`. The extractor turns bare words in Markdown into class
  candidates, so prose compiled into utilities -- `.contents`, `.isolate`,
  `.flex`, `.border`, `.relative`, `.sticky`, `.truncate`, `.italic`.
- The design import did not create this; it exposed it. The committed
  baseline was already contaminated. Scoping the scan removed **713 of 2,289
  lines, 31% of the stylesheet**.
- Fix: `@import "tailwindcss" source(none)`. Rejected alternatives, both
  offered to the owner: regenerate as-is, which would couple the design
  documentation to production CSS permanently; and `@source not "../../docs"`,
  which fixes only `docs/` and leaves `tests/`, `scripts/` and the root
  Markdown feeding the scanner.
- Verified rather than assumed: both theme blocks survive (`--color-base-100`
  is `#faf8f3` light and `#0e0c12` dark, and `data-theme` still appears three
  times), and a second consecutive build reproduces the first byte for byte.
- Deviations: two `@source not` directives are now unreachable and were left
  in place deliberately, as protection if `source(none)` is ever removed.
  Recorded in `F-B21-8`.
- **Process failure worth naming.** Last session's check,
  `git diff --exit-code -- static/css/tailwind.css`, was reported as proof
  that `docs/design/` was outside Tailwind's scope. It proves only that the
  file was not hand-edited. The build has to actually run. `F-B21-8` records
  that nothing local runs it, which is what WP-2's `tailwind-css-drift` hook
  closes.
- Validation: `pytest -q` -- **633 passed**, 3 warnings.
  `doc_state_sync.py --check` exits 0. `pre-commit run --all-files` passes.
  Quality Gate re-run on PR #173.
- Forward guidance: **WP-2 is next** and should treat `F-B21-7` and `F-B21-8`
  as its own, since the drift hook it adds runs both code paths.

### 2026-08-22 - Two WP-1 review items filed as F-B21-6 and F-B21-7 (side-task)

- Scope: `FINDINGS.md` only -- two new findings plus the stale status header.
  No code changed. Filed before opening the Batch 21 PR so the branch is
  self-describing rather than leaving a reviewer to rediscover them.
- Both items came out of the five-agent WP-1 review on 2026-08-20 and were
  carried in local notes, unfiled, ever since. Each was re-verified against
  the code before filing; neither was taken on the review's word.
- `F-B21-6`: `routes.py:135,302,436` use naive `datetime.now()`. Line 436
  gates the requested year against host-local time while
  `orchestrator.py:70-71` builds the fetch window in UTC, so gate and window
  disagree by the host offset near New Year. They agreed before F-SWE-2,
  which fixed the window and left the gate. Production runs UTC, so this is
  a developer-host defect.
- `F-B21-7`: two defects in the WP-1 toolchain. The one test naming the
  integrity property patches both `required_artifacts` and `ensure_artifact`,
  so no integrity code runs. **Verified by mutation:** deleting
  `bin_dir=bin_dir` from `tailwind_build.py:293` leaves the full suite at
  633 passed. The review had claimed only the 35 toolchain tests stay green;
  the real blast is the whole suite. Separately,
  `http.client.IncompleteRead` subclasses `HTTPException`, not `OSError`, so
  it escapes both handlers as a raw traceback -- confirmed from the MRO --
  and a cleanly truncated download surfaces as `SHA-256 mismatch`, which
  reads as tampering rather than a network fault.
- Deviations: none. The mutation was reverted with `git checkout --` and the
  working tree confirmed clean before anything was staged.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; the only
  Python touched was the mutation, which was reverted.
  `doc_state_sync.py --check` exits 0. `pre-commit run --all-files` passes.
- Forward guidance: **WP-2 is next.** It should absorb `F-B21-7`, because the
  `tailwind-css-drift` hook it adds runs the same code path. `F-B21-6` is
  independent of the UI batch and needs no WP of its own.

### 2026-08-21 - SESSION_CONTEXT batch status row resynced (side-task)

- Scope: `.claude/SESSION_CONTEXT.md` Section 1 only -- the Batch 21 status
  row and the "Last updated" date. No code, no gate, no Section 3 change.
- Why: the row still read "the owner-approved root-hygiene side task is next,
  then WP-2". That side task closed on 2026-08-20, and two further side tasks
  landed on 2026-08-21. PLAYBOOK Section 3 was correct throughout; only the
  snapshot was stale.
- Three earlier commits caused the drift. Each updated PLAYBOOK and left this
  row alone. `AGENTS.md` "What to update after a WP or side-task commit"
  requires SESSION_CONTEXT Section 1 to move when the batch status changes.
- Not a gate failure, and nothing would have caught it. `doc_state_sync.py`
  manages the STATUS block in Section 2, which was correct the whole time.
  Section 1 prose is hand-maintained and unchecked.
- The row now also names `docs/design/README.md` as the canonical design spec
  and `docs/design/RECONCILIATION.md` as the override list, so a bootstrapping
  agent finds the design tree from the state snapshot.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; no Python
  touched. `doc_state_sync.py --check` exits 0. `pre-commit run --all-files`
  passes.
- Forward guidance: **WP-2 is next**, unchanged. Section 1's batch row is the
  first thing a bootstrapping agent reads for state. Update it in the same
  commit as the PLAYBOOK entry, never afterwards.

### 2026-08-21 - Size rule restated as intent in AGENTS.md (side-task)

- Scope: rewrote Proposal and Design Rules item 3 in `AGENTS.md`. One rule, no
  other rule touched, no code touched. Owner-authorised.
- Plan vs implementation: the rule read "No new file should be larger than the
  largest peer in its directory", which is the proxy metric rather than the
  intent, and it is the example `CLAUDE.md` had been carrying as the model for
  the planned trim. It now states the intent: the rule is against god files,
  not line counts; a file large because its job is large is fine; the peer
  comparison is the check you run when you notice scope creep, not a threshold
  to clear. Owner's framing, given 2026-08-21.
- This also resolved a contradiction inside the same list. Item 5 already said
  "SoC/DRY is the constraint on file content, not line count", which item 3
  denied. They now agree.
- Checked before writing, not after: `F-WORKTREE-4` and `F-MAS-3` are the only
  other places that restate the cap, and both already carry the correct
  reading -- "the rule exists to prevent unmaintainable monoliths" and "size
  was never the defect". Neither was edited; item 3 now cites both.
- Deviations: one, and it matters. The rewrite grew the item from three lines
  to eight, so every `AGENTS.md` line citation past it moved by five. This is
  the same drift that made `F-STYLE-1` cite 254, 262 and 550 when the real
  lines were 255, 263 and 551. One live citation was affected --
  `docs/design/RECONCILIATION.md` pointed at the ASCII rule by line. It now
  names the section instead, and `CLAUDE.md` records the rule: cite
  `AGENTS.md` by section or rule name, never by line.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; no Python
  touched. `doc_state_sync.py --check` exits 0. `pre-commit run --all-files`
  passes.
- Forward guidance: WP-2 is still next. When the wider `AGENTS.md` trim
  happens, do it this way -- one rule at a time, intent replacing the proxy
  metric, and re-grep line citations afterwards because they will move.

### 2026-08-21 - Front-end design handoff imported to docs/design (side-task)

- Scope: imported the owner's Claude Design project
  (`7d95e96a-613b-4017-9dd7-8b74d2db9535`) into `docs/design/`, recorded where
  it diverges from the batch contract, and filed two findings. No runtime code
  changed. WP-2 keeps its own reserved commit.
- Plan vs implementation: the source project holds 207 files; 61 are imported
  verbatim through the design MCP -- the canonical `README.md`, 10 token files,
  24 components as `.prompt.md` plus `.d.ts`, and two subordinate references.
  The import is a curated subset and says so; everything else stays reachable
  through the MCP, and `RECONCILIATION.md` section 2 tables what was left
  behind and why. Claude added a 62nd file,
  `RECONCILIATION.md`, because a verbatim snapshot states the Adobe Typekit
  stack and the `.dark` marker as fact and the owner has overridden both;
  without an override list a later agent reading only the specification would
  implement the wrong thing. `docs/AGENT_DOC_MAP.md` gains a row so the tree is
  discoverable.
- Owner decisions, all made this session: (1) the type stack stays self-hosted,
  so `BATCH21_DEFINITION.md:155-158` decision 4 stands and kit `rwy8ghw` is not
  adopted; (2) `docs/design/README.md` is canonical and is the default over
  both files in `reference/`, but it does not automatically retire an audit
  finding; (3) curated text-only import; (4) import only, one commit.
- Deviations: none against the approved plan, but two of its assumptions were
  corrected by evidence found while importing. The plan treated the mobile
  input size as a live conflict; it is not -- the canonical bundle's own
  `components/forms/Input.prompt.md` mandates 16px or larger on mobile, which
  matches the shipped override at `static/css/index.css:158`. `F-B21-5` records
  it as settled rather than open. The plan also assumed the component layer
  followed the Adobe stack; it does not -- `Button.d.ts` and `Input.d.ts` name
  JetBrains Mono, so the self-hosted mapping agrees with most of the bundle.
- Verified against code, not accepted from the documents: the seven `rocket_r`
  stops in `static/js/heatmap.js:14-22` match the specification exactly; every
  hex value in both colour tables matches `static/css/tailwind.src.css:69-137`;
  the three accessibility defects in `F-B21-5` were each confirmed at the line
  cited. The unmatched-grouping bug the design review names was already in the
  batch contract at `BATCH21_DEFINITION.md:25-27` and is not filed again.
- `docs/` is excluded from every pre-commit hook by `.pre-commit-config.yaml:2`
  and sits outside Tailwind's `@source` scope, so the import cannot rewrite the
  specification's Unicode or move `static/css/tailwind.css`. Both were checked.
- Validation: `pytest -q` -- **633 passed**, 3 warnings. Unchanged; this commit
  touches no Python.
- Forward guidance: WP-2 is still next and its scope is unchanged. Before
  starting it, read `docs/design/RECONCILIATION.md` section 5 -- the theme
  marker resolves to `data-theme="dark"` on `<html>` at `templates/base.html:2`,
  which satisfies daisyUI, the WP-2 contract and the specification at once.
  WP-3 must measure label and hint widths at 9-11px: there is no narrow
  JetBrains Mono, so the clipping regression the specification warns about is
  live here rather than avoided. `F-B21-4` must not be closed by ruling on all
  four screens at once; each is decided at the WP that builds it.
