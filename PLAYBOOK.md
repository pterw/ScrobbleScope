# ScrobbleScope Execution Playbook

Date: 2026-02-22
Purpose: Single source of truth for work sequencing and execution history.
Rules for agent behaviour live in `AGENTS.md`; current-state snapshot in
`.claude/SESSION_CONTEXT.md`.

## 1. Why this document exists

- Provide a single source of truth for work sequencing.
- Enable continuation by another agent with minimal context loss.
- Prevent risky refactor-first changes before parity tests exist.

**Implementation principles:**
1. Approval tests before structural refactor.
2. No behavior-breaking refactors without parity checks.
3. Add observability before optimization where possible.
4. Keep changes batch-scoped and reversible.
5. Keep security-safe rendering (`tojson`, escaping) as baseline.

---

## 2. Batch order (strict sequence)

Completed batch definitions are archived individually under `docs/history/`.

### Batch index (completed batches archived; the active batch, if any, is listed last)

| Batch | Title | Definition | Log |
|-------|-------|------------|-----|
| 0 | Baseline freeze + approval parity suite | `docs/history/definitions/BATCH0_DEFINITION.md` | -- |
| 1 | Proper upstream failure state + retry UX | `docs/history/definitions/BATCH1_DEFINITION.md` | -- |
| 2 | Personalized minimum listening year | `docs/history/definitions/BATCH2_DEFINITION.md` | -- |
| 3 | Remove nested thread pattern | `docs/history/definitions/BATCH3_DEFINITION.md` | `docs/history/logs/BATCH3_LOG.md` |
| 4 | Expand test coverage significantly | `docs/history/definitions/BATCH4_DEFINITION.md` | `docs/history/logs/BATCH4_LOG.md` |
| 5 | Docstring + comment normalization | `docs/history/definitions/BATCH5_DEFINITION.md` | `docs/history/logs/BATCH5_LOG.md` |
| 6 | Frontend refinement/tweaks | `docs/history/definitions/BATCH6_DEFINITION.md` | `docs/history/logs/BATCH6_LOG.md` |
| 7 | Persistent metadata layer (Postgres) | `docs/history/definitions/BATCH7_DEFINITION.md` | `docs/history/logs/BATCH7_LOG.md` |
| 8 | Modular refactor (app factory + blueprints) | `docs/history/definitions/BATCH8_DEFINITION.md` | `docs/history/logs/BATCH8_LOG.md` |
| 9 | Audit remediation (WP-1 through WP-8) | `docs/history/definitions/BATCH9_DEFINITION.md` | `docs/history/logs/BATCH9_LOG.md` |
| 10 | Gemini audit remediation (WP-1 through WP-9) | `docs/history/definitions/BATCH10_DEFINITION_2026-02-21.md` | `docs/history/logs/BATCH10_LOG.md` |
| 11 | Gemini Priority 2 audit remediation (SoC, DRY, architecture) | `docs/history/definitions/BATCH11_DEFINITION.md` | `docs/history/logs/BATCH11_LOG.md` |
| 12 | Polish and observability (CSS, formatting, SoC, progress) | `docs/history/definitions/BATCH12_DEFINITION.md` | `docs/history/logs/BATCH12_LOG.md` |
| 13 | Internal decomposition and coverage hardening | `docs/history/definitions/BATCH13_DEFINITION.md` | `docs/history/logs/BATCH13_LOG.md` |
| 14 | Doc hygiene (archive restructure, docsync package, per-batch routing) | `docs/history/definitions/BATCH14_DEFINITION.md` | `docs/history/logs/BATCH14_LOG.md` |
| 15 | Alignment, hardening, and handoff | `docs/history/definitions/BATCH15_DEFINITION.md` | `docs/history/logs/BATCH15_LOG.md` |
| 16 | Script hygiene, local dev hardening, and integration testing | `docs/history/definitions/BATCH16_DEFINITION.md` | `docs/history/logs/BATCH16_LOG.md` |
| 17 | Agent bootstrap hardening, CI/CD improvements, and dep pinning | `docs/history/definitions/BATCH17_DEFINITION.md` | `docs/history/logs/BATCH17_LOG.md` |
| 18 | Scrobble heatmap -- iteration 1 | `docs/history/definitions/BATCH18_DEFINITION.md` | `docs/history/logs/BATCH18_LOG.md` |
| 19 | Heatmap polish -- frame, KPIs, mobile layout | `docs/history/definitions/BATCH19_DEFINITION.md` | `docs/history/logs/BATCH19_LOG.md` |
| 20 | File-hygiene + docs methodology refresh | `docs/history/definitions/BATCH20_DEFINITION.md` | `docs/history/logs/BATCH20_LOG.md` |
| 21 | UI overhaul -- Tailwind + daisyUI migration | `BATCH21_DEFINITION.md` | active -- Section 4 |

A batch's close-out entry sits in its per-batch log only when the heading
carried a `(Batch N WP-X)` tag (as Batch 18's did). Close-outs tagged
`(Batch N close-out)` are not parser-recognized and were routed to the
monolith archive instead -- Batches 19 and 20 are the current examples.
See FINDINGS F-DOCSYNC-3.

### Open decisions (owner confirmation needed)

1. Persistent store choice: Postgres only or Postgres + Redis.
2. Retry UX policy: immediate retry button only, or retry + cooldown messaging.
3. Error copy style and user-facing tone for upstream failures.

---

## 3. Active batch + next action

- **Batch 18 is complete.** All 5 WPs done. Definition archived:
  `docs/history/definitions/BATCH18_DEFINITION.md`.
- **Batch 19 is complete.** All 5 WPs done plus owner-review follow-up.
  Definition archived: `docs/history/definitions/BATCH19_DEFINITION.md`.
  PR #152 (Batches 18 + 19) merged to `main`.
- **Batch 20 is complete.** All 9 WPs done (WP-0 through WP-5 via PR #159
  on `file-hygeine`; audit gap-fix follow-up, WP-6, WP-7, and WP-8 on
  `wip/batch-20`, submitted as PR #162). Definition archived:
  `docs/history/definitions/BATCH20_DEFINITION.md`.
- **Batch 21 is active.** Definition: `BATCH21_DEFINITION.md` (repo
  root). Scope: UI overhaul -- Bootstrap 5.1.3 -> Tailwind v4 (standalone
  CLI) + daisyUI v5, warm heatmap-derived themes propagated app-wide,
  page-by-page strangler migration. Expanded from the owner's Claude
  Design audit (UI Audit v3); four owner decisions locked in the
  definition. Branch: `wip/batch-21` (worktree off `main`).
- **Next action:** land PR #170, then execute the full F-SWE-1 principles
  audit, then proceed to Batch 21 WP-1. PR #169 merged to `main` on
  2026-08-08 and the Quality Gate is green for `5bc6294`, so the canonical
  repository-integrity gate and read-only worktree guard are shipped and
  F-DOCSYNC-5/F-WORKTREE-1/F-WORKTREE-2 are resolved. Three guard files
  exceed their directory peer caps after review remediation -- accepted as a
  deviation and tracked as F-WORKTREE-4 in FINDINGS.md, not silently. Review
  remediation ran to round 6: rounds 2 through 5 landed before the merge, and
  round 6 was reviewed after the final push, so its four findings reached
  `main` unaddressed. They are remediated in **PR #170** (open, on
  `wip/batch-21`), which must land before the F-SWE-1 audit begins -- the
  audit reads the guard and docsync sources that PR still changes.
- Batch 21 WP status: WP-0 done. WP-1 through WP-8 not yet started.
- **Perf note:** heatmap fetch speed is rate-limit bound; measurement and
  rationale live in FINDINGS.md F-B18-11 (single source).
- **Last.timer note (checked 2026-05-19):** the referenced project uses
  aggregate `user.gettopartists`/`user.gettoptracks` calls with page fan-out,
  not exact per-scrobble recent-track timestamps. Useful for future perf
  research, but not a drop-in heatmap speedup. See FINDINGS.md F-B19-3.
- Future feature candidates (confirmed by owner roadmap):
  - **Top songs** (future): rank most-played tracks for a year (Last.fm + possibly
    Spotify enrichment, separate background task + loading/results flow).

---

## 4. Execution log (for agent handoff)

Keep only the active window here: current batch entries plus the latest 4
non-current operational logs. Older dated entries live in
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.

**How to read dated entries:**
- Each heading `YYYY-MM-DD - ...` is a completion/addendum log.
- Untagged side-task history: `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`.
- Tagged batch history: per-batch logs under `docs/history/logs/`.
- Batch scope/acceptance criteria: definitions under `docs/history/definitions/`.
- Current-batch boundaries are machine-managed (do not move entries manually):
  - `<!-- DOCSYNC:CURRENT-BATCH-START -->`
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->`
- After any edit here, run `python scripts/doc_state_sync.py --fix`.
- Archive search: `rg -n "^### 20" docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`

<!-- DOCSYNC:CURRENT-BATCH-START -->

### 2026-07-24 - Batch 21 opened: UI overhaul definition committed (Batch 21 WP-0)

- Scope: opened Batch 21 (UI overhaul -- Tailwind + daisyUI migration)
  on `wip/batch-21`, a worktree off `main` at the PR #162 merge.
- Plan vs implementation:
  - `BATCH21_DEFINITION.md` expanded from the stub into the full 9-WP
    definition derived from the owner's Claude Design audit (UI Audit
    v3): toolchain (WP-1), base shell + error-page pilot (WP-2), index
    (WP-3), unified loading (WP-4), results leaderboard (WP-5), heatmap
    seam removal (WP-6), unmatched + reason_code backend fix (WP-7),
    sweep + close-out (WP-8). Strangler migration, page by page.
  - Four owner decisions locked in the definition: rotating loading
    messages cut; welcome modal deleted; `limit_results` kept inside the
    thresholds disclosure; fonts self-hosted under `static/fonts/`.
  - Agent verification recorded in the definition: the unmatched
    reason-string grouping bug is live; `--bs-primary` never overridden;
    `bootstrap.Popover` in `index.js` is a third Bootstrap JS consumer
    the audit missed; `--bars-color` must be aliased in both themes.
  - PLAYBOOK Section 2 row title updated; Section 3 marks Batch 21
    active with next action WP-1; SESSION_CONTEXT rows updated.
  - Toolchain mechanics locked after an owner-relayed Opus 5 review:
    CLI binary in gitignored `scripts/bin/` with `.gitkeep`; auto-fetch
    at a pinned version via a new `scripts/dev/tailwind_build.py` (not
    `dev_start.py` -- app startup never needs the toolchain); WP-8 adds
    a rebuild-and-diff pre-commit hook for compiled-CSS drift; WP-8
    owner E2E explicitly opens the downloaded save-as-image file.
- Deviations: none.
- Validation: `pytest -q` -- **390 passed**. `pre-commit run --all-files`
  -- all hooks pass. `doc_state_sync.py --check` -- exit 0 (expected
  root warning for the now-active `BATCH21_DEFINITION.md`).
- Forward guidance: WP-1 sets up the Tailwind v4 standalone CLI +
  daisyUI v5 bundled plugin, defines both themes from the audit token
  sheet, and commits the compiled CSS. No template changes until WP-2.

<!-- DOCSYNC:CURRENT-BATCH-END -->

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
