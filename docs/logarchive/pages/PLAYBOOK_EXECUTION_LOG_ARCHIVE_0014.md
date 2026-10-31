<!-- DOCSYNC:ARCHIVE-PAGE v1 -->
# PLAYBOOK_EXECUTION_LOG_ARCHIVE -- page 0014

### 2026-09-09 - Complete Results scaling and warm the shared canvas

- Owner direction: keep the deployed Results aesthetic, warm the page/navbar
  subtly, keep the header fixed on every screen size, and defer
  Task 6 until Bootstrap is fully removed. The canonical remediation plan
  records the timing; WP-7's backend-first contract and final page migration
  remain unchanged.
- Owner typography refinement: Track Plays table numerals are 25% larger;
  Listening Time retains its existing size, including after switching modes.
- Owner follow-up: Results stat rail, table, empty-state panel and sidebar
  cards use `--ss-surface-sunken`; table hover uses the card token for a
  visible state change. Buttons retain their control surfaces.
- Implementation: shared light canvas is `#faf7f0`; DOC009 guards the Tailwind,
  legacy-page and navbar copies. Results uses measured numeric scaling across
  named spacing tokens, typography, artwork and controls. F-B21-55 records the
  fixed Firefox arithmetic failure and incomplete geometry scaling. Mobile
  table headings wrap within their columns. The mobile gate verifies both fixed positioning and matching body padding.
- Evidence: `scratch/fixed-results-measurements.json` and paired Chromium /
  Firefox screenshots. Both engines agree on 20% growth between 1200px and
  1920px. Fourteen viewport samples (320-2560px) have no horizontal overflow;
  the shared header remains at top 0 after scrolling at every width. Index, Results and
  Unmatched bodies and navbars all compute to the warm canvas. Dark token values are unchanged; Results panels now consume the sunken token. The Results gate checks growth ratios and
  mobile recovery using rendered values.
- Publication validation: fresh `pytest -q` -- **975 passed**. Full frontend
  gate: 25 checks passed in 45 runs across Chromium and the Firefox canary.
  The prior loading-pipeline navigation race did not reproduce. The separate
  Results probe covered both engines at seven widths; the final surface and
  metric-toggle checks covered both themes and desktop/mobile respectively.
  All pre-commit hooks pass, including generated-CSS drift; docsync and
  whitespace checks pass. Read-only review found no material code issue and
  corrected active document contradictions; exhaustive historical-document
  coverage was interrupted by reviewer usage limits. Owner authorized commit
  and push; local tool artifacts remain outside the published changes.

### 2026-09-09 - Triage PR 227 assertions and deleted TODOs; fix job-page statuses

- Scope: owner requested top-priority fixes only and logging of other review
  comments. Read live review threads, complete review bodies including the
  low-confidence block, current source, and the TODO add/remove commits.
- Plan vs implementation: fixed F-B21-49 with explicit HTTP/badge pairs at
  its four source branches. Missing IDs return 400; unavailable jobs 404;
  pending results 202; processing failures use their classified status.
  Saved empty-state recovery stays 200. Strengthened five existing tests and
  added thirteen route cases. The tests failed before the source fix.
- Disposition: F-B21-54 records test-scanner noise. F-B21-50 now distinguishes
  implemented notes from deferred unmatched redesign / POST retirement.
  F-B21-51 no longer incorrectly claims there are no gate infrastructure tests.
  Detailed evidence and remaining finding owners:
  `docs/history/reports/PR227_PRIORITY_TRIAGE_2026-09-09.md`.
- Validation: `pytest -q` -- **975 passed**. Route suite: 18 failed / 89 passed
  before, 107 passed after. Focused read-only review found no regression.
  Docsync and `git diff --check` pass. Hooks pass after formatting except the
  existing `tailwind-css-drift` failure described below.
- Deviations: the pre-work hooks rebuilt already-dirty `tailwind.css` for the
  owner's existing results markup; its index comparison fails until that
  separate styling work is staged. No source CSS/template changes were made
  here. The known Windows log-rotation lock appeared in red-test diagnostics.
- Forward guidance: keep this status fix separate from existing styling.
  Published PR `a53e412` lacks the earlier local remediation; no commit,
  push or review reply was made. Task 6 and WP-7 remain next.

### 2026-09-09 - Audit PR 227 for regression and bloat; ignore gate artifacts (side-task)

- Scope: the owner asked which commits after `b987e48` carry value and which
  are bloat, and whether the 15 route TODOs were implemented. Owner chose the
  hygiene-only remedy: no history rewrite and no gate split.
- Premise correction recorded before any change: `b987e48` is not a baseline
  to restore toward. `main` merged into this branch at `ebc5145`, *after*
  `b987e48`, so reverting toward it would discard PRs #225 and #226. PR content
  was therefore measured against `origin/main`.
- Size of the PR, since three different questions give three different answers
  and the first is the one that misleads. `b987e48..HEAD` is +4524/-1848 over
  62 files, but it hides everything that arrived through the `ebc5145` merge
  and must not be quoted. `origin/main..HEAD` is +8458/-2293 over 76 files.
  Summing each of the 34 non-merge commits' own diffs gives the real churn:
  **+13802/-5450 over 86 distinct files**, so netting the endpoints conceals
  8,501 touched lines. The largest single contributor is `frontend_gate.py`:
  20 commits and 3,158 gross lines to land a net +791 while chasing the CI
  stall. Quote the churn figure when judging review effort and the endpoint
  diff when judging the delivered change.
- Three bloat suspicions were tested and **disproved**, so nothing was
  reverted: (1) the 486/484-line `global.css` diff is a whole-file CRLF-to-LF
  conversion in `d41db1f` with about five semantic lines, and `global.css` was
  the only CRLF outlier in `static/**` and `templates/**`, so the conversion
  normalized it; (2) `typekit_fixture.css` was added then deleted under the
  owner's 2026-09-07 font-licensing ruling, recorded in
  `scripts/dev/fixtures/README.md`; (3) the ruff migration touched about
  fifteen test files but only reflowed `assert` formatting, weakening no
  assertion. `ipinfo` and `cachetools` removal was confirmed against zero
  imports repo-wide.
- Security and hardening in the range were confirmed genuine and kept:
  `innerHTML` sinks in `static/js` fall 5 (main) to 4 (`b987e48`) to 1 (HEAD,
  `heatmap.js` only); least-privilege `contents: read`;
  `persist-credentials: false`; 18 vulnerable pins upgraded to a zero-finding
  `pip-audit`; aiohttp 3.14 deprecations replaced with stdlib `base64`; CI
  actions moved off the deprecated Node 20 runtime.
- TODO verification: 13 of 15 described already-implemented behaviour
  (`/unmatched` GET route, `unmatched_empty.html`, `index.js` blur validation,
  `heatmap.js` `retryable` branching), so removing them was correct. Two were
  genuine and are now **F-B21-49**.
- Implementation: added root-anchored `.gitignore` entries for
  `/gate_out*.txt` and `/gate_summary.txt` (about 3 MB of untracked console
  captures) plus `*.new` and `*_backup.toml` migration scaffolding, verified
  against `git ls-files` so no tracked file became hidden; deleted the
  untracked zero-byte `.github/workflows/workflow1`, which would have been an
  invalid workflow had it ever been committed.
- Deviations: three findings were filed rather than fixed, because each needs
  an owner ruling or parity tests this side-task does not carry. **F-B21-49**
  (four `error.html` callers return HTTP 200 while painting a 400 badge;
  measured, not read) needs the owner to choose 404 or 410 for expired jobs.
  **F-B21-50** records the net-zero TODO churn that cost eight Qlty rounds
  (15 distinct `routes.py` line numbers, each republished 8 times: 120 comment
  bodies). **F-B21-51** sizes `frontend_gate.py` at 3,756 lines against its
  largest sibling's 404, and defers the split because gate infrastructure has
  no parity tests (AGENTS.md Proposal and Design Rules item 4). F-B21-10's
  status line now points at F-B21-49 for its call-site half.
- One claim in the review commit's own subject was checked and does not hold as
  written: "simplify frontend checks". The gate plus helper grew from 2,965
  lines in 49 functions on `main` to 3,879 in 78 at HEAD, about 222 of those
  lines added by that very commit, with its test file going 966 to 1,328. What
  did improve is unit size -- the longest function fell 485 to 271. Recorded in
  F-B21-51 so a later reader does not inherit "simplified" as fact.
- Validation: `pytest -q` -- **962 passed**. All pre-commit hooks and
  `doc_state_sync.py --check` pass. The committed tree was verified clean by
  stashing the unrelated results-scaling work in progress; the earlier
  `tailwind-css-drift` failure belonged to that work, not to any PR commit.
- Forward guidance: the PR #227 body still needs writing before merge. Task 6
  (accessibility pass) and WP-7 remain the next batch work.

### 2026-09-07 - Remediate PR 227 and simplify frontend checks

- Owner requested one review-remediation package. The full comment inventory,
  body exclusions, repeated claims and individual dispositions are in
  `docs/history/reports/PR227_REVIEW_2026-09-07.md`.
- Extracted gate measurement/comparison/profile responsibilities, shared phase
  probes and lazy generic CDN fixture loading; preserved the live-fonts option.
  Existing thresholds and the Chromium matrix / Firefox static canary remain.
- Separated spotlight aggregation from routes, shared Spotify payload parsing,
  separated heatmap validation/dispatch, and extracted the Last.fm job stage.
  Existing job-state, empty/error, fallback and sampling behavior stays covered.
- Split results spotlight hydration/rotation from exports; use DOM text nodes
  for metrics/toasts and supported metric-toggle font weights. CSV follows the
  current rank/metric with full ISO dates while display stays month precision.
  JPEG background comes from the active theme; browser checks decode actual
  downloads in both themes at mobile and desktop widths.
- Reconciled implemented route TODOs, corrected explicit 404/500 badges (the
  remainder of F-B21-10 stays open), and disabled checkout credential persistence.
- Review caught invalid JSON in the extracted stale-response fixture. A failing
  regression test proved it; structured JSON serialization restored the check.
- Validation: `pytest -q` -- **962 passed**, zero warnings. The frontend gate
  passed 25 checks in 45 runs across Chromium and the Firefox static canary.
  Both theme exports decode to nonblank 3600px-wide JPEGs. All pre-commit
  hooks and `doc_state_sync.py --check` pass. No push or deployment. Header
  alignment and optional white-card shadow remain a separate design follow-up.

### 2026-09-07 - Qlty adopted; first triage closes the workflow-permission gap (side-task)

- Scope: the owner added qlty (`.qlty/qlty.toml`, uncommitted by owner
  choice) as a fourth static-analysis layer alongside ruff, bandit-class
  SAST, and the existing gates. This entry records the config tuning,
  the first triage, and the two fixes it produced.
- Plan vs implementation: no plan -- owner-directed tooling adoption and
  triage. Config tuning: scratch/, scripts/bin/, generated tailwind.css,
  and graphify-out/ excluded (metrics went from 68 to 18 files); the
  flake8 plugin removed (ruff replaced it; two plugins would report one
  rule surface in two vocabularies); tests/ added to test_patterns.
- Triage of the first `qlty check` (88 findings): ~60 are bandit B101
  "use of assert" in tests -- noise, asserts are the point of tests;
  2 are real (zizmor on the workflow, fixed here); 1 is a false positive
  recorded with a nosec (bandit B311, fixed here); the cognitive-
  complexity pair (frontend_gate.py check_large_display_scale_parity,
  spotify.py fetch_spotify_artist_spotlight) is known owned debt that
  matches F-B20-2/F-SWE-7/issue #222 and stays batch-scoped, not
  gate-blocking.
- Implementation:
  - `.github/workflows/test.yml`: added a job-level `permissions:
    contents: read` block. The job only reads the checkout and uploads a
    coverage artifact; without the block the runner's default token
    permissions are broader than any step needs and every third-party
    action inherits them (zizmor excessive-permissions and artipacked).
  - `scrobblescope/routes.py`: `# nosec B311` with justification on the
    `random.Random(str(job_id)).sample(...)` spotlight selection. The
    seed makes the sample deterministic per job (asserted by
    test_results_page_samples_five_unique_artists_from_aggregate_top_ten);
    cryptographic unpredictability would defeat the intent.
- Deviations: none.
- Validation: `qlty check` -- 88 -> 86 findings. The excessive-permissions
  finding is gone; the B311 finding is suppressed (the nosec must sit on
  the same line as the call -- a preceding comment line is ignored by
  bandit, which the first attempt got wrong and the re-run caught).
  Remaining: one zizmor artipacked medium on the checkout step (line 34)
  -- zizmor flags any cache/artifact-adjacent job; with the permissions
  block in place the token is already contents-read only, so the
  practical exposure is closed and the residual finding is a
  scanner-pattern advisory, not an open hole. The rest are the recorded
  noise classes. `pytest -q` -- **938 passed**, zero warnings. All
  pre-commit hooks pass.
- Forward guidance: the meta-lesson is recorded here because it
  generalizes -- each gate only checks what it was built to check, and
  no gate checked the checkers' blind spots. Workflow files had no
  linter, the codebase had no SAST, structure had no complexity metric;
  qlty closes exactly those three. The complexity refactor and the
  bandit B101 test-path suppression are future-batch candidates, not
  scheduled work. WP-7 (unmatched page + reason_code) remains next.

### 2026-09-07 - Clean uninterrupted frontend gate run achieved (side-task)

- Scope: closed the deviation recorded in the two 2026-09-07 entries above
  -- no clean uninterrupted `frontend_gate.py` run had been achieved
  locally -- and updated the spec status line for the implemented design.
- Plan vs implementation: Task 6 Step 3 of
  `docs/superpowers/plans/2026-09-07-frontend-gate-isolation.md`. One run,
  qualified venv path, no interference.
- Result: the run completed all four groups across both engines with 261
  page loads, zero timeouts, zero errors, and zero font warnings (the kit
  served live). The only failures were the 7 large-display-scale-parity
  assertions at 4K (deltas ~1 percent: 770.0 vs 780.4px form width,
  774.4 vs 781.6px hero height, 77.2 vs 78.2px headline line-height, and
  related), which are the same failure family the owner already accepted
  in the gate-isolation entry above. The isolation mechanics work as
  designed: every check ran and reported; nothing cascaded.
- Deviations: none beyond the already-recorded 4K parity pair.
- Validation: `pytest -q` -- **938 passed**, 5 warnings (unchanged; no
  code changed in this entry). Spec status line updated to record the
  owner-ruled licensing amendment (Typekit fixture withdrawn).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.

### 2026-09-07 - Gate isolation, license-safe CDN routing, paper-cream tokens, and results polish (side-task)

- Scope: made the frontend gate stall-tolerant (grouped checks, fresh
  contexts, fail-fast navigation), resolved the PR #227 Quality Gate
  failures, applied the owner's paper-cream surface palette, and landed
  the owner-annotated results-page polish.
- Plan vs implementation: followed
  `docs/superpowers/plans/2026-09-07-frontend-gate-isolation.md` with one
  fundamental amendment. The metric-pinned font fixture (plan Tasks 1 and
  5) was abandoned at the owner's licensing ruling: the kit families
  (Gotham, Akzidenz-Grotesk Next Pro) are commercial web fonts and must
  never be re-hosted, embedded, or synthesized in the repo. The kit loads
  from the real Typekit origin on every gate run; only the generic cdnjs
  Bootstrap stylesheet is served from a repo fixture. The gate is
  therefore not fully hermetic -- accepted trade-off for license safety,
  recorded in `scripts/dev/fixtures/README.md`.
- Implementation:
  - Gate grouping: `CHECKS` entries gained a group field; groups derive
    from the tuple at call time (no second declared copy, no group
    integrity test per the owner's "redundant to test a test" ruling).
    Each group opens a fresh browser context, so a wedged page poisons
    only its group -- the 2026-09-07 CI run had cascaded one navigation
    timeout through every later check on a shared page.
  - Firefox is a canary: it runs only the static-assets group (the
    2026-09-01 remediation plan measured engine agreement within 0.1px,
    so a full second pass doubles the stall surface for near-zero
    signal). Chromium runs everything.
  - Fail-fast navigation: 10s page-level timeout (the context-level
    kwarg does not exist in Playwright -- caught by a local run, not by
    unit tests).
  - Fonts advisory: `check_fonts` reports missing faces as WARN lines
    and returns no failures (owner ruling: a font-supply problem is not
    a UI defect).
  - License posture: no Adobe family is copied, embedded, synthesized,
    or re-hosted anywhere; a synthetic TTF generator briefly existed in
    untracked scratch and was destroyed before any commit.
  - Paper-cream surfaces: `--ss-surface-card` #fcfbf8 -> #f7f3ea
    (halfway to the sunken tone; cards had become indiscernible from
    the page and pure white read as harsh). `global.css` mirrors follow.
    The imported design snapshot keeps `#ffffff` by contract; the
    override is recorded in `docs/design/RECONCILIATION.md` section 12.
  - Theme pill: the active Light choice dropped its #ffffff background
    (introduced in `14215d6`) for `--shell-surface` elevation with a
    stronger border/shadow.
  - Heatmap preview: bullets at color-mix(body 55%, muted); copy
    rewritten (7x52 grid, totals/streak, best-day highlight).
  - Index: `--index-scale-cap` 2.15 -> 1.75 (owner ruling: the lockup
    dominated beyond 1440p and the right-hanging void grew faster than
    content).
  - Card surfaces, final ruling (revising the paper-cream line above,
    same day): #f7f3ea was too warm and #fcfbf8 read cold, so the owner
    split the surfaces. `--ss-surface-card` -> #f9f7f1 (midpoint of the
    two; general cards), mirrored in `global.css`, and a new
    `--ss-surface-card-standout` (#ffffff light / #181520 dark) paints
    the index card alone pure white as a standout; `.ss-card` and
    `.hint__body` in `index.css` read the standout token. DESIGN.md
    header and the token test follow. RECONCILIATION.md section 12
    records the full trial -> reversal -> split sequence.
  - Results StatBlock typography (owner ruling): numerals and labels
    back to Instrument Serif with labels at 11px/xs serif in
    `--ss-text-body` (not muted); the sans-numeral line below is
    superseded by this.
  - Results polish (owner-annotated screenshot): action-row gap 8 -> 12px;
    filter-bar values to input-mono; row hover at full sunken strength;
    sort-toggle weight 500.
- Deviations: superseded by the 2026-09-07 stale-gate-cap entry below.
  The 4K parity failures recorded here were later root-caused to the
  gate's expected-scale cap lagging the CSS `--index-scale-cap` change
  in this same entry, not to font metrics. Owner confirmed the form card
  does not scroll the page at 1080p/92dpi with bookmarks extended.
- Validation: `pytest -q` -- **938 passed**, 5 warnings (final
  consolidated run for this entry; the standout token added one
  parametrized test to the shell suite). Full suite green before commit;
  pre-commit hooks (black auto-fix included) enforced on every commit in
  the series. The gate itself was exercised repeatedly during
  development; the remaining parity pair is recorded above rather than
  hidden.
- Forward guidance: WP-7 (unmatched page + reason_code) remains next;
  the heatmap form lacks validation-on-blur and private-account gating
  (owner-noted), candidate for WP-7 or a scoped side-task.

### 2026-09-07 - Stale gate scale-cap corrected; 4K parity failures resolved (side-task)

- Scope: root-caused and fixed the 7 large-display-scale-parity failures
  at 4K recorded in the two 2026-09-07 entries above.
- Plan vs implementation: no plan -- a defect found while reviewing the
  gate's measurement model with the owner. Verification first: the CSS
  computes scale `clamp(min, slope, 1.75)` from the owner's 1.75 ruling
  in `static/css/index.css` line 26, giving 440px x 1.75 = 770.0px form
  width at 4K -- exactly what the gate measured. The gate's
  `expected_scales` formula still capped at the old 2.15, expecting
  780.4px. The 0.9866 ratio reproduces every width/height/cap delta;
  1440p is unaffected because its slope term (1.308) sits below the cap.
  The `headline lineHeight` delta is the only member of the old
  attribution that font metrics could explain; the rest were this cap.
- Implementation: `scripts/dev/frontend_gate.py` outer scale cap
  2.15 -> 1.75 with a comment pinning it to `--index-scale-cap` so the
  next cap change does not repeat the drift. No tolerance changed.
- Deviations: the original attribution ("real kit's tall Instrument
  Serif metrics are not present") was wrong for 6 of the 7 failures and
  is corrected in that entry. The gate's measurement model was the
  question the owner asked; the answer exposed the defect.
- Validation: gate unit module 47 passed. Full gate run: **24 checks
  passed in 43 runs**, exit 0, zero failures, zero timeouts, zero font
  warnings. `pytest -q` -- **938 passed**, 5 warnings. All pre-commit
  hooks pass; `doc_state_sync.py --check` exits 0 (expected root BATCH
  warning).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.
  The gate cap and the CSS token are one fact in two places; a future
  sweep could have the gate read the value, but no further work is
  scheduled now.

### 2026-09-07 - Remove the dead pypdf/pdf2image/pillow cluster (side-task)

- Scope: executed the removal half of F-B21-3's recorded shape. The
  2026-09-07 pip-audit run found 120 advisories in 13 packages; these
  three carried ~65 of them and nothing imports any of them.
- Plan vs implementation: no plan -- owner-directed side-task executing
  F-B21-3's suggestion. Verification before removal: `pip show` metadata
  (pypdf Required-by: nothing; pdf2image Required-by: nothing; pillow
  Required-by: pdf2image only) plus a repo-wide grep for imports across
  scrobblescope/, scripts/, tests/, app.py, templates/, static/js/, the
  Dockerfile and the deployment docs -- zero hits. The JPEG export is
  client-side html2canvas (static/js/results.js), as F-B21-3 already
  recorded; the prior archive log confirms the owner was asked about
  this cluster before and confirmed it serves nothing.
- Deviations: none for the approved scope. Two further dead packages
  were found during verification -- `ipinfo` (Required-by: nothing) and
  `cachetools` (Required-by: ipinfo only) -- but they were not in the
  approved removal list, so they stay pending an owner ruling. The
  owner's correction on `virtualenv` was accepted: it is a real
  dependency of pre-commit (pip show pre-commit: Requires ... virtualenv)
  and stays; `filelock` stays with it. The stdlib `venv` module, not the
  virtualenv package, creates .venv -- the two were conflated in the
  first proposal.
- Validation: `pytest -q` -- **938 passed**, 5 warnings (unchanged; the
  packages were unimported). All pre-commit hooks pass.
- Forward guidance: commit 2 upgrades the vulnerable runtime packages
  (aiohttp, requests, urllib3, werkzeug, flask, python-dotenv, idna,
  click, pytest, virtualenv, filelock). Owner ruling pending on
  ipinfo/cachetools.

### 2026-09-07 - Upgrade vulnerable packages; audit now reports zero (side-task)

- Scope: executed the upgrade half of F-B21-3's recorded shape, plus the
  owner's two rulings from the removal entry: ipinfo and cachetools are
  removed (both dead -- ipinfo Required-by nothing, cachetools required
  only by ipinfo, zero imports), and pip-audit is pinned in
  requirements-dev.txt so the audit is repeatable locally.
- Plan vs implementation: no plan -- owner-directed side-task. Fix
  versions from the audit's own fix_versions, not guesses: aiohttp
  3.11.10 -> 3.14.3, requests 2.32.3 -> 2.33.0, urllib3 2.2.3 -> 2.7.0,
  werkzeug 3.1.3 -> 3.1.6, flask 3.1.0 -> 3.1.3, python-dotenv
  1.1.0 -> 1.2.2, idna 3.10 -> 3.15, click 8.1.8 -> 8.3.3, pytest
  9.0.2 -> 9.0.3, virtualenv 20.28.0 -> 20.36.1, filelock
  3.16.1 -> 3.20.3.
- Deviations: aiohttp 3.14.3 requires aiohappyeyeballs>=2.5.0, so its
  whole dependency family moved with it (aiohappyeyeballs 2.4.4 ->
  2.7.1, aiosignal 1.3.2 -> 1.4.0, frozenlist 1.5.0 -> 1.8.0, multidict
  6.1.0 -> 6.7.1, propcache 0.2.1 -> 0.5.2, yarl 1.18.3 -> 1.24.5) --
  the first install attempt failed with ResolutionImpossible until the
  family was upgraded together. The pinned-requirements discipline
  (AGENTS.md: all ==) is preserved; every new pin is exact.
- Validation: `pytest -q` -- **938 passed**, 7 warnings (two new
  warnings are aiohttp 3.14 deprecation notices, cosmetic). All
  pre-commit hooks pass. Full frontend gate -- **24 checks passed in 43
  runs**, exit 0, zero failures: the aiohttp jump is clean in a live
  browser. `pip-audit` re-run: **0 packages with vulnerabilities, 0
  advisories** (was 13 packages / 120).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.
  F-B21-3's remaining suggestion -- splitting runtime from developer
  requirements -- is still open and unruled. The two new aiohttp
  deprecation warnings are cosmetic; a future sweep could silence them
  at the call sites.

### 2026-09-07 - Fix the B023 route-handler regression the ruff migration introduced (side-task)

- Scope: repaired the two validator checks the ruff migration broke in
  CI (run on `c7bfaec`: "validator race" and "validator network failure"
  both raised `AttributeError: 'Request' object has no attribute
  'append'`), plus three Pylance type errors the owner surfaced while
  reviewing the same file.
- Plan vs implementation: no plan -- regression repair on the open PR.
  Root cause of the CI failures: the B023 fix used a default-argument
  binding (`lambda route, pending=pending: ...`), but Playwright inspects
  the handler's parameter count -- two parameters means it is called with
  (route, request), so the request object overrode the `pending` default
  at call time. The fix is a handler factory (`_collecting_handler`)
  whose closure binds the list with a single visible parameter,
  satisfying both Playwright's contract and bugbear B023. Lesson
  recorded: a lint-driven rewrite of a framework callback must be
  validated against the framework's calling convention, not only the
  linter.
- Implementation:
  - `scripts/dev/frontend_gate.py`: `_collecting_handler` factory used by
    both validator checks; `spotlight_requests` bound before its poll
    loop (possibly-unbound read after a possibly-zero-iteration loop);
    `CHECK_GROUPS` built through an honestly-typed list accumulator with
    a final comprehension producing the declared tuple shape; the
    summary line reads the firefox canary through `groups_for()` instead
    of subscripting `BROWSER_SCOPES` values, whose `None` sentinel for
    chromium's full pass makes direct subscripting a type error. The
    chromium-full-pass / firefox-canary design is unchanged.
- Deviations: none. No check semantics, tolerance, or grouping changed.
- Validation: full gate run -- **24 checks passed in 43 runs**, exit 0,
  zero failures (the two validator checks pass in a live browser), zero
  timeouts, zero font warnings. `pytest -q` -- **938 passed**, 5
  warnings. All pre-commit hooks pass. `doc_state_sync.py --check`
  exits 0 (expected root BATCH warning).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.

### 2026-09-07 - CI action bumps and ruff lint/format migration (side-task)

- Scope: cleared the Node.js 20 deprecation warning on the Quality Gate
  (the run on `d41db1f` flagged checkout/cache/setup-python/upload-artifact
  as forced onto Node 24) and modernized the Python toolchain by replacing
  black + isort + autoflake + flake8 with ruff, per owner request.
- Plan vs implementation: no plan -- owner-directed side-task. Action
  versions were fetched from each repo's latest release, not guessed:
  checkout v4 -> v7, setup-python v5 -> v7, cache v4 -> v6,
  upload-artifact v4 -> v7. Ruff pinned to 0.16.6 (latest at adoption),
  wired through `astral-sh/ruff-pre-commit` v0.16.6 with `ruff-check
  --fix` and `ruff-format` hooks.
- Implementation:
  - `.github/workflows/test.yml`: the four action bumps. No other step
    changed.
  - `pyproject.toml`: `[tool.ruff]` config replaces `[tool.isort]`.
    select = E,W,F,I,UP,B (pycodestyle, pyflakes, isort, pyupgrade,
    bugbear). Ignored: E203/E501 (black-compatible formatter artifacts
    flake8's default ignores already excluded) and E741 (same default
    ignore set). E402 exempted per-file for `app.py` only -- it must call
    `load_dotenv()` before imports that read env at import time. The
    pre-commit exclude list is mirrored in `extend-exclude` (plus
    `scratch/`, untracked).
  - `.pre-commit-config.yaml`: four tool repos replaced by one ruff repo.
  - `requirements-dev.txt`: `flake8==7.3.0` -> `ruff==0.16.6`.
  - Code fixes ruff surfaced (all real, none cosmetic-only): B904
    exception chaining in `dev_start.py` (3) and `docsync/declarations.py`
    (3); B023 loop-variable binding in two `frontend_gate.py` route
    lambdas; B007 unused loop variables renamed in `orchestrator.py` and
    `docsync/declarations.py`; B905 `zip(strict=True)` in
    `docsync/logic.py` and `test_template_shell.py`; E402 mid-file import
    moved to the top of `test_routes.py`; plus 66 safe autofixes (unused
    imports, import sorting, pyupgrade rewrites) and 9 files reformatted
    by ruff-format (black-equivalent; the visible deltas are implicit
    string-concat joins and assert-message placement).
  - Docs: README (Code Quality row, structure comments), CONTRIBUTING
    (code-style section), SESSION_CONTEXT pre-commit line.
- Deviations: none. No tolerance, test, or behaviour changed; the 938
  count is unchanged because ruff's fixes touch no tested path.
- Validation: `ruff check .` -- all checks passed. `ruff format --check`
  -- clean. `pytest -q` -- **938 passed**, 5 warnings. All pre-commit
  hooks pass (ruff check, ruff format, and the 8 surviving hooks).
  `doc_state_sync.py --check` exits 0 (expected root BATCH warning).
- Forward guidance: WP-7 (unmatched page + reason_code) remains next.
  The Quality Gate run on this push should show no Node 20 warning.
