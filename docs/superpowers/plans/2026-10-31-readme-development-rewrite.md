# README and DEVELOPMENT Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `README.md` and `DEVELOPMENT.md` so a reader sees a mature web app, built with stated engineering choices under a Fly.io cost ceiling, and sees each development tool running. Screenshots are refreshed, the cache's role and speed are stated once with a date, and the "what shipped in September" and "what is planned" sections are gone.

**Architecture:** One frozen interface, a facts file (`facts.md`, in the plan workspace), written first from source. The README and DEVELOPMENT writers both consume it, and each links to the other and to `docs/ARCHITECTURE.md` instead of repeating a fact (AGENTS.md anti-duplication). Screenshots and the cache measurement are independent Wave 0 tasks, and each writes its own workspace output. The two rewrites are parallel code phases that return patches; the controller dispatches the landings (`MODE: land`, one sdd-implementer each) serially. Every task writes its report to the workspace as `task-<N>-code-report.md`.

**Tech Stack:** Markdown, PNG/JPEG images under `docs/images/`, agent-browser against production, a local run for the cache measurement. No code changes.

## Global Constraints

- Owner brief, verbatim, section "Docs rewrite" of `.superpowers/sdd/2026-10-31-ui-bugfix/owner-brief-later-work.md` (workspace file, untracked): the README is "stale", DEVELOPMENT.md "is stale"; both are re-written with screenshots, the graceful degradation, "the intentional architechtural constraints of the fly.io cost of <$5 and how that shaped engineering", the streamgraph and heatmap pipelines "along the top albums at a high-level", "a better tech stack explanation, more human prose, less clutter, but still focusing on technical and engineering achivements and choices". The cache is not "optional" in the sense that undersells it: say what it does for speed, how it works, and the delta without it. "What shipped in september" and "what is planned" go.
- Owner rulings 2026-10-31. O34: "make sure to use /writing-guidelines when doing so". O35: screenshots "small-sized and side-by side", taken with agent-browser from production (`https://scrobblescope.fly.dev`) with the Last.fm user `flounder14`, plus the owner's light-mode streamgraph and heatmap export `C:/Users/peter/Downloads/scrobblescope_flounder14_heatmap.jpg` (3018x1710, 789 KB; downscale it). The cache speed is measured once, cold against warm, same account and period, and stated once in prose with its date. It is not a docsync-declared value. O27: the branch `docs/readme-development-rewrite` is cut from the docsync PR head `bde173bf`.
- Owner preferences (memory, 2026-10): the README is recruiter-friendly but technical and carries no machine-checked numbers; DEVELOPMENT shows each tool running (a command plus a short real output excerpt). The older preference for visible updates in the README is superseded for this rewrite by the owner's explicit answer (O35, 2026-10-31): "Remove both entirely". The README has no changelog and no "Recent changes" list. It shows maturity with concrete facts (users, uptime design, gates), not adjectives; the word "very" is banned.
- Writing rules. Every writing task and its review apply the guidelines copy `.superpowers/sdd/2026-10-31-docs-rewrite/writing-guidelines.md` (workspace). Some rules are for Vercel's docs site and do not apply to a GitHub README: `meta.contentType` and the page-plan metadata. The rest apply: plain words, short active sentences, one idea each, the banned words. AGENTS.md "Markdown Authoring Rules" wins on conflict: ASCII only (`--` not an em-dash, straight quotes) and ISO dates.
- `AGENTS.md` and `docs/agents/global-rules.md` bind this work. Stage paths by name; never `.superpowers/`. No attribution trailer.
- Sources for facts: `DEPLOY.md`, `docs/ARCHITECTURE.md`, `docs/architecture/`, `.claude/SESSION_CONTEXT.md`, `config/docsync.toml`, `.github/workflows/test.yml`, `scripts/dev/` and `scrobblescope/`. Diagrams are verified against source, not trusted (AGENTS.md Anti-Pattern Registry, item 15, "Trusting an architecture diagram without checking source").
- Fly.io facts the prose must state, each checked against `fly.toml`, `Dockerfile` and `DEPLOY.md`: slim image, `init_db.py` as the release command, one worker with four threads, 512 MB, scale to zero with an idle exit, a cost ceiling under $5 a month (owner brief).
- Expected, not defects: `ERROR WT003` and `WARNING WT010` from the worktree hook, the root `BATCH23_DEFINITION.md` warning and the two `WARNING DOC024` lines on the findings archive pages.

## Gate traps (state them to every writer)

- `config/docsync.toml` declares `README.md` with pattern `last (\d+) days` and `expect = "365"`. Keep one README sentence that matches (the heatmap window), or change the declaration in the same commit. Silent deletion fails `--check`.
- DOC001: every backticked path the docs cite must be a tracked file. Cite only paths that exist at the landing commit.
- DOC010: cite AGENTS.md rules by their current heading, not by a number or a remembered name. Read the heading at HEAD.
- `Last updated:` lines: update the date in any file that carries one, whenever its content changes. Do not add one to a file that has none.
- README badges: the PostgreSQL badge says "optional cache". The owner brief says that undersells the cache. Reword or replace it, and check any other badge for a claim that is no longer true.
- Machine-checked numbers (test count, coverage, window days) must not appear in the README except the one declared window sentence. DEVELOPMENT may show a real output excerpt, but an excerpt that contains a pinned value must match the pin at the landing commit or leave the number out.

## Delivery sequence

- [ ] Commit this plan as the branch's first commit (controller).
- [ ] Wave 0, parallel: Task 1 (facts), Task 2 (screenshots), Task 3 (cache measurement).
- [ ] Wave 0 review: one sdd-reviewer reads `facts.md`, `cache-measurement.md` and the staged images; facts are checked against their cited sources, images against the O35 rulings. The controller then approves Wave 1.
- [ ] Wave 1, parallel code phases: Task 4 (README), Task 5 (DEVELOPMENT).
- [ ] Landings, serial, each a `MODE: land` dispatch by the controller: Task 4 first (with the images), then Task 5. A gate-runner follows each.
- [ ] Review of each destination file, whole file, against the guidelines and `facts.md`.
- [ ] Execution record (docs only, last).

## Task 1: Facts file

**Wave:** 0. **After:** the plan commit. **Mode:** serial, one implementer, in the workspace (writes outside the repository). **Touches:** `facts.md` in the workspace only.

**Interfaces:** consumes the sources under Global Constraints; produces the frozen interface both writers read. Each fact carries its source path (and line or heading); a fact with no source is not written.

- [ ] **Stack.** Language, framework, server, database, cache store, front end, charting and test tooling, each as a one-line fact.
- [ ] **Three pipelines, high level.** Top albums, the heatmap and the streamgraph: input, provider calls, aggregation, output. Check each against source and the diagrams in `docs/architecture/`; where a diagram disagrees with source, record the source's answer and note the diagram as stale.
- [ ] **Graceful degradation.** Each path a provider or the cache can fail on, what the user sees, and what is retried or skipped (Last.fm, Spotify, Deezer, the cache, job expiry).
- [ ] **Cache mechanics.** What is cached, the key, the expiry, how a hit and a miss flow, and what the app does with the cache unavailable. Do not write the measurement; Task 3 records it in its own file `cache-measurement.md`.
- [ ] **Fly.io constraints and their effect on the engineering.** For each constraint under Global Constraints, the design choice it caused, with the source.
- [ ] **CI layout.** The four jobs and what each runs, from `.github/workflows/test.yml`.
- [ ] **Gates and tools DEVELOPMENT must show.** Each tool, its exact command, and where its configuration lives. Name only tools tracked at the plan's base (`git ls-files` decides): pytest and its markers (CI runs `pytest -m "not browser"`), pre-commit and its hooks, `scripts/doc_state_sync.py`, the frontend gate, the Tailwind build, the worktree guard, CI and formatters. No mutation script and no shard runner unless `git ls-files` shows them. The writer runs the commands; this list says which.
- [ ] **Stale-claims list.** Every claim in the current README and DEVELOPMENT that source contradicts (a section name, a path, a command, a count), so the writers know what not to carry over.

**Acceptance:** every fact has a source path that exists at HEAD (`git ls-files` check); no section copies a paragraph from the README or DEVELOPMENT; the cache mechanics section carries no timing figure (Task 3 owns that); the file is ASCII only. Report: `task-1-code-report.md`.

## Task 2: Screenshots

**Wave:** 0. **After:** the plan commit. **Mode:** serial, workspace-only. **Touches:** the workspace folder `images/` only; it commits nothing and writes nothing in any repository worktree.

**Interfaces:** produces the final, downscaled image files in the workspace folder `images/`, which Task 4 copies into `docs/images/`; consumes production with the account `flounder14`.

- [ ] **Capture.** With agent-browser, in Firefox where it works (the owner browses with Firefox only), capture the results page for a fixed period, the heatmap, the streamgraph, the loading state and one degraded state if reachable without harm. Every browser run is wrapped in `C:/ssw/tools/with_browser_lock.py` with the absolute venv Python. Never write to production beyond loading pages and submitting the `flounder14` form.
- [ ] **Owner export.** Downscale `scrobblescope_flounder14_heatmap.jpg` to the same display size family as the captures.
- [ ] **Size and layout.** Choose one display width so two images sit side by side in a README table row; keep each file under 200 KB (the export under 150 KB); record each file's pixel size and bytes in the report. Reuse an existing image only if it still matches the live UI.
- [ ] **Alt text.** Draft one plain alt text per image in the report for the README writer.

**Acceptance:** each new image opens and shows the page named; none shows a username other than `flounder14`; every file is under its stated size; names are lower snake case beside the existing ones; the report lists which existing images in `docs/images/` stay referenced and which become unreferenced (the README task decides on removal). Report: `task-2-code-report.md`.

## Task 3: Cache measurement

**Wave:** 0. **After:** the plan commit. **Mode:** serial, local only. **Touches:** `cache-measurement.md` in the workspace only. The writers read `facts.md` and `cache-measurement.md`.

**Interfaces:** produces one dated measurement. The method is controller-approved before the run; the controller reads the proposed method in the first report and replies.

- [ ] **Local only.** The task refuses to start unless `DATABASE_URL` points at `localhost` or `127.0.0.1`. It never reads Fly secrets, never runs `fly` and never connects to the production database. It uses the provider keys from the local `.env`.
- [ ] **Preconditions.** A local Postgres is reachable. If none is available the task stops with NEEDS_CONTEXT; do not substitute SQLite or a fake.
- [ ] **Measure.** The same account (`flounder14`) and period twice: cold, then warm. For the cold run, empty only the local cache table (named in `init_db.py`) in that local database. Record wall-clock time for each run, the run count (at least three of each, report the median and range), the date, the machine class, and the network state. Say what is cached on a warm run and what is not (provider calls that still happen).
- [ ] **Record.** Write `cache-measurement.md` with the account, the period, both timings, the date in ISO form and the method in two sentences. State that the figure is a single-machine reading, not a guarantee.

**Acceptance:** the raw timings, the median and the date are in the report (`task-3-code-report.md`) and in `cache-measurement.md`; the section says which calls the cache removes; the measurement is not added to `config/docsync.toml` and appears in no gate.

## Task 4: README rewrite

**Wave:** 1. **After:** the Wave 0 outputs exist and the Wave 0 review approved them. **Mode:** code phase in a detached worktree `C:/ssw/t<N>`, then land. **Touches:** `README.md`, and `docs/images/` files. The code phase copies the Task 2 images from the workspace `images/` into `docs/images/` in its own worktree and writes its patch with `git diff --binary`; the landing applies it with `git apply --index`, so the images land with the README.

**Interfaces:** consumes `facts.md`, `cache-measurement.md` and the Task 2 images; produces the README. It links to `docs/ARCHITECTURE.md`, `DEPLOY.md` and `DEVELOPMENT.md` for depth and does not repeat them.

- [ ] **Read the whole current README and `facts.md` first.** Keep what source still supports; drop the rest. Do not paste from either; write from the facts.
- [ ] **Shape.** One short opening that says what the app does and for whom; the screenshots side by side near the top; the three pipelines at a high level (top albums, heatmap, streamgraph); graceful degradation; the cache (role, how it works, the dated speed figure, once); the Fly.io cost ceiling and how it shaped the engineering; the tech stack with the reason for each choice; where to go next (links). No changelog and no "Recent changes" list (O35, "Remove both entirely"). Show maturity with concrete facts (users, uptime design, gates), not adjectives; do not use "very".
- [ ] **Remove.** The "what shipped in September" section, the "what is planned" section and every forward-looking line about Spotify import.
- [ ] **Badges and gate traps.** Apply the Gate traps above: keep the declared `last N days` sentence, fix the PostgreSQL badge wording, update any `Last updated:` line.
- [ ] **Self-check against the guidelines.** Recruiter-friendly but technical; plain words; no clutter; the banned words absent.
- [ ] **Code phase outputs.** The patch (docs only, with the images), the report with a Handoff section (commit subject and draft body, the PLAYBOOK Section 3 and 4 text), and the nested gate-run.

**Acceptance:**
- No heading or sentence mentions "shipped in September" or a planned-features list; `grep -in "september\|planned\|roadmap" README.md` has no hit, or each hit is listed in the report and cleared.
- Every image the README references exists in `docs/images/` and is under its Task 2 size; every relative link resolves to a tracked file.
- The cache section states the dated measurement once and the role of the cache in a few sentences; the figure appears nowhere else: `git grep` for it across the repository, excluding `facts.md`, `cache-measurement.md` and this plan, finds only the README.
- The README holds no test count, coverage figure or other docsync-pinned number except the declared window sentence; `doc_state_sync.py --check` is clean apart from the expected lines.
- The words `easy`, `simple`, `simply`, `quick`, `very`, `just` and `really` do not appear; the file is ASCII only (`grep -nP '[^\x00-\x7F]' README.md` is empty).
- Report: `task-4-code-report.md`.

## Task 5: DEVELOPMENT rewrite

**Wave:** 1. **After:** the Wave 0 outputs exist and the Wave 0 review approved them (it needs `facts.md` only, not the images or the cache figure). **Mode:** code phase in a detached worktree `C:/ssw/t<N>`, then land. **Touches:** `DEVELOPMENT.md` only.

**Interfaces:** consumes `facts.md` (CI layout, gates and tools lists); produces DEVELOPMENT. It links to the README for the product, to `docs/ARCHITECTURE.md` for design and to `AGENTS.md` for rules, and does not restate them.

- [ ] **Read the whole current DEVELOPMENT.md and `facts.md` first.** Drop what the stale-claims list names.
- [ ] **Run each tool.** For every tool in the facts file's tool list, run its command in the worktree and paste a short real output excerpt (the last few lines, or the lines that prove it ran). No invented output. Where a tool needs a service that is not available (a browser, a database), say so and show the command only, once, with the reason. Every browser run (the frontend gate, browser tests) is wrapped in `C:/ssw/tools/with_browser_lock.py` with the absolute venv Python. The tool list holds only tools tracked at the plan's base: no mutation script and no shard runner unless `git ls-files` shows them.
- [ ] **Shape.** Setup from clone to a running app; the test layout and the pytest commands with their markers; the frontend gate; docsync and the commit procedure (linked to AGENTS.md rather than copied); pre-commit; the CI layout in short, linked to the workflow; troubleshooting that a newcomer meets. Plain prose between the command blocks.
- [ ] **Gate traps.** DOC001 and DOC010 as above; keep a `Last updated:` line current only if the file carries one. An excerpt that shows the test count must equal the `[test_count]` pin at the landing commit, or omit the number.
- [ ] **Code phase outputs.** The patch, the report with a Handoff section and the nested gate-run.

**Acceptance:**
- Every tool section under the tool list has a command and a real output excerpt, or a stated reason the output is absent.
- No cited command fails with "not found" when run from the repository root; every cited path is tracked.
- The README's content is linked, not repeated; no paragraph is shared with the README, `DEPLOY.md` or AGENTS.md.
- Banned words absent (including `simply`), ASCII only, `--check` clean apart from the expected lines.
- Report: `task-5-code-report.md`.

## Dispatch

| Wave | Tasks | Mode | Agents (peak) |
|------|-------|------|---------------|
| 0 | 1 facts, 2 screenshots, 3 cache measurement | three serial implementers in parallel; each writes its own workspace file, none writes tracked code | 3 |
| 0 review | `facts.md`, `cache-measurement.md`, images | one sdd-reviewer | 1 |
| 1 | 4 README, 5 DEVELOPMENT | two parallel code phases, each with a nested gate-runner | 4 (two implementers, two gate-runners) |
| Landings | 4 then 5 | land, one at a time, a gate-runner after each | 2 |
| Reviews | one per destination file | read the whole file | 2 |

Peak agent count: 4. Landing order: README with its images, then DEVELOPMENT, because the images land with the README and DEVELOPMENT links to the README. The controller dispatches each landing as `MODE: land`. Task 3 may lag Tasks 1 and 2; if it does, Task 4 waits and Task 5 may start once `facts.md` is reviewed.

## Gates

Docs only (owner ruling 2026-10-31, scoped gates): no unit shards and no frontend gate. Run from the worktree root:

- `pre-commit run --all-files` (expected: `ERROR WT003`, `WARNING WT010`; the hook still reports Passed).
- `python scripts/doc_state_sync.py --check` (expected: the root `BATCH23_DEFINITION.md` warning and the two `WARNING DOC024` lines on the findings archives).

The commit procedure is AGENTS.md "Commit Rules": a PLAYBOOK Section 3 bullet and a Section 4 entry (untagged, directly after the `<!-- DOCSYNC:CURRENT-BATCH-END -->` marker), then bare `--fix` with the count from the `[test_count]` pin and no pytest run, since the change is docs only.

## Review

Each writing task's review reads the WHOLE destination file, not only the diff (AGENTS.md Anti-Pattern Registry, item 12, "Lossy or contradictory consolidation"). It checks the file against the writing guidelines, `facts.md`, the Gate traps and the acceptance checks of its task, and runs the named greps itself.

## Definition of done

- Both files are rewritten, landed and gate-clean; every image referenced exists.
- No September changelog or roadmap remains in the README.
- The cache measurement is stated once, dated, in the README; `facts.md` holds the raw figures.
- DEVELOPMENT shows each tool with a real excerpt.
- The execution record is added to this plan as a last docs-only commit.
