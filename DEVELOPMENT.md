# ScrobbleScope: Development Methodology

ScrobbleScope was built by one developer working with several LLM coding
agents. An agent has no memory between sessions, and it cannot see what
another agent did. So nothing that matters is allowed to live only in a chat.
Decisions, state and rules live in tracked files. Scripts and hooks check
those files, because an agent cannot be trusted to keep them tidy by hand.

The pieces, in one sentence each:

- `AGENTS.md` holds the rules every agent follows.
- `docs/agents/PLAYBOOK.md` holds the work order and the execution log.
- `.claude/SESSION_CONTEXT.md` is the dashboard of current state.
- `scripts/doc_state_sync.py` rotates and checks those documents.
- `scripts/dev/check_worktree_alignment.py` checks the git worktree.
- `scripts/dev/frontend_gate.py` drives a real browser against the app.
- `scripts/dev/tailwind_build.py` builds the committed stylesheet.

This document explains why each piece exists and shows each tool running.
It is explanatory. `AGENTS.md` owns the operational rules, and nothing here
overrides them. One section is an exception: Frontend Asset Build owns the
build and watch commands, and other documents point to it. The owner plans to
lift this workflow out into a reusable template. That intent is recorded in
`docs/agents/AGENT_NOTES.md`, under "This repository is also a template being
extracted". The section "This Repository Is Also a Template Being Extracted"
below reports how far the work has gone.

In every "In action" block, the output was captured from a real run. Lines cut
for length are marked `...`. Counts and timings change from run to run, so
read them as examples.

---

## The Core Problem: Collaborating With Amnesiac Engineers

The prototype-to-deployed-app work happened mostly in a compressed
February-March sprint, with lighter follow-up work later. The project had been
abandoned once, after a thundering-herd bug and a large monolithic `app.py`.
Rate-limiter changes fixed the herd. The Batch 8 refactor replaced the
monolith with Flask Blueprints and an application factory. More coding agents
were then added, some inside VSCode and some outside it.

That created the central problem. An LLM has a finite context window and no
persistent memory. It cannot tell another agent what it did. Every session
starts from zero. A model that produced a clean refactor yesterday does not
know it did so today. A different model does not know either.

Left unmanaged, this produces four failures:

- **Drift**: two agents edit related files with different ideas of the
  current state.
- **Regression**: an agent redoes finished work, or undoes a deliberate
  decision, because no record says why the code looks as it does.
- **Token bloat**: one "catch-up" file grows until it fills the context window
  before any work starts.
- **Lost reasoning**: a review tool flags code as wrong because it cannot see
  why the code was written that way.

The orchestration system below exists to prevent these four failures.

---

## The Orchestration Architecture

The external-memory layer is a small set of tracked files, the read-on-demand
`docs/agents/FINDINGS.md`, and two archive directories. Each file has one
concern. The design goal is that every fact lives in exactly one place.

`docs/agents/HANDOFF_PROMPT.md` holds only what is unique to starting and
ending a session. It links to `AGENTS.md` for rules instead of summarising
them. Earlier versions summarised the rules in a cold-start checklist, and
every summary drifted from the text it summarised.

`README.md` is outside this memory layer. It is written for people and is not
used for orchestration.

### `AGENTS.md` -- Rules

`AGENTS.md` states the invariants every session must keep: commit format, test
quality, what counts as a side task and what counts as batch work, how to
start a session, and how to run pre-commit and doc sync. It holds no current
state and no history. It rarely changes.

Its language is deliberately strict ("Must", "Do not", "Forbidden"). An LLM
handles ambiguity poorly. A wrong inference can break the pipeline or scope a
commit wrongly.

### `docs/agents/HANDOFF_PROMPT.md` -- Session Start and Handoff

The owner gives this file to any agent that starts work, and passes it as
context when delegating to a new session. It holds two things that belong to
no other file:

- the check that repository reality matches what the bootstrap documents claim
  (branch, recent commits, test count);
- the checklist for handing work to the next session.

The read order, the validation gates and the commit rules once lived here too.
They now live only in `AGENTS.md`. Each copy had drifted from the original. In
one case a copy outlived the rule it described. So the copies became pointers.

### `docs/agents/AGENT_NOTES.md` -- Owner Context

This file records facts that belong nowhere else: the owner's workflow
preferences, the local dev setup (Docker, Postgres, Browser MCP), constraints
found during development, and known open issues. It is tracked in git, so
every agent on every machine reads the same preferences. For venv rules it
points to `AGENTS.md`.

### `docs/agents/PLAYBOOK.md` -- Work Orders

The PLAYBOOK is the source of truth for what work is in progress, what is
next, and what just finished. It has four sections:

- **Section 1**: why the document exists (agent onboarding, not history).
- **Section 2**: the ordered batch table. A finished batch keeps only a row
  and a `docs/history/` link.
- **Section 3**: the active batch state. It has enough detail for an agent to
  continue mid-batch without reading anything else.
- **Section 4**: a small window of dated execution-log entries. Older entries
  rotate into the archive.

Batches and work packages (WPs) work like a light sprint system. Each batch
starts with a definition document at the repository root
(`BATCHN_DEFINITION.md`). It states the acceptance criteria before work
begins. That prevents scope creep and gives a later agent an unambiguous
target. At close-out the definition moves to `docs/history/definitions/`.

Agents write the narrative log entry. `doc_state_sync.py` does the mechanical
work: rotation, deduplication and the status-block refresh. `AGENTS.md`
("Before writing to Section 4") owns what an agent must check before it
appends an entry. The next section explains why a script does the mechanical
part.

### `.claude/SESSION_CONTEXT.md` -- Dashboard

This file is a machine-managed snapshot: the current test count, the branch,
known risks, the module structure, the dependency graph and the architecture
overview. It is not a rules file and not a history file. A new session reads
this one file to learn the current runtime state, instead of parsing the
PLAYBOOK or running the tests.
`docs/history/reports/SESSION_CONTEXT_REFERENCE.md` holds a reference snapshot
of its format.

The file lives in `.claude/` and is committed. A `.gitignore` exception makes
that work: `.claude/*` plus `!.claude/SESSION_CONTEXT.md`. It is committed
because every agent must start from the same state. When it was uncommitted,
agents started with a stale branch, test count and batch status.

CI does not depend on it. If the file is absent, `doc_state_sync.py` skips the
SESSION_CONTEXT steps through `_read_lines_optional()`. The rest still runs.
That covers a sparse checkout or a custom workflow. See commit `05c7b19` on
`main` for the original change.

The `DOCSYNC:STATUS` block inside the file is a derived view. `--fix` rebuilds
it from the PLAYBOOK. Forgetting to update it by hand therefore corrects
itself.

### `docs/history/` -- The Archive

The archive holds finished batch definitions, per-batch logs, audits and old
changelogs. A finished batch's definition moves here. PLAYBOOK Section 4
entries rotate here when the window overflows. Nothing is deleted. Agents can
grep past decisions without loading them into the active context.

Its subdirectories:

- `docs/history/definitions/`: archived batch definitions.
- `docs/history/logs/`: per-batch execution logs rotated from Section 4.
- `docs/history/findings/`: resolved findings rotated out of
  `docs/agents/FINDINGS.md`.
- `docs/history/reports/`: dated one-off documents (audits, changelogs,
  refactor plans, the worker ADR, the SESSION_CONTEXT snapshot). These are
  point-in-time records. They are not revised after later reorganisations, so
  paths inside them may name a layout from before 2026-08-14.
- `docs/logarchive/`: the tool-managed archive for side-task entries that
  belong to no batch.

A tool or a documented procedure writes into every subdirectory except
`reports/`. `docs/history/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` stays at the top
level on purpose. It is a tombstone that resolves references to the legacy
path.

---

## `doc_state_sync.py`: Why a Script, Not a Prompt

You cannot ask an LLM to rotate 50-line Markdown sections between files
without eventually getting corruption, duplicate entries or broken markers.
This is the least obvious part of the infrastructure, so it gets the most
space here.

The problem appeared early. As PLAYBOOK Section 4 grew, agents trimmed it
differently each session. Some removed entries that should have been
archived. Some duplicated entries. Some moved entries across the
`<!-- DOCSYNC -->` boundary markers and broke the rotation policy. Some
deleted the markers. Rotation by hand was tried three times, and each try
failed differently: an entry archived that should have stayed, an entry
duplicated across the boundary, and a stale remark left behind after the text
it described had moved. All three failures are silent. The document still
renders, so nothing tells the reader it is now wrong.

The fix was to stop asking for care and build a mechanism: a parser that reads
the section into typed entries, a renderer that writes the result, and a
rotation step that decides what moves. The hooks and diagnostics came later,
once there was a mechanism worth guarding.

### What the script does

1. **Parses** Section 4 of the PLAYBOOK into typed entries. Each has a date, a
   title, its lines and a SHA-256 fingerprint.
2. **Splits** the entries into current-batch (inside the DOCSYNC markers) and
   non-current (outside them).
3. **Enforces the keep limit.** Non-current entries beyond the limit move to
   the archive. Nothing is deleted.
4. **Deduplicates** the archive by fingerprint. The same entry cannot appear
   twice, even if an agent copied it by hand.
5. **Rebuilds** the `<!-- DOCSYNC:STATUS-START/END -->` block in
   `SESSION_CONTEXT.md` from PLAYBOOK truth. `AGENTS.md` ("Integrity
   diagnostics") owns the rule for which count wins when counts disagree.
6. **Checks live-document integrity.** Dead references, active-definition
   metadata, archive prologue drift and session contradictions each produce a
   stable, blocking diagnostic. `--fix` writes only deterministic output, then
   revalidates the result. It never guesses at a semantic repair.

The script runs as the `doc-state-sync-check` pre-commit hook in `--check`
mode. The hook goes through `scripts/dev/docsync_preflight.py --worktree`. A
commit that leaves drift, or a proven contradiction between live documents, is
refused before it reaches CI.

### In action: `--check` on a clean tree

```text
$ python scripts/doc_state_sync.py --check
WARNING DOC024 docs/history/logs/BATCH22_LOG.md -- An archive under its page target of 500 lines stays a single file; ...
Remediation: docs/history/logs/BATCH22_LOG.md has grown past the 500-line page target. Run `python scripts/doc_state_sync.py --paginate-archives` to split it into indexed, numbered pages. This warning writes nothing on its own.
...
WARNING: Root BATCH file detected: BATCH23_DEFINITION.md should be archived under docs/history/definitions/.
doc_state_sync check passed (current_batch_entries=0, kept_non_current=4, rotated=0).
```

The command exits 0. A warning never blocks a commit.

- `WARNING DOC024` says an archive has grown past its page target. Each
  warning is followed by its own `Remediation:` line. The tool only reports
  it. Splitting the archive is a separate operator command
  (`--paginate-archives`), described in
  `docs/architecture/documentation-tooling.md` under "CLI surface added by
  the close-out and bounded-archives plan". An ordinary commit does not run
  it. Per `AGENTS.md` ("Doc Sync Rules"), warnings print without changing
  the exit code.
- `WARNING: Root BATCH file detected` appears while a batch is active. Its
  definition sits at the repository root until close-out archives it. It
  needs no action mid-batch.
- The last line is the verdict. The numbers in it describe what the check
  saw. Only the word `passed` and the exit code matter.

### In action: a planted defect

To see a failure, this run copied the tree to a scratch directory, ran
`git init` there, and changed one declared value. `config/docsync.toml`
declares that the light page background is `#faf7f0` in several files. The
edit changed one copy in `static/css/shell.css` to `#faf7f1`.

```text
$ python scripts/doc_state_sync.py --check
...
ERROR DOC009 static/css/shell.css:15 -- static/css/shell.css states 'the shared light page and navbar background' as #faf7f1 here and the declaration expects #faf7f0.
Remediation: Every occurrence in this file must read the same. Change it, or change the declaration if the value itself has moved.
...
```

The command exits 1, and the pre-commit hook would refuse the commit.

- `ERROR DOC009` is the code. The catalogue in
  `docs/architecture/documentation-tooling.md` explains every code.
- `static/css/shell.css:15` is the file and line that disagree.
- The message names the fact, the value found and the value expected.
- `Remediation:` says what to do. Here you either put the value back, or, if
  the value really changed, change the declaration in `config/docsync.toml`
  in the same commit.

The scratch copy was deleted afterwards.

### In action: `--fix --test-count N`

`AGENTS.md` ("Procedure before every commit") requires the suite to run first.
The measured count then goes to the script. Never hand-edit the count. N is
the number the `pytest -q` run just printed.

```text
$ python scripts/doc_state_sync.py --fix --test-count N
...
doc_state_sync wrote updates:
- .claude\SESSION_CONTEXT.md
- config\docsync.toml
- docs\agents\FINDINGS.md
doc_state_sync summary (current_batch_entries=0, kept_non_current=4, rotated=0).
```

One command wrote the number in five places across three files. The diff, in
short:

```text
.claude/SESSION_CONTEXT.md   Tests row: "**<N> passing** across ... tracked test modules"
.claude/SESSION_CONTEXT.md   STATUS block: "Latest validated test count: **<N> passed**."
.claude/SESSION_CONTEXT.md   Section 6 heading: "Test structure (<N> tests)"
config/docsync.toml          [test_count] pinned = <N>
docs/agents/FINDINGS.md      header: "<N> tests across ... tracked test modules"
```

The tool lists every file it wrote. Stage those files with the commit. If the
Section 4 window was over its limit, `--fix` also rotates the oldest entry
into the archive, and that file appears in the list too. The `<N>` above stands for
the count your own `pytest -q` run printed; it is elided here on purpose.

### In action: the commit preflight refuses a control-plane change

The checker cannot fairly judge a commit that also changes the checker. The
preflight refuses that case. This run staged a one-character change to
`scripts/docsync/models.py` in the scratch copy:

```text
$ git add scripts/docsync/models.py
$ python scripts/dev/docsync_preflight.py --worktree
ERROR docsync control-plane code is staged in this commit: scripts/docsync/models.py
Refusing to run the checker against a candidate corpus while the checker's own logic is part of the same commit -- see 'Commit preflight' in docs/superpowers/specs/2026-09-15-docsync-closeout-archives-design.md. The only supported local escape is 'SKIP=doc-state-sync-check git commit', ...
```

The command exits 3. When you mean to change `scripts/docsync/`, run
`doc_state_sync.py --check` yourself and confirm it exits 0. Then commit with
`SKIP=doc-state-sync-check git commit`. That skips only this hook. Every other
hook still runs. `--no-verify` is never allowed. The message says CI's
preflight is the backstop for control-plane changes.

With nothing from the control plane staged, the preflight runs the same check
as `--check` and prints the same output.

### The package

The script began as one 600-line file. Batch 14 split it into the package
`scripts/docsync/`. The root `scripts/doc_state_sync.py` is now a thin
wrapper. Batch 22 added the modules for declared-value checks, close-out
signals, bounded archives, finding lifecycle, crash-safe publication and a
shared fenced-block scanner. The module map, the DOC diagnostic catalogue and
the preflight and hook-installer design are owned by
`docs/architecture/documentation-tooling.md`. This document does not repeat
them. Run `pytest tests/test_docsync_*.py -q` for the current test count.

### Publication is crash-safe

Reading Section 4 and writing it back changes several files that must agree.
A half-finished write would leave the corpus in a state no later agent could
reason about. So every mutating mode (`--fix`, `--close-batch`,
`--split-archive`, `--paginate-archives`, `--cold-storage`) publishes through
`scripts/docsync/transaction.py`:

1. An exclusive lock (`.docsync.lock`) makes the run single-writer.
2. The run proves every file it read is still byte-identical. A concurrent
   edit becomes a refusal, not a silent overwrite.
3. The before-image of every path is journalled (`.docsync.journal`) before
   the first write.
4. Each write goes to a same-directory staging file (`.docsync-stage`) and
   lands through `os.replace`, which is atomic on one filesystem.
5. A run killed between two writes leaves the journal behind. The next
   publication replays it, or refuses if a journalled file matches neither the
   before-image nor the interrupted content. It never guesses.

The guarantee is narrow. A crash can lose the whole run. It cannot leave a
half-published corpus.

"ACID" is shorthand here, not a claim:

- **Atomicity** is real. A publication commits or does not.
- **Consistency** is real. A declarative rules engine enforces the invariants.
- **Isolation** is partial. The lock is scoped to the filesystem, not a
  database. It does not coordinate across machines and does not block readers.
- **Durability** holds within filesystem limits. The journal survives the
  process, but there is no fsync per write, so power loss can still lose data.

The accurate description is an atomic file-transaction and invariant-checking
system. Read the acronym as design intent, not as a database guarantee.

### Archives are bounded

`archives.py` caps an archive page at 500 lines by default. An archive that
outgrows the cap splits into numbered, immutable pages with a flattened index,
so every page stays searchable Markdown. Page `0001` holds the oldest content.
Version 1 numbered pages the other way round and put the newest entries on the
oldest page. Commit `4b36d6a` fixed that.

Cold migration never reads the system clock. It runs only under an explicit
`--cold-storage --as-of <ISO date>`. A check that aged files by today's date
would give the same commit different results on different days.

### Two more parts of the workflow

- **The commit preflight** (`scripts/dev/docsync_preflight.py`) validates the
  commit candidate, not the working tree. It is the first hook in
  `.pre-commit-config.yaml`, so no later hook can rewrite files it has
  already validated.
- **The hook installer** (`scripts/dev/install_docsync_hook.py`) is opt-in and
  not installed in this repository. pre-commit's own dispatch cannot make
  docsync run before every other hook. The installer writes a wrapper that
  does, and it refuses to overwrite a hook it did not write. Running it for
  real is an owner action.

---

## Worktrees, Rebase Merges, and Branch Lineage

ScrobbleScope uses linked git worktrees, so a long batch stays isolated from
the owner's main checkout. A linked worktree has its own branch and working
directory. It shares the object store with the primary checkout. Updating
`main` does not move the batch branch.

### Why the guard exists

After a GitHub rebase merge, `main` holds the source commits under new
identities, while the source branch still points at the old ones. Git then
reports the branch as both ahead and behind, even when its tree is identical to
`main`. This happened after PRs #163, #165 and #168. On two of those cycles the
stale branch caused a phantom or reverse-direction follow-up PR.

The guard compares two things: commit ancestry and tree identity. A clean
divergence with identical trees is normally a rebase-merge artifact. A
divergence with different trees is real work and must not get the same reset
remedy. Realignment is never automatic, because a reset and force-push rewrite
history and need the owner's approval.

### Where the virtualenv lives

The repository has one `.venv`. It normally lives in the primary checkout and
is not copied into linked worktrees. A fresh shell in a worktree cannot rely on
bare `pytest` or a relative `.venv` path. So `AGENTS.md` sends those commands to
the qualified executable in the primary checkout. A second environment inside
the worktree would bring back the package-version drift that policy prevents.

That leaves a bootstrap gap. The guard must run before the primary checkout's
paths are known. So `AGENTS.md` permits system Python for that first launch
only, and the guard uses the standard library alone. The paths the guard
reports then name the environment for every later Python, pytest and
pre-commit command. `AGENTS.md` owns the procedure. This section only explains
the design.

### In action: `check_worktree_alignment.py`

The guard is read-only. It never switches branches or creates an environment.
`--base-ref` names the local ref to compare against. These runs used a scratch
repository with `main` as the base.

On the branch the active batch names:

```text
$ python scripts/dev/check_worktree_alignment.py --base-ref main
INFO WT000 feat/batch23-wp0-hygiene -- branch is 0 behind and 0 ahead of main; checkout kind: primary checkout; Python: ...\.venv\Scripts\python.exe; pytest: ...\.venv\Scripts\pytest.exe; pre-commit: ...\.venv\Scripts\pre-commit.exe.
```

The command exits 0. `WT000` means all clear. It reports the branch, how far
it is from the base, and the exact Python, pytest and pre-commit paths to use
for the rest of the session. Copy those paths.

On any other branch:

```text
$ python scripts/dev/check_worktree_alignment.py --base-ref main
ERROR WT003 fix/demo -- active Batch 23 requires branch feat/batch23-wp0-hygiene.
Remediation: Stop and move the work to the named branch only with the owner's direction; this guard does not switch branches.
```

The command exits 1. `WT003` says the current branch is not the one the active
batch names. The `Remediation:` line says stop and ask the owner. Do not
switch branches on your own. Every `WT` code names its own remediation the
same way.

The guard runs as an advisory pre-commit hook, not a gate. On a feature branch
a gate would refuse every commit. `WT003` fires for any branch the active batch
does not name, and `WT004` fires for the identical-tree divergence that every
rebase merge leaves. A stacked review-fix branch therefore prints `WT003`, and
the hook still reports Passed.

### How it splits from docsync

Two safeguards cover two different failures. Drift inside live operational
documents is a blocking check in `doc_state_sync.py`, which runs locally and in
CI. The read-only worktree guard covers local bootstrap and post-rebase
checks. It is not a CI topology gate. On a detached, recognised CI checkout it
reports an explicit skip. The test workflow exercises the guard's state
decisions instead.

The design is in
`docs/superpowers/specs/2026-08-05-repository-integrity-worktree-alignment-design.md`.
`scripts/dev/check_worktree_alignment.py` is the entry point. The checks live
in `scripts/dev/_worktree_guard_*.py` behind the `scripts/dev/worktree_guard.py`
facade. `docs/architecture/documentation-tooling.md` owns the module map.

---

## Frontend Asset Build

Batch 21 moved the interface to the Tailwind CSS standalone CLI and daisyUI
bundles, with no Node project. That migration is complete. The source of truth
is `static/css/tailwind.src.css`. Production serves the committed
`static/css/tailwind.css`, so app startup never downloads or compiles frontend
tooling.

Run a one-shot build before committing any source or template change:

```bash
python scripts/dev/tailwind_build.py
```

Watch during local UI work:

```bash
python scripts/dev/tailwind_build.py --watch
```

The script picks the pinned executable for the host. It stores that file, with
`daisyui.mjs` and `daisyui-theme.mjs`, under the gitignored `scripts/bin/`. On
every run it checks all three files against their pinned SHA-256 values. It
fetches a missing or invalid file once and verifies it before an atomic
replacement. An invalid replacement stops the build.

These commands are written for the primary checkout. In a linked worktree, use
the qualified Python path printed by `scripts/dev/check_worktree_alignment.py`,
as `AGENTS.md` requires. Stop watch mode before the one-shot build. Commit both
the source and the generated CSS. CI runs the same one-shot path on Linux and
rejects generated-file drift.

### In action: `--check`

`--check` rebuilds the stylesheet, then fails if the result differs from the
committed file. Run it before you push.

When the committed CSS matches its source:

```text
$ python scripts/dev/tailwind_build.py --check
...
Done in 239ms
[tailwind_build] building static\css\tailwind.css
```

The command exits 0 and prints only Tailwind's own build log. Nothing needs
committing.

To see drift, this run changed one colour in `static/css/tailwind.src.css` and
did not rebuild:

```text
$ python scripts/dev/tailwind_build.py --check
...
-    --color-base-100: #faf7f0;
+    --color-base-100: #faf7f1;
...
[tailwind_build] ERROR: committed CSS drift. static\css\tailwind.css does not match a rebuild from its source. Commit the rebuilt file.
```

The command exits 1. The `-` line is what the committed CSS says. The `+` line
is what the source now produces. The `ERROR` line gives the fix: run
`python scripts/dev/tailwind_build.py` without `--check`, and commit the
rebuilt `static/css/tailwind.css` with your source change. Editing the
generated CSS by hand does not help, because the check rebuilds it from the
source.

---

## Frontend Browser Gate

Three test entry points drive a real Chromium. They test different things.

**`scripts/dev/results_behavior_tests.py`** runs isolated Chromium tests
against the production Results scripts. It uses a controlled clock and no
Flask server or external service. The tests cover Spotlight rotation, the
card staying hidden until every hydration settles, and the card dropping any
candidate without a confirmed photo. They also cover reduced motion,
leaderboard state, tooltip timing and keyboard access. A rotation swap must
keep the visible photo and name together. Two cases guard against a card stuck
hidden forever: a stalled hydrate request is dropped once its own timeout
passes, and a confirmed candidate whose photo hangs past the same budget is
dropped the same way. These tests run in CI after the browser install and
before the full-page gate. They are separate from the Python `pytest` count.
Sampling itself lives in `scrobblescope/spotlight.py`, and the Results route
regression in `tests/test_routes.py` covers it.

**`tests/frontend/`** is collected by `pytest`. It tests pure functions, not a
served page. Its cases carry the `browser` marker registered in
`pyproject.toml`. A local `pytest -q` runs them with everything else, so a
local run needs the same Playwright Chromium build as the gate. CI's coverage
step runs `pytest -m "not browser"` instead. It runs the marked tests in the
"Run frontend gate" job step, after installing both browsers. See
`.github/workflows/test.yml` for the exact invocations. Advisory `pip-audit`
scans both `requirements.txt` and `requirements-dev.txt`.

**`scripts/dev/frontend_gate.py`** is the full-page gate. Install the browsers
once, after the pinned development requirements:

```bash
python -m playwright install chromium firefox
python scripts/dev/frontend_gate.py
```

In a linked worktree, use the qualified primary-checkout Python path. The gate
starts and stops its own loopback Flask server. Chromium runs the complete
matrix. Firefox runs the static-assets and theme-token canary. UI changes also
get focused Firefox checks and owner visual review. `--headed` shows the
diagnostic browser windows.

### What makes it a gate rather than a screenshot run

Each of these closes a way a visual check can pass while the page is wrong:

- **It serves the real application on a port it owns.** The gate binds
  `127.0.0.1` on port `0`, so the OS picks a free port. It shuts the server
  down in a `finally` block. No separate app needs to run, and two concurrent
  runs cannot collide on a fixed port.
- **It asserts computed values, not class names.** A probe that reads a
  `className` passes against a stylesheet that was never applied. The checks
  read `getComputedStyle` and real geometry instead. The colour maths lives in
  `_frontend_gate_colour.py` as pure functions with no page attached: WCAG
  relative luminance and alpha-composited contrast. A translucent divider
  token must clear 3:1 against every surface it can sit on, not only the one
  it was sampled over.
- **It measures the interface at the sizes readers use.** The viewport
  profiles cover mobile, 1080p, 1440p and 4K, plus a wide screen with a coarse
  pointer. Width does not imply a mouse: a landscape tablet and a touch laptop
  are both wide and both touched. Touch targets on coarse-pointer profiles
  must measure at least 44px on their smaller side. Desktop composition must
  reach its proportions through layout, not through a CSS `zoom` or
  `transform`. A `zoom` would satisfy a pixel check and break the type scale.

Stylesheet isolation is asserted per page. Each page must load exactly one
framework stylesheet, because daisyUI, Tailwind v4 and a legacy Bootstrap file
all claim `.btn`, `.card` and `.modal`. If two loaded, one would silently win.
`docs/agents/ui-accessibility.md` owns the unit, touch-target, motion and
keyboard rules the checks enforce.

Four checks show what each closes:

- `check_theme_reattaches_to_system`: a toggle choice that matches the OS
  preference clears the stored key, so the pre-paint script can derive the
  theme again.
- `check_heatmap_cells_are_keyboard_accessible`: a real Tab press reaches a
  heatmap cell whose `aria-label` and focus ring are real.
- `check_inline_marks_need_no_wrapper_list`: the inline mark SVGs colour
  themselves through `currentColor` and a CSS custom property, so no wrapper
  has to list them.
- The artist-spotlight photo checks in `_frontend_gate_spotlight_photo.py`:
  no crop, no overlay, no animation, a non-square photo shown whole through
  `object-fit: contain`, and the card hidden when there is no real photo.
  A layout check from 320px to 1920px (and after a resize) requires that no
  artist name breaks inside a word and that the card is one height for every
  candidate. A hold check focuses the Spotify link, then hovers the card,
  and requires that the link keeps its focus, target and name across three
  rotation periods.

`_frontend_gate_spotify_icon.py` adds the official Spotify icon check: the file
each theme shows, at least 21px, half its height of clear space, and the
spotlight link's target. The results attribution check reuses it and also
requires the icon in the "Save image" JPEG.

### In action: a passing run

```text
$ python scripts/dev/frontend_gate.py
2026-09-29 18:05:04,736 [MainThread] [INFO] ScrobbleScope starting up, debug mode: True
[frontend_gate] <N> of <N> checks selected; disabled: none
...
[frontend_gate] <N> checks passed in <M> runs across chromium, firefox (static assets & tokens canary on firefox); profiles: desktop, mobile, wide touch
```

The command exits 0 (counts elided: `config/frontend_gate_checks.toml` owns
the manifest). This run took about two minutes. Log lines from the Flask
server fill the middle. Ignore them. Two lines matter:

- `checks selected` shows how many checks `config/frontend_gate_checks.toml`
  enabled. A manifest that names an unknown check, or disables a required one,
  is refused here, before any browser launches.
- The last line is the summary. A run is one check on one browser and one
  profile. Only the words `checks passed` and the exit code matter.

### In action: a failing run

To see a failure, this run changed the light page background in the committed
`static/css/tailwind.css` to the dark ink colour, then ran the gate:

```text
$ python scripts/dev/frontend_gate.py
[frontend_gate] <N> of <N> checks selected; disabled: none
...
[frontend_gate] FAIL chromium: divider contrast [desktop]: / index divider light: --ss-border-divider composites to 1.00:1 against its adjacent surface, expected at least 3:1
[frontend_gate] FAIL chromium: release check disclosure [desktop]: corrected row's note contrasts at 1.44:1, below the 4.5:1 body-text floor
[frontend_gate] FAIL firefox: divider contrast [desktop]: / index divider light: --ss-border-divider composites to 1.00:1 against its adjacent surface, expected at least 3:1
```

The command exits 1. Each `FAIL` line names the browser, the check, the
profile in brackets, and the measured value against the limit. One cause can
fail several checks, and the same check can fail on both browsers. Read the
measured value first. A divider that composites to 1.00:1 has the same colour
as the surface under it. Fix the value in the source CSS, rebuild with
`tailwind_build.py`, and run the gate again. Only `FAIL` lines and the exit
code report the result. Other server log lines, such as `Failed to fetch
Spotify token`, are not check results.

---

## This Repository Is Also a Template Being Extracted

**Owner intent, stated 2026-08-25.** The long-term goal is to lift this
workflow out of ScrobbleScope and reuse it when building any application, at
least any data-visualisation or full-stack one. That is why the tooling is
larger than the application it checks. It is also why the hardening has been
progressive instead of one-off. The docsync package, the worktree guard, the
frontend gate, `AGENTS.md`, the PLAYBOOK and FINDINGS discipline, and the batch
and work-package structure are all meant to leave with the template.
`docs/agents/AGENT_NOTES.md` owns the owner intent and the reasoning behind the
constraint. If this section and that one disagree, AGENT_NOTES wins.

The repository holds three separable systems at different levels of maturity.

**1. The documentation control plane (`scripts/docsync/`).** This is the most
portable and the closest to finished. Its integrity checks are generic, apart
from the document names in `LIVE_DOCUMENT_RELATIVE_PATHS`. Its facts live in
`config/docsync.toml`, not in the code. `declarations.py` carries no
ScrobbleScope value at all. It publishes atomically, reports typed codes with a
remediation, and runs from a pre-commit hook and from CI.

**2. The worktree guard (`scripts/dev/_worktree_guard_*.py`).** It is
structurally complete: a public facade (`worktree_guard.py`), a thin CLI entry
point, and checks split by concern across sibling modules. Each `WT` code names
its own remediation. It runs as an advisory hook, not a gate, for the reason
given in the worktree section above.

**3. The frontend gate (`scripts/dev/frontend_gate.py`).** Its structure is
generic: serve the app, drive a browser, run checks per device profile. Its
checks are specific, and they stay behind. That split is right. The
decomposition (F-B21-51) has landed. The facade stays under the decomposition
plan's 700-line threshold
(`docs/superpowers/plans/2026-09-21-frontend-gate-decomposition.md`). The
checks are grouped by concern across `_frontend_gate_*` sibling modules. One
holds pure colour maths (`_frontend_gate_colour`). One holds shared state, such
as the page inventories several slices read (`_frontend_gate_shared`). The
manifest F-B21-51 proposed has also landed (foundation plan Task 8):
`config/frontend_gate_checks.toml` selects which `CHECKS` run, by name.

Two things are not portable and should not try to be: the design system under
`docs/design/`, and every path constant that names a ScrobbleScope file.

### `config/docsync.toml` shows how far extraction has gone

The file exists as a separate declaration layer so a second repository can
supply its own without touching the mechanism. The checks read what to verify
from it. That split works. What remains tied is the content of the
declarations:

| Tie | Where | Why it is repository-specific |
|---|---|---|
| Document paths | `[[value.sites]]` and `[[anchor]]` entries | They name `docs/design/README.md`, `docs/design/RECONCILIATION.md`, `docs/history/definitions/BATCH21_DEFINITION.md`, `docs/architecture/documentation-tooling.md`, `docs/agents/ui-accessibility.md` |
| Scanned corpus | `scan = ["*.md", "docs/**/*.md", ".claude/SESSION_CONTEXT.md"]` and its `allow_files` list | The document inventory a repository has is a policy choice, not a universal |
| Section anchors | `[retired.allow_after] "docs/agents/PLAYBOOK.md" = "## 4. Execution log (for agent handoff)"` | PLAYBOOK and its section names are this workflow's vocabulary |
| Batch vocabulary | `[closeout] admit_from_batch = 22` | Batching is the portable idea; *which* batch is the local fact |
| Design tokens | the `[[value]]` entries for the page background and muted text | These are ScrobbleScope's visual system, and one of them straddles source CSS, a legacy shell bridge and exact tests |
| Live-document list | `LIVE_DOCUMENT_RELATIVE_PATHS` in `integrity.py` | The module's own remaining repository knowledge; the short list AGENT_NOTES names as the last thing to move |

The pattern is consistent. The mechanism is generic and the facts are local.
That is the intended end state. The unfinished half is that those local facts
still live inside this repository's config, not in a config a second
repository would write for itself. The deferred kernel plan addresses that. Its
constraint is that the new kernel modules "must not contain `ScrobbleScope`,
`docs/agents/PLAYBOOK.md`, `Batch`, `WP`, or `docs/superpowers/` policy
literals".

### Why it is deliberately unfinished

There are two reasons, and both are engineering reasons.

First, some of it cannot be extracted without loss. `config/docsync.toml`, the
design system and the path constants encode this repository's own rules. A
control plane must know which documents its repository owns. Forcing
genericity before a second consumer exists adds configuration indirection with
nothing to justify it.

Second, the modules still worth simplifying are `integrity.py`,
`declarations.py` and `cli.py`, the largest in the package. Restructuring them
while the Batch 22 checks were still settling would trade a working control
plane for a tidier unfinished one. The plan says so: "Refactor by
responsibility, not line count."

### The standing constraint

The extraction is a batch of its own. It has not been scheduled. Do not start
it as a side task. Until it is scheduled, one rule binds every commit: write
new tooling so the extraction stays cheap.

- Keep repository facts in the declarations file, not in the mechanism.
- Name an assumption and make it switchable. Do not let it harden into
  doctrine.
- Prefer the standard library, so the next repository does not have to accept
  a new dependency.
- Fail with a path, a line and a remediation. The reader will not be the person
  who wrote the check.

The two extraction plans are
`docs/superpowers/plans/2026-09-12-repository-agnostic-plan-spec-guards.md`
(the docsync kernel) and
`docs/superpowers/plans/2026-09-12-reusable-frontend-ci-verification-components.md`
(the gate components). Both carry explicit "do not execute until" conditions.
Neither is current work.

---

## Claude Code Skills (tightly scoped tooling)

Two project-scoped Claude Code (CC) skills give structured entry points for
common tasks. They are CC-specific. The portable, model-agnostic rules live in
`AGENTS.md`. The skill definitions are kept locally and are not tracked here,
because `.gitignore` excludes `.claude/` except `SESSION_CONTEXT.md`. This
section documents their purpose.

**`scrobblescope-bootstrap`** runs the canonical session bootstrap in a fixed
read order:

1. `AGENTS.md`;
2. `docs/agents/PLAYBOOK.md` Sections 3-4;
3. the active batch definition named there;
4. `.claude/SESSION_CONTEXT.md` Sections 1-2;
5. `docs/agents/AGENT_NOTES.md`.

It ends with a git-state and test-baseline check against what those files
claim. If PLAYBOOK Section 3 and SESSION_CONTEXT Section 1 agree on the current
batch and next work package, the agent can start. Invoke it at the start of any
substantive session: new feature work, refactors, or multi-WP batch work. Skip
it when the change is too small to need batch context. The skill's own
anti-example is "tweak the heatmap pill padding". That change needs only the
relevant template file.

**`pr-bot-triage`** prioritises a batch of incoming PR review comments before
anyone acts on them. It sorts each comment into one of three classes:

- **Act**: actionable and in scope, so address it now.
- **Defer**: valid but out of scope for this session or batch.
- **Decline**: not warranted because it is incorrect, already addressed, or
  rejected by the PR author.

The classification standard lives in the skill definition. That keeps CC
workflow detail out of `AGENTS.md`.

Both skills are scoped to one agent at a time. They are not designed for
parallel sub-agents.

---

## The Batch Structure as a Lightweight SDLC

Batches and work packages work as a light delivery model. They map onto
familiar software-process concepts:

| SDLC concept | ScrobbleScope equivalent |
|---|---|
| Sprint / milestone | Batch (e.g., Batch 7: Persistent metadata layer) |
| Definition of done | `docs/history/definitions/BATCHN_DEFINITION.md` acceptance criteria |
| Stand-up / status | SESSION_CONTEXT Section 1 (current state table) |
| CI gate | GitHub Actions Quality Gate |
| Code review | PR review plus automated review feedback |
| Release | `flyctl deploy` (manual, after PR merge to `main`) |

The key difference from a human team is that the team members have amnesia
between sessions and cannot talk to one another. That forced unusually strict
documentation discipline. The reason is not that documentation is a virtue. An
undocumented decision lets a later session reopen a solved problem, or
refactor a prior agent's working code.

---

## How This Differs From Typical Agentic Coding / AIDD

Most AI-driven-development (AIDD) workflows treat the agent's context window,
or one running conversation, as the whole memory of the project. A prompt like
"continue where you left off" or "here is the chat history" works inside one
session. It does not survive a tool switch (Claude Code to Copilot to Gemini
CLI), a context compaction, or a gap of days or weeks. This project runs under
all of those conditions, with five or more agent tools.

The usual failure is that state lives in conversation history. Whoever holds
the longest, most recent transcript "knows" the project. Everyone else must
read that transcript in full, which is expensive and lossy, or start over.

ScrobbleScope inverts that. State never lives only in a conversation. It sits
in a small set of files, each with one concern: `AGENTS.md`,
`docs/agents/HANDOFF_PROMPT.md`, `docs/agents/AGENT_NOTES.md`,
`docs/agents/PLAYBOOK.md`, `.claude/SESSION_CONTEXT.md` and the `docs/history/`
archive. Any agent, from any vendor and with any context length, can rebuild
full working context from that short reading list instead of digging through
transcripts. Four practices follow:

- **Deterministic tooling for the parts that must never fail.** Section
  rotation, archive deduplication and cross-file consistency checks belong to
  `doc_state_sync.py`, a plain Python script with its own test suite. Typical
  AIDD setups ask the agent to remember the bookkeeping every session. Here the
  `doc-state-sync-check` pre-commit hook enforces it. A proven live-document
  defect is a blocking error. An expected active-root notice stays a warning.
- **A definition of done written before work starts.** Each batch's root
  `BATCHN_DEFINITION.md` is committed before its WPs begin. It moves to
  `docs/history/definitions/` at close-out. An agent resuming mid-batch, or a
  human auditing it later, has an unambiguous target and does not have to
  reconstruct intent from commit messages.
- **Review suggestions are logged and judged, not auto-applied.** "On
  Rejecting Code Review Suggestions" below follows from this. A review tool
  that sees only the current diff will sometimes recommend reverting a
  deliberate fix. Keeping the reasoning in `docs/agents/PLAYBOOK.md` and
  `docs/history/` stops the next agent or reviewer repeating the wrong
  suggestion. A conversation-only workflow cannot do that.
- **The documentation cost is paid up front.** A typical single-agent loop
  ships the change and treats documentation as optional follow-up. Here, work
  passes between independent sessions with no shared memory. Skipping the
  doc update is not a shortcut. It makes the next session redo or undo the
  work.

---

## On Rejecting Code Review Suggestions

Not every review suggestion improves the codebase.

**Pattern 1: Correct in isolation, wrong in context.** An automated review
(Gemini Code Review, Batch 12 post-audit) flagged the `getComputedStyle` call
in `results.js` as possibly redundant. In isolation that is a fair point. In
context, the call patches a dark-mode rendering issue in the `html2canvas`
JPEG export. Without it, the exported image gets the wrong background colour
in dark mode. The reviewer could not see the git history of that bug, the
session logs where the fix was built, or the test that validates it. The
suggestion was rejected with a documented reason in the session log. The code
stayed as it was.

**Pattern 2: Review tool versus review context.** Automated tools review code
as a snapshot. They do not know:

- which bugs were fixed on purpose with what looks like a workaround;
- which "magic numbers" are environment-specific constants that cannot be
  parameterised without breaking the Fly.io deploy pipeline;
- which test patterns look vacuous but guard against a specific production
  failure.

The response to all of these was the same. Log the suggestion. Judge it
against the causal knowledge in the session history. Then act on it, or reject
it with the reasoning kept in PLAYBOOK Section 4 or `docs/history/`. That
keeps the audit trail honest without accepting every automated suggestion.

---

## What Did Not Work Initially

Four things failed before the current approach settled:

- **A single long context file.** Early sessions used one `STATUS.md` that grew
  to about 400 lines. By mid-session it used most of the context budget and
  left little room for code. Splitting it into the PLAYBOOK (detailed),
  SESSION_CONTEXT (summary) and the archive (historical) fixed that.
- **Unpinned agent instructions.** Without `AGENTS.md`, agents sometimes
  committed without running tests, used the wrong commit format, or wrote
  "Added X" instead of "Add X". Strict rules in `AGENTS.md` made these
  failures reproducible, and then preventable.
- **Manual archive management.** Before `doc_state_sync.py`, agents trimmed
  Section 4 by hand. That produced duplicate content and entries moved across
  the DOCSYNC boundary. The pre-commit hook now catches this class of error
  before it lands.
- **The nested thread pattern (Batch 3).** The original background task
  started a thread that started another thread to run the asyncio event loop.
  Behaviour under load was unpredictable. Batch 3 removed it.

---

## How to Read the Orchestration Files

To understand any decision in this repository:

1. Read the relevant `docs/history/definitions/BATCHN_DEFINITION.md`. It shows
   the acceptance criteria from before the work started.
2. Search `docs/agents/PLAYBOOK.md` Section 4 and
   `docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md` for dated entries in the
   relevant date range.
3. Search `docs/history/logs/` and `docs/logarchive/` for older entries.
4. Read `AGENTS.md` for how a session should start and which rules govern
   commits, tests and documentation.

`.claude/SESSION_CONTEXT.md` is the current-state snapshot for an active
session. It is committed and shared across all agents. A reference copy of its
format is at `docs/history/reports/SESSION_CONTEXT_REFERENCE.md`.

Bootstrapping an agent with the template prompt and the repository documents
gives each session the current state and the next task. Batch definitions and
WPs supply the orientation. The method costs tokens. It has proven effective as
a cross-session, cross-agent external memory. Logging decisions, deviations
and implementations preserves the reasons behind each change.
