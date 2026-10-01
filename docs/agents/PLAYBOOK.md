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
| 21 | UI overhaul -- Tailwind + daisyUI migration | `docs/history/definitions/BATCH21_DEFINITION.md` | `docs/history/logs/BATCH21_LOG.md` |
| 22 | Enrichment providers and original release years | `docs/history/definitions/BATCH22_DEFINITION.md` | `docs/history/logs/BATCH22_LOG.md` |
| 23 | Spotify Extended Streaming History import | `BATCH23_DEFINITION.md` | active -- Section 4 |

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

- **Batch 23 is active.** Definition: `BATCH23_DEFINITION.md`.
  Branch: `feat/batch23-wp0-hygiene`. The branch was cut from `test`; run the
  worktree guard with `--base-ref origin/test`.
- **Next action:** WP-0 is next.
  Part A and Part B are complete. Part C continues through the three
  follow-on plans in the order recorded under "After this plan" in
  `docs/superpowers/plans/2026-09-23-batch23-wp0-reconcile-and-clear.md`:
  control-plane, frontend, then test infrastructure and dependencies.
  The control-plane plan is written and reviewed:
  `docs/superpowers/plans/2026-09-25-batch23-wp0-control-plane.md`. Its eight
  tasks are all complete (Task 7 landed `8cf5fd4`..`c39da3c`). The frontend
  and test-infrastructure/dependencies plans are now written and reviewed:
  `docs/superpowers/plans/2026-09-26-batch23-wp0-frontend.md` and
  `docs/superpowers/plans/2026-09-26-batch23-wp0-test-infra-deps.md`. The
  frontend plan and the test-infrastructure/dependencies plan are both fully
  executed (every task in each has landed). The three plans' carried items
  are closed out, and their final code review of the whole branch ran on
  2026-09-27; its one fix wave has landed and passed a scoped re-review
  (see Section 4). The WP-0 close-out below is what remains of WP-0. The
  definition owns WP-0 scope and acceptance; `docs/agents/FINDINGS.md`
  owns open finding status.
- **WP-0 close-out:** Re-review `e7e076b` independently, review the whole
  branch, verify Part C's listed findings member by member, and run the
  final gates in the definition. Then write one tagged `(Batch 23 WP-0)`
  Section 4 entry, carrying an explicit `**Status:** WP-0 complete` line
  (DOC007 requires it before the package reads done). Earlier WP-0 commits
  remain untagged by the owner's 2026-09-23 ruling in the definition.
- **Batch 23 close-out obligation:** WP-7 includes the deferred Batch 21
  frontend and accessibility audit; the batch cannot close without it.
- **What PR #245 ships (owner ruling 2026-09-29):** the WP-0 foundation and
  every fix from the three reviews, including the job module with its storage
  seam, typed provider failures and provider failure logs that carry no
  listener data. Moved to the follow-up PR: job persistence, the Last.fm
  scrobble seams, the album request module, one album-metadata encoding, the
  statistics module and the tooling package.
- **Architecture seams before the Spotify import (owner ruling 2026-09-29):**
  "If any seams from architechture deepening are worth doing now before
  further feeat implements, thats the time." The seams and the work package
  each one gates are in
  `docs/history/reports/architecture-review-20260930-0040.html`: a job
  module with a storage seam and typed provider failures, job persistence
  (gates WP-3), an album request module (gates WP-4), normalized Last.fm
  scrobbles with one typed album aggregate (gates WP-2), one album-metadata
  encoding (gates WP-3), a statistics module (gates WP-6), and provider
  failure logs that carry no listener data. Which of these #245 ships is
  in the "What PR #245 ships" bullet above; the rest wait for the follow-up
  PR.

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
  - `<!-- DOCSYNC:CURRENT-BATCH-END -->

<!-- DOCSYNC:CURRENT-BATCH-START -->

<!-- DOCSYNC:CURRENT-BATCH-END -->

### 2026-10-01 - The ring check waits out animations before reading pixels

Side task, no batch tag: the heatmap focus-ring check waits for running animations to finish before it reads the cell's geometry and takes its screenshot, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: the previous step's reproduction showed 8 of 20 last-cell screenshots landing while `#heatmap-result` was still crossfading in (opacity changed between the read before and the read after the shot), and a reading taken mid-animation is invalid by construction. PR #252 applied the same reasoning to every other check that slept through a transition; the ring check still waited only for fonts and two frames.

Change: `_ring_shot` in `scripts/dev/_frontend_gate_heatmap_access.py` calls `wait_for_settled` (`scripts/dev/_frontend_gate_shared.py`, bounded, raises when the page never settles) at the start of each attempt, after the tooltip nudge and before `_LAYOUT_SETTLED_JS` and the geometry read. This removes a confounder; it is not claimed as the fix for F-B23-39, whose status stays open.

Evidence: a new test records the order of the wait and the geometry reads over a two-attempt run; with the call removed it fails (`assert 0 == 2` on the wait count). The existing ring-page helper answers the settle script with an empty result so the real `wait_for_settled` can run against it. The 20-run reproduction (the check alone, fresh desktop context each, `reduced_motion="no-preference"`) passed 20 of 20, with `container.opacity` 1 and nothing changed during the shot on all 80 shots read (4 per run). A ring forced to `visibility=hidden` still fails with `ring.visibility=hidden` in the evidence.

Validation: `pytest -q` -- **2528 passed**.

### 2026-10-01 - The ring check also reads opacity and animations

Side task, no batch tag: the heatmap focus-ring check also reads the result's opacity and running animations when it fails, a test of the crossfade hypothesis for F-B23-39, a fix from the third review of PR #245, on the review-fix branch that fast-forwards into PR #245's branch. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: CI run 36808671140 (Linux, desktop, 043368eb) failed the ring check with the ring visible, 1.6px outside the cell, stroke the accent, `:focus-visible` held, tooltip clear of the ring and nothing moved: the DOM said painted, the pixels said not. The one state the evidence line did not read is opacity. `static/js/heatmap.js` `revealHeatmapResult` crossfades `#heatmap-result` in (`heatmap-fade`, `fading-out`, `is-handing-off`, 180 ms handoff) unless `prefers-reduced-motion: reduce` matches, and `_LAYOUT_SETTLED_JS` waits for fonts and frames, not animations.

Change: `_RING_EVIDENCE_JS` in `scripts/dev/_frontend_gate_heatmap_access.py` also reads the result container's and the SVG's computed `opacity`, the container's three crossfade flags, how many `document.getAnimations()` are `running`, and the page's `prefers-reduced-motion` match, in the same evaluation as the geometry (so on both sides of the shot, the suffix from the read after it). The suffix gains `container.opacity`, `svg.opacity`, `container.heatmap_fade`, `container.fading_out`, `container.is_handing_off`, `animations.running` and `prefers_reduced_motion`, and `changed_during_shot=` names them when they differ between the two reads. Three tests (38 in the file).

Reproduction, no fix: the check alone, 20 times in one desktop Chromium, with `reduced_motion="no-preference"`: 20 of 20 passed, twice; 20 of 20 with no emulation. The page reports `prefers-reduced-motion: reduce` matches False in the ordinary local run, so the premise that a local run skips the fade is false on this machine. With the evidence read on every shot of one `no-preference` run, 8 of its 20 last-cell shots had a different container opacity before and after the screenshot (so a shot can land inside the fade, on the very cell that failed on CI), and the ring still painted each time; the no-emulation run showed none. No iteration failed, so by the rule for this task the crossfade hypothesis is not confirmed and `_ring_coverage` does not wait for animations. F-B23-39 records the lead. The next CI failure's line will show it.

Validation: `pytest -q` -- **2527 passed**.

### 2026-10-01 - The heatmap ring check says why a ring is unpainted

Side task, no batch tag: the heatmap focus-ring check names its cause when it fails, an evidence-first step for F-B23-39. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Problem: `heatmap cells keyboard access` fails now and then with "paints no rgb(106, 75, 175) pixel ... (samples painted: top 0%, right 0%, bottom 0%, left 0%)" and passes on a re-run (ccc2c921 [mobile], dce6f148 [mobile], CI run 36726578353, and CI run 36803075335 on PR #253 [desktop], which had no failed app resources). The line said only that nothing was painted, so a ring that was never shown, a ring in the wrong place, another stroke and a tooltip over the ring all looked the same.

Change: a ring failure in `scripts/dev/_frontend_gate_heatmap_access.py` now ends with one `[evidence: key=value ...]` suffix (`_RING_EVIDENCE_JS`), read in the page in the same evaluation as the geometry, before and after the screenshot; the suffix is built from the read after it, and `changed_during_shot=` names the evidence fields that differed between the two reads (reported, never judged): the ring's `visibility` and box, the cell's box, `document.activeElement` and whether it matches `:focus-visible`, `document.hasFocus()`, the ring's computed stroke, `data-theme`, the tooltip's box, whether it is shown and whether it covers the ring, the scroll offset, `devicePixelRatio`, how many cells paint after the ring, and how long the settle wait took (`settle_slow` past one second). `_ring_shot` returns the coverage and the evidence; `_ring_coverage` keeps its old return. Probe: with `showFocusRing` forced to `hidden` in a scratch copy of `static/js/heatmap.js`, the check failed on all three cells with `ring.visibility=hidden`; restored, it passed. Eleven tests in `tests/scripts/dev/test_frontend_gate_heatmap_access.py` cover the line, the slow-settle flag and the two-sided read; those that read the suffix fail without it.

Root cause not found, so no fix to the check: every check in a group and profile shares one context (`frontend_gate.py` `open_page` makes one per group and profile), but nothing earlier in the `layout & pipeline` group writes `darkMode`, emulates a colour scheme or forced colours on that page (the pipeline check's init script runs on a probe page; the spotlight rotation check's stays on the desktop page but only shortens a 7000 ms interval and passes other fetches through, and the mobile failures have no such script), and 20 runs of the check in one desktop Chromium under a concurrent `pytest -q` all passed. F-B23-39 records what was ruled out; the next failure's evidence line names the cause.

Validation: `pytest -q` -- **2524 passed**.

### 2026-09-30 - Coverless albums get a deterministic two-tone wash

Side task, no batch tag: a missing album cover is drawn as a muted two-tone wash instead of a flat bordered box. Untagged by owner ruling 2026-09-23 until the whole of WP-0 lands.

Why: owner, 2026-09-30, on the Unmatched page's empty cover boxes: "it should have some sort of gradient pattern". The design system already says covers are "muted two-tone washes" (`docs/design/README.md`, `AlbumRow.prompt.md`); the code never drew them. Owner ruling, same day: Last.fm images are not trusted, so there is no image fallback of any kind.

What: eight pairs of `--ss-wash-N-a`/`-b` tokens in both themes of `static/css/tailwind.src.css` (compiled `tailwind.css` rebuilt), painted by `.cover-wash-N` in `static/css/results.css` (one shared rule set, forced colours drop the gradient and keep the border). `cover_wash_index` in `scrobblescope/domain.py` picks the pair from `zlib.crc32` of the normalised artist and album, so it is the same in every process (`hash()` is salted); the `cover_wash` template filter in `scrobblescope/routes/__init__.py` writes the classes. All four Unmatched placeholders and the Results image fallback use it; a portrait slot drops its wash once the photograph loads. No network call is added. A cover still loading wears its wash too: the cover `<img>` carries the same classes, so the wash shows until the picture paints and behind transparent pixels. The initials stay, in `--color-base-content`: 10.12:1 to 13.41:1 on every light stop and 10.72:1 to 14.04:1 on every dark stop (owner, 2026-09-30: "The 4.5 is a floor not a goal", so 7:1 is the line). RECONCILIATION section 19 records the palette and supersedes the snapshot README's sentence about Last.fm art replacing the washes (the snapshot is guarded and cannot be edited).

A test ties `COVER_WASH_COUNT` to the `.cover-wash-N` rules in `results.css` and to both stops in both theme blocks of `tailwind.src.css`.

Gate: `_cover_wash_page_failures` in `scripts/dev/_frontend_gate_unmatched.py` reads the coverless placeholders in both themes (two different gradient colours) and under forced colours (a painted border), and reads the tokens of all `COVER_WASH_COUNT` pairs in each theme, not the nodes on the page (the initials at 7:1 or better on both stops of every pair, whether or not the pair is on the fixture page, the failure naming the wash, the stop and the ratio; a colour it cannot parse fails loudly). Its fixture's Deezer row now has no cover so a coverless other-provider row is on the page. Live probe: a planted flat background, a planted `border: 0` and a planted pale light-theme stop on wash 0, a pair that is not on the fixture page, each failed the gate; restored, it passed.

Validation: `pytest -q` -- **2513 passed**.
