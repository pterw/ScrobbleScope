# CI Parallel Jobs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the single `quality-gate` job in `.github/workflows/test.yml` into parallel jobs behind an aggregator, so a run takes about 1.5 minutes where it now takes about 7, and a docs-only pull request skips the browser job.

**Architecture:** Four jobs: `changes` (is this pull request docs-only), `checks` (install, docsync, pre-commit, pytest, advisory pip-audit), `browser` (Playwright and the frontend gate) and `quality-gate` (the aggregator, the only required check). The two decisions that can produce a wrong green (docs-only classification, aggregation) live in one tested stdlib script, `scripts/dev/ci_jobs.py`, not in inline YAML shell. The ruleset `main-protection` keeps requiring the context `quality-gate`; it needs no change.

**Tech Stack:** GitHub Actions YAML, a stdlib-only Python script, pytest (the script's functions called directly; the workflow read as text only for secrets and the Playwright cache sequence). Actions cannot run locally; acceptance is this pull request's own CI plus one post-merge check.

## Global Constraints

- Owner rulings. O25 (2026-10-31): "splitting the job into parallel jobs with an aggregator is a sound idea. The ruleset can always change, I'm fine with that. The time saving cost from 7 minutes to 1.5 is a big gain". O24: gates are scoped to what changed. O27: PRs may stack; this branch `ci/parallel-jobs` is cut from PR #284's head (`docs/paginate-archives`, `881f00d7`). The owner asked that every doc referencing the CI be checked and updated where the split makes it untrue.
- `AGENTS.md` and `docs/agents/global-rules.md` bind this work. Stage paths by name; never `.superpowers/`.
- Triggers unchanged (push to `main` and `wip/**`, `pull_request`, `workflow_dispatch`). Python version, coverage settings (`--cov-fail-under=70`), test selection and `C:/ssw/tools/ci_judge.py` do not change.
- Every job keeps `permissions: contents: read` and `persist-credentials: false` on every checkout. No provider secret outside a step-level `env:`. Job-level `env: FLASK_ENV: development` goes on each job that runs app code (`checks`, `browser`).
- Existing comments move with the step they explain; trim only what the split makes untrue.
- Measured baseline (run 41179864550, one job, about 400 s): install 11 s, docsync preflight 1 s, pre-commit 12 s, pytest with coverage 56 s, Playwright install 23 s, frontend gate 274 s, pip-audit 12 s. The repository is public, so minutes are free.
- Expected, not defects: `ERROR WT003` and `WARNING WT010` from the worktree hook, the root `BATCH23_DEFINITION.md` warning and the two `WARNING DOC024` lines on the findings archive pages.

## Frozen decisions

1. **`changes`** (`ubuntu-latest`, read-only, runner `python3`, no setup-python): outputs `docs_only` as the string `true` or `false`. Plain git plus `python3 scripts/dev/ci_jobs.py docs-only`; no third-party action. Only a `pull_request` event can be docs-only. A push (to `main` or `wip/**`) and `workflow_dispatch` always output `false`; no diff is computed for them.
2. **Docs-only is a skip-list, and the whole pull request is diffed against its base.** `true` only when the changed-path list is non-empty and every path matches `docs/**`, `**/*.md` (any depth, including the repository root), `.superpowers/**` or `config/docsync.toml`. Any other path, including a new top-level one, outputs `false`. The classification is `python3 scripts/dev/ci_jobs.py docs-only` (decision 8); the workflow only computes the diff and pipes it in.
   - The diff uses `--no-renames` so a file moved out of a docs path counts under its old path as well, and `-z` so a path with spaces or quotes is matched whole.
   - The diff has merge-base semantics: it lists what the pull request changes relative to its base, not what the base gained since the branch was cut. The default `refs/pull/N/merge` checkout with `fetch-depth: 2` and `HEAD^1..HEAD` gives exactly that (`actions/checkout` fetches both parents of the merge commit at depth 2); the implementer may choose another way that keeps the property.
   - Fail closed: if `HEAD^2` does not resolve, or the diff cannot be computed (shallow history, missing ref, a merge conflict that leaves no merge ref), the step outputs `false` (or the job fails, which the aggregator turns into red). An empty list also prints `false`.
   - A per-push diff (`before..after`) is rejected: a docs-only commit on top of a code pull request would skip the browser job while the pull request still changes code, a wrong green. Consequence: on any pull request that changes the workflow or code, `docs_only` stays `false` for the pull request's whole life.
3. **`checks`**: checkout, Python 3.13 with the pip cache, the Tailwind asset cache, dependency install, docsync preflight, pre-commit with `SKIP: worktree-alignment`, the Tailwind digest print, `pytest -m "not browser"` with the same coverage flags, the coverage upload, then the advisory pip-audit step with `continue-on-error: true`. pip-audit stays a step of `checks`, so `advisory-steps` in the `ci` block keeps matching. Step order and comments as today.
4. **`browser`**: `needs: changes`; `if` runs it unless `needs.changes.outputs.docs_only == 'true'`. It needs its own checkout, Python 3.13 with pip cache, dependency install and (if the gate needs it; confirm by reading `scripts/dev/frontend_gate.py` and `scripts/dev/_frontend_gate*.py`) the Tailwind asset cache. It keeps the runner-image step, the Playwright apt cache restore, install and save sequence (F-B23-57) in that order and unchanged, and the three browser commands in their current order (`pytest -m browser -q`, `results_behavior_tests.py`, `frontend_gate.py`).
   - The existing `fly.io-deploy` / `flyio-deploy` head-ref condition **stays on the step that runs the three commands, as now**, not on the job. This matters: a job-level skip for those heads would be a "browser skipped for another reason" and the aggregator would fail. The install steps still run for those heads, as today.
5. **`quality-gate`** (the aggregator, keeping this exact job name): `needs: [changes, checks, browser]`, `if: always()`, `permissions: contents: read`. It checks out (`persist-credentials: false`) and runs `python3 scripts/dev/ci_jobs.py aggregate` with the runner's `python3` (no setup-python), passing the three `needs.*.result` values and `needs.changes.outputs.docs_only` through the step's `env:` (never interpolated into the script). The script exits 0 only when `changes` is `success`, `checks` is `success`, and `browser` is `success`, or `browser` is `skipped` and `docs_only` is `true`. Every other combination exits 1 and prints which input failed: a failed or cancelled `browser`, a `browser` skip while `docs_only` is not `true` (for example `changes` failed, so its output is empty), a failed or cancelled `changes` or `checks`. If the checkout itself fails the job is red: fail closed.
   - **`if: always()` is deliberate and stays** (not `!cancelled()`): a cancelled run reads red, which is the safe side. The implementer does not change it.
6. **Docs-only does not need `config/docsync.toml` in the browser job.** Confirmed by grep at plan time and again by the plan review: nothing the browser job executes (`scripts/dev/frontend_gate.py`, `scripts/dev/_frontend_gate*.py`, `scripts/dev/results_behavior_tests.py`, `tests/frontend`) reads `config/docsync.toml`; the only mentions in `scrobblescope/heatmap.py:43` and `static/css/tailwind.src.css:161` are comments. The implementer repeats the grep and stops with NEEDS_CONTEXT if it now finds a read.
7. **Job count and the watcher block (controller step).** The run has four jobs. When Task 1 lands, the controller (not an implementer; the block is untracked) replaces the workspace `ci` block with: `jobs: 4`; `blocking:` `'quality-gate'` and `'checks'`; `changes` and `browser` advisory to ci_judge (a skipped `browser` is OK; a failed one also fails `quality-gate`, which is blocking); `advisory-steps:` `'Security audit (pip-audit)'`; `scan-log: checks` with the same `extract:` patterns (the pytest counts live in that log); `timeout-min` reviewed against the new run time. The browser job's evidence is its conclusion, and the ci-watcher saves its failed log when it fails. Extracting the frontend-gate line from a second job is a ci-watcher feature request, not part of this pull request.
8. **`scripts/dev/ci_jobs.py`, frozen interface.** Stdlib only, no side effects at import, functions callable from tests.
   - `python3 scripts/dev/ci_jobs.py docs-only` reads NUL-separated changed paths on stdin, prints `true` or `false` and exits 0. Empty input, or input made only of NUL separators, prints `false` (fail closed).
   - `python3 scripts/dev/ci_jobs.py aggregate --changes R --checks R --browser R --docs-only true|false` (each `R` is a `needs.<job>.result` value) exits 0 only under decision 5's rule, otherwise exits 1 and prints which input failed it. An empty or unrecognised `--docs-only` value is a failure: it exits 1, never 0.
   - The workflow computes the diff with git and pipes it in. No YAML string pin guards these two decisions; the script's tests do.

## Delivery sequence

- [x] Commit this plan as the branch's first commit (controller, before Task 1).
- [x] Task 1: add `ci_jobs.py` with its tests, split the workflow, adapt the workflow tests.
- [x] Controller step after Task 1 lands: replace the workspace `ci` block per decision 7.
- [x] Task 2: documentation sweep.
- [x] Task 3: execution record (docs only, last): this pull request's full-run evidence.
- [x] Acceptance (a), on this pull request's CI: the head that changes the workflow runs all four jobs and `quality-gate` succeeds.
- [x] Acceptance (b1), local: the docs-only truth table and the aggregator truth table pass (Task 1).
- [ ] Acceptance (b2), after merge (controller): on the first docs-only pull request, `browser` is skipped and `quality-gate` succeeds; the controller records it. It cannot be observed on this pull request, because decision 2 diffs the whole pull request, which changes the workflow.

## Task 1: Script, workflow split and tests

**Wave:** 1. **After:** the plan commit. **Mode:** serial, one implementer.
**Touches:** `scripts/dev/ci_jobs.py` (new), `tests/scripts/dev/test_ci_jobs.py` (new; place and import it the way the neighbouring `tests/scripts/dev` tests import `scripts/dev` modules), `.github/workflows/test.yml`, `tests/test_ci_workflows.py`; plus the side-task log entry and measured docsync counts the commit procedure requires (controller-owned bookkeeping).
**Gates:** `tests/scripts/dev/test_ci_jobs.py`, `tests/test_ci_workflows.py`, the three suite shards, `pre-commit run --all-files` (its `check yaml` hook parses the workflow), `doc_state_sync.py --check`. The frontend gate is not required: no template, static file or gate script changes.

**Interfaces:** consumes the current single-job workflow; produces the script of decision 8 and the four jobs of decisions 1 to 5 with the step bodies moved, not rewritten.

- [x] **Read and confirm.** Read `.github/workflows/test.yml`, `tests/test_ci_workflows.py` and one neighbouring `tests/scripts/dev` test for the import style. Repeat the decision 6 grep. Read the gate scripts to decide whether `browser` needs the Tailwind cache.
- [x] **Script tests first (RED).** Write `tests/scripts/dev/test_ci_jobs.py`, calling the script's functions directly, each test with a GIVEN/WHEN/THEN docstring:
  - One parametrized truth table for `aggregate`: every combination of the result values (`success`, `failure`, `cancelled`, `skipped`) for `changes`, `checks` and `browser` with `docs_only` `true`, `false` and empty, asserting exit 0 only for the two allowed shapes (all three `success`; `changes` and `checks` `success` with `browser` `skipped` and `docs_only` `true`). It must include a failed and a cancelled `changes`, a `browser` skip without docs-only, and a failed `checks` with a green `browser`. It also has a row for an empty and for an unrecognised `--docs-only` value (for example `maybe`), each expected to exit 1 and never 0. A failure message names the offending job.
  - One parametrized table for `docs-only` (NUL-separated input): a path under `docs/`; a `.md` at the repository root and at depth; a `.superpowers/` path; `config/docsync.toml`; each of those mixed with one code path (`false`); a new top-level path (`false`); a path with a space; empty input (`false`); an input made only of NUL separators (`false`); near-miss negatives that a loose prefix or suffix match would wrongly accept, each `false`: `docs_tools/x.py`, `app/docs/x.py`, `notes.mdx`, `sub/config/docsync.toml`, `config/docsync.toml.bak`.
  - Run it and see it fail because `scripts/dev/ci_jobs.py` does not exist (the right reason).
- [x] **Workflow tests, adapt (RED).** Adapt the existing `tests/test_ci_workflows.py` tests to the new layout instead of adding copies. One shared helper returns the lines of a named job; the job-level `env:` reader and the step reader are both built on it (neither returns "the first block in the file").
  - The no-secret rule holds for every job: the env reader finds `FLASK_ENV` on `checks` and `browser`, and the secret scan keeps reading the whole file. Update the module docstring ("the CI quality-gate job") to say every job.
  - The Playwright cache test finds its four steps in the `browser` job, in the same order and with the same checks.
  - No new YAML text pin for the docs-only patterns or the aggregator condition (decision 8). Run the file and see the adapted tests fail against the unchanged single-job workflow (no `browser` job).
- [x] **Build the script (GREEN).** Write `scripts/dev/ci_jobs.py` per decision 8, the simplest code that passes the tables; the `**/*.md` match must cover a root-level `README.md` (a plain shell `case` does not do this, which is why the logic is in Python).
- [x] **Build the workflow (GREEN).** Write the four jobs per decisions 1 to 5. `changes` and `quality-gate` call the script as decision 8 says. Keep every existing comment with its step; rewrite only comments the split falsifies (for example "Last on purpose. Starting a browser costs far more than a lint ... so every cheaper gate reports first" is now untrue: the jobs run in parallel, so reword it to say the browser job is the slowest and runs beside the cheaper ones). Re-run both test files to green.
- [x] **Prove the new tests bite.** In the script, make one temporary change per decision and see the table fail, then undo it: accept a `browser` skip without checking `docs_only` (aggregator); drop `docs/**` from the patterns, or let empty input print `true` (docs-only). Report command and output. No `mutate.py` run unless a `tests/mutants/*.json` is edited, which is not expected.
- [x] **Gates and commit.** Run the gates; the commit is `ci: Run the quality gate as parallel jobs`, body saying why (about 7 minutes to about 1.5, docs-only pull requests skip the browser job, one required context unchanged). The side-task entry sits directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker, untagged, with the measured test count. Push is the controller's.

**Acceptance (task level):** the workflow parses; both test files are green with the tables proven red first; the diff shows the step bodies moved, not changed, apart from the comments named above and the `if` on the three browser commands staying on that step; the two decision-8 invocations in the workflow match the frozen interface.

## Controller step after Task 1

Not an implementer task. When Task 1 lands, the controller edits the untracked workspace `ci` block per decision 7 (`jobs: 4`, blocking `quality-gate` and `checks`, advisory step unchanged, `scan-log: checks`, same `extract:` patterns, timeout reviewed) before the ci-watcher is dispatched for the pushed head.

## Task 2: Documentation sweep

**Wave:** 2. **After:** Task 1. **Mode:** serial, one implementer.
**Touches:** `DEVELOPMENT.md`, `docs/architecture/documentation-tooling.md`, `docs/architecture/development-cycle.md`, `tests/scripts/dev/test_frontend_gate.py` (one docstring line); bookkeeping as in Task 1.
**Gates:** `pre-commit run --all-files`, `doc_state_sync.py --check`, the three suite shards (a docstring edit still goes through the same shards). Mermaid diagrams are rendered by the controller, not the implementer.

The hit list is `.superpowers/sdd/2026-10-31-ci-split/sweep-ci-references.md` in the main checkout. Point-in-time records (log entries, dated specs, findings, archives) are not edited.

- [x] **Hits that describe structure, steps or order.** Check each against the new layout and fix where now untrue:
  - `DEVELOPMENT.md:592-597`: the frontend gate runs in the `browser` job, which is skipped for a docs-only pull request; the coverage step is in `checks`; pip-audit is in `checks`. Keep the pointer to `.github/workflows/test.yml`; name `scripts/dev/ci_jobs.py` as the home of the docs-only and aggregation rules where the paragraph describes them.
  - `docs/architecture/documentation-tooling.md:468` and `:492`: "CI's explicit Run docsync preflight step" stays true as a step name; add the job (`checks`) only if the sentence would otherwise mislead.
  - `docs/architecture/development-cycle.md:70-78`: the paragraph says CI runs everything in one sequence. Rewrite to the four jobs: `checks` and `browser` run in parallel, `changes` decides whether `browser` runs, `quality-gate` aggregates, and say which pull requests skip the browser job (those whose whole diff against the base is docs paths).
  - `docs/architecture/development-cycle.md:33` and `docs/architecture/documentation-tooling.md:104-110` (Mermaid nodes naming the Quality Gate): change only if the node text or edges are now false (for example "runs before PC"). If a diagram changes, list it in the report for the controller to render.
  - `tests/scripts/dev/test_frontend_gate.py:4`: "which is what the Quality Gate does" is still true of the aggregate; reword to "which is what the CI browser job does" if the implementer judges the old wording misleading.
  - `tests/test_ci_workflows.py:1` and `:110` were handled in Task 1; confirm they read correctly.
- [x] **Hits that name the workflow or file only.** Read once, leave if still true: `README.md:12` (badge), `:21`, `:198`, `:714`; `DEVELOPMENT.md:869`; `docs/agents/AGENT_NOTES.md:311`, `:323`, `:326`, `:339`, `:343`. If the badge or a sentence implies one job or one sequence, fix it; otherwise record "read, still true".
- [x] **Re-sweep.** Grep tracked files for `quality-gate`, `Quality Gate`, `frontend gate` and `Run frontend gate` to catch a mention the sweep list missed; list new finds and decisions in the report.
- [x] **Untracked items are the controller's, listed in the report only:** the `ci` blocks in workspace `constraints.md` files (done by the controller step after Task 1; confirm no other workspace still says `jobs: 1`).
- [x] **Commit** `docs(ci): Describe the parallel CI jobs`, with the side-task entry and measured counts.

**Acceptance (task level):** every "describe structure" hit is either corrected or recorded as still true with the reason; no tracked live document still says CI runs one sequence of steps in one job; docsync check passes.

## Task 3: Execution record

**Wave:** 3. **After:** Task 2 and the CI result of the workflow-changing head. **Mode:** serial, docs only.
**Touches:** this plan (tick checkboxes, add the record) and the PLAYBOOK/log bookkeeping the commit procedure requires. No workflow, code or test file.
**Gates:** `pre-commit run --all-files`, `doc_state_sync.py --check`, the suite shards.

- [x] Record on the plan the CI run for the head that changed the workflow: four jobs, job durations, and `quality-gate` success (acceptance a). A failed aggregator or a skipped `browser` there is a defect to fix in Task 1's files, not to record.
- [x] Record that acceptance (b1) passed locally (the two truth tables, with the test counts) and name (b2) as the controller's post-merge check on the first docs-only pull request. Do not try to show a skipped `browser` on this pull request: by decision 2 its diff includes the workflow, so `docs_only` is `false` here and `browser` runs on every head; that is correct behaviour, not a defect.
- [x] Commit `docs(plan): Record the CI parallel jobs execution`. Tick the delivery sequence boxes that hold (a, b1); leave (b2) open for the controller.

**Acceptance (task level):** the plan holds the full-run evidence of this pull request and names (b2) as the post-merge check; no claim of a skipped browser job on this pull request.

## Definition of done

- Acceptance (a) holds on the pull request's CI with `quality-gate` success; (b1) passes in `tests/scripts/dev/test_ci_jobs.py`; (b2) is recorded by the controller after merge, on the first docs-only pull request.
- `tests/scripts/dev/test_ci_jobs.py` and `tests/test_ci_workflows.py` are green; pre-commit and `doc_state_sync.py --check` pass with only the expected advisories.
- The workspace `ci` block was updated by the controller per decision 7.
- The ruleset still requires `quality-gate` and was not edited.
- Owner is told: the required context is now the aggregator; a skipped browser job on a docs-only pull request is intended; a push to `main` always runs every job; a pull request that changes any non-docs path runs the browser job on every push.

## Execution record

Pull request #285, branch `ci/parallel-jobs`, stacked on PR #284 (decision O27).

| Commit | Subject | Review outcome |
|--------|---------|----------------|
| `47c2a9ba` | `docs(plan): Plan the CI split into parallel jobs` | Reviewed once, then fixed in 2 rounds, the second without its own re-review |
| `496e3651` | `ci: Run the quality gate as parallel jobs` | Approved after 1 fix round (`fbb6f449`, `test(ci): Tighten the CI split tests after review`) |
| `3ca1f53b` | `docs(ci): Describe the parallel CI jobs` | Approved |

**Acceptance (a), CI evidence.** Run 41223708194 at head `3ca1f53b`, which includes the workflow change, ran all four jobs and all four succeeded: `changes` 7 s, `checks` 74 s (2997 passed, 4 skipped, 156 deselected), `browser` 313 s, `quality-gate` 4 s. `changes` and `checks` started together, and the whole run took 5 min 32 s, against 6 min 47 s for PR #284's single job (run 41219439839). `browser` ran, as decision 2 requires: this pull request changes the workflow, so `docs_only` is `false` here on every head. That is correct behaviour; this run does not show a skipped `browser`, and it could not.

**Acceptance (b1), local.** `tests/scripts/dev/test_ci_jobs.py` passes (37 tests): the `aggregate` truth table (the full product of `success`, `failure`, `cancelled` and `skipped` for the three jobs with `docs_only` `true`, `false` and empty, accepting only the two allowed shapes) and the `docs-only` table (including the near-miss paths and empty or NUL-only input). With `tests/test_ci_workflows.py` the two files hold 46 tests, all passing.

**Acceptance (b2), open, the controller's post-merge check.** On the first docs-only pull request after merge, confirm `browser` is skipped and `quality-gate` succeeds, and record it here. It cannot be observed on this pull request.
