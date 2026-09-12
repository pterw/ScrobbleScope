# Batch 21 design-system plan: exhaustive traversal findings

Recorded 2026-09-11 for the repository's own record. The traversal itself was
run with the `deeper-reading` skill against
`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`,
and it bound that plan's pre-publication revision -- the revision `c277728`
published later the same day.

Coverage: 70 of 70 canonical chunks, 192 byte-anchored assertions, one recorded
failure and its recovery. The machine proof (chunk manifest, evidence ledger,
run ledger, rendered traversal report) lives in the untracked run root
`scratch/deeper-reading-batch21-plan/`; it is not committed, and this report is
the durable summary of it.

Chunk ordinals below are cited as `[n]`. Sections read together in the source
appear as ranges `[n-m]`.

---

## 1. The document outranked itself, and the body was not its history

The single most consequential property of this plan is that **its Progress
section supersedes its own body**, and it says so twice:

- Progress `[2]`: "**Owner of this status: this section. Do not restate it in
  [Implementation Order]; update it here.**"
- Implementation Order `[60]`: "**Step status is not tracked here. The Progress
  section above owns it** -- one place, so the two cannot disagree."

Progress `[2-3]` records Phase 1 as **done and committed** and Phases 2-5 as
**not started**. The body's Phase 1 section `[62]` still lists steps 4-10 as
work to do, with an instruction to write failing assertions first. Those steps
are already discharged: step 10's commit `fix(ui): Align unmatched report with
Results` landed as `57d1474` `[3][5]`. A reader who had worked the numbered steps
in order without reading Progress would have re-done completed work.

## 2. Four recorded deviations meant the body was deliberately not a faithful record

Progress `[8]` records four divergences from the plan as written, and explains
why they are recorded rather than silently corrected: "the plan above still
reads as written and a future executor should not treat it as a faithful record
of what happened."

1. **The layout was not rebuilt.** The plan's Phase 1 step 5 said to restructure
   the report into stacked full-width sections. The owner's ruling is
   side-by-side, and three frontend-gate assertions defend the shipped
   arrangement. Phase 1 refined instead of rebuilding.
2. **Three refinements came from skills, not the plan** -- the `daisyui` colour
   rule moving the panel count off `primary`, its usage rules justifying
   Results' panel padding, and the `frontend-design` pass justifying the
   reason-detail wrap.
3. **The step size was chosen, not specified** -- the owner allowed "20 or 25";
   25 is live `[9]`.
4. **A pre-existing data-integrity defect was found and fixed in passing**: a
   stale `.collapse` utility in `static/css/tailwind.css` no source produces. It
   entered with `72615ed`, **not** with Phase 1 `[8]`.

## 3. Two audit claims were corrected rather than followed

The plan does not treat the audit as ground truth `[11]`:

- **`--index-scale` does not have 102 consumers.** Measured 111 occurrences in
  `static/css/index.css` alone. The plan's instruction is explicit: "Do not
  publish a count. Re-measure across every sheet before quoting one, or describe
  the mechanism without a number (Anti-Pattern Registry item 10)."
- **`--shell-accent-ink` is not live.** Its only consumers are inside
  `global.css`, "a file no page loads". The instruction is to resolve it **by
  deletion with `global.css`, not by re-pointing it** -- the opposite of what
  the audit implies.

## 4. One audit instruction was a trap and one was mechanically impossible

`[10]` states both, and both are handled explicitly elsewhere in the document:

- **The trap.** Retiring `global.css` and the `.dark-mode` write together
  "silently breaks the heatmap's zero-count cells, because `heatmap.js`
  `initDarkModeObserver()` observes `document.body` for `class` and nothing else
  watches a theme toggle." Phase 4 `[21]` repeats the constraint: the observer
  must move to `data-theme` on `documentElement` **in the same commit**, "or a
  theme toggle silently leaves every zero-count cell painted in the previous
  theme's colour and no gate notices." Progress `[3]` flags the trap in the
  phase table itself.
- **The mechanical error.** F-B21-23's `stroke: var(--bars-color)` "cannot be a
  presentation attribute, because the audit's own section 4 proves an SVG
  presentation attribute does not resolve a custom property." The Container-class
  contract `[36]` gives the correct home: an SVG `<style>` element for the
  stroke, and `fill="currentColor"` as an attribute because a keyword does
  resolve. Getting it backwards ships a fixed colour in one theme "with no error
  anywhere, which is exactly how F-B21-21 shipped."

## 5. A blocking conflict sat before WP-8, and the plan named it

`[7]` and the Overview `[10]` agree: the approved spec
`docs/superpowers/specs/2026-09-11-unmatched-threshold-horizontal-report-design.md`
still says "stacked, full-width reason sections", while the owner ruled
side-by-side and the shipped page is side-by-side. The instruction was to start
Phase 2 there because it "actively misleads", and `[17]` added that `PLAYBOOK.md`
Section 3's next-action bullet still points at the document the ruling
overrode -- so an agent following Section 3 literally "rebuilds the rejected
layout and the frontend gate fights it."

Assumption 6 `[69]` supplies the stop condition: if the side-by-side ruling were
wrong, "Phase 1 changes shape entirely and should be stopped before it starts",
because rebuilding the layout the owner asked for would fail three existing
frontend-gate assertions.

## 6. The plan said what it could not claim -- and that was part of the work

The audit-disposition table `[67-68]` is not padding. It records that:

- **D-1..D-34 cannot land in this repository.** The `docs/design/` snapshot is
  byte-frozen; `tests/test_design_snapshot.py` pins a 61-file digest and exempts
  only `RECONCILIATION.md` and `designsystemaudit.md` `[10]`. Corrections land in
  `DESIGN.md` and `docs/design/RECONCILIATION.md`.
- **`docs/design/designsystemaudit.md` must not be edited** `[17]` -- "a dated,
  self-correcting record whose later sections supersede its earlier ones."
- **Seven root tooling files, `app.py` and `scrobblescope/` are out of scope and
  explicitly not claimed** `[68]`: "no document written under this plan may
  assert anything about them." Limitation `[69]` repeats that claims about
  server-authored copy, KPI payloads, phase labels and `page_navigation`
  "remain unverified here."

A skim that reads only the phase tables would miss that this document forbids
its own reader from asserting certain things.

## 7. The document contradicted its own location

Three passages still described the file at its old root path:

- `[25]`: "| `implementation_plan.md` (this file) | A working plan, not a
  governed document. Decide before the first commit whether to keep it ... so it
  does not become another undeclared root file."
- `[69]` open decision 1: "**Would `implementation_plan.md` be kept or
  removed?**"
- `[70]`: "The only file created is `implementation_plan.md`."

The file lived at
`docs/superpowers/plans/2026-09-11-batch21-design-system-reconciliation.md`, and
Progress `[6]` listed that move as one of the three uncommitted work items. So
the plan's own self-reference by name was stale in the same way the audit's
citations were, and decision 1 was partly answered by the move having happened.
This was the drift Anti-Pattern Registry item 11 covers, and it was invisible
unless the header and the tail were both read. All three passages were repaired
afterwards in `c277728`, and `9cb3662` then dropped the move from Progress's
uncommitted-work list, so this finding no longer holds at HEAD.

## 8. Operational constraints a skim would have dropped

- **The validation sequence is ordered and failure-gated** `[44-46]`: `pytest -q`,
  `pre-commit run --all-files`, `python scripts/dev/tailwind_build.py`,
  `python scripts/dev/frontend_gate.py`, `node --check static/js/unmatched.js`,
  `python scripts/doc_state_sync.py --fix`, then `--check` -- "Run in order and
  do not advance on a failure." Then confirm
  `git diff --exit-code -- static/css/tailwind.css` is clean.
- **The staging order is a known open question, and the plan says to record what
  you did rather than reorder the procedure** `[46]`: "Per F-B21-20 the
  documented order (hooks before staging) and the Tailwind drift hook disagree;
  stage the named paths, run the hooks, verify the named paths are unchanged,
  and record the order actually used in the WP log entry."
- **`.docsync.toml` edits need an immediate check** `[46]`: run `--check`
  "immediately after editing `.docsync.toml`, before any other work in that
  phase", because new declarations are exactly what turns a green corpus red.
- **Guards must be shown to fail** `[39]`: the mutation is to be stated in the
  docstring or the WP log -- restore `font-weight: 500` and the weight sweep
  must fail; revert `attributeFilter` to `['class']` and the heatmap fill check
  must fail; set `data-step="50"` and the expander assertion must fail. "A guard
  whose failure mode was never observed is an assumption, not a test."
- **Nine browser-gate checks are assigned to phases** `[43]`, including the one
  that watches nothing today: zero-count heatmap cell `fill` on theme toggle
  (phase 4) and the ten/ten wrapper theme check for the inline marks.
- **Dependency stance is closed** `[37]`: no package added or removed, no new
  Node project, `playwright==1.62.0` already pinned, Tailwind and daisyUI
  versions unchanged, no new environment variable. The only dependency-like
  removal is the Bootstrap 5.1.3 CDN stylesheet in `templates/base.html`.
- **No production Python is added** `[31]`: the WP-7 extension already landed
  `partition_albums_by_threshold` and the three-value `fetch_top_albums_async`.
  `scrobblescope/` is untouched `[34]`.

## 9. What the plan recorded as gating execution

Open decisions `[9]` and `[69]` were not incidental; several of them blocked
work:

| Decision | Where | Consequence if unresolved |
| --- | --- | --- |
| The spec-versus-ruling conflict | `[7]`, `[17]`, `[69]` assumption 6 | Phase 2 cannot start correctly; an agent following `PLAYBOOK.md` Section 3 rebuilds the rejected layout |
| `gemini_implementation_plan_unverified.md` fate | `[7]`, `[9]`, `[25]`, `[69]` | It is untracked and superseded; leaving it is "another undeclared root file" |
| Expander step 20 vs 25 | `[9]`, `[69]` | Settled in code at 25; unresolved only as an owner decision |
| Serif figure face on Results | `[9]`, `[69]` | `DESIGN.md`'s Role Segregation Rule must be restated or the two documents contradict each other |
| Third "System" theme state | `[9]`, `[69]` | F-B21-22 stays open; the current two-state logic is correct as written |
| F-B21-20 staging-order contract | `[9]`, `[69]` | "Every phase depends on which answer the owner picks" |
| `implementation_plan.md` kept or removed | `[25]`, `[69]` | Partly answered: it was kept and moved |

Two further hard constraints on sequencing were recorded:

- **WP-8 keeps its number and position** `[69]` assumption 4: `DOC007` in
  `scripts/docsync/integrity.py` reads the WP headings, and renumbering WP-7 or
  WP-8 "breaks citations in `PLAYBOOK.md`, `FINDINGS.md` and `AGENT_NOTES.md`."
- **The heatmap fill behaviour has no automated coverage today** `[69]`
  limitation: Phase 4 creates the first check, and "until that check
  exists, the retirement is unsafe to ship."

## 10. Where the plan recorded the work resuming

Progress `[6]` is the only place that carries the three uncommitted work items
and their commit order, and `[7]` is the only place carrying the four-step
pickup list. Neither is in `PLAYBOOK.md` Section 3, whose next-action bullet
speaks only to the WP-7 refinement and the open spec conflict. The practical
consequence: an agent that bootstrapped from `AGENTS.md` alone reached the right
blocking conflict but never learned that two commits were owed before Phase 2.

The pickup list, in the order the plan gave it:

1. Commit the staged set -- "Its PLAYBOOK entry and every gate result are
   recorded." The staged set is named file by file in `[6]`, with 480
   insertions and 140 deletions, and every gate is recorded as observed green on
   exactly that state `[3]`.
2. Commit the diagram rebuild, "re-staging `PLAYBOOK.md`" because its diagram
   entry sits unstaged and the file therefore reads `MM` `[6]`.
3. Commit the plan's move, deciding `gemini_implementation_plan_unverified.md`'s
   fate "at the same time".
4. Start Phase 2 at the spec-versus-ruling conflict.
