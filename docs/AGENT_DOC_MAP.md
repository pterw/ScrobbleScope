# Document map for agents

This document is for AI agents that work on ScrobbleScope. It is written for
agents that are new to the repository, in particular agents other than the
one that wrote most of these documents.

This document is a map. It tells you which document to open, and it tells you
why the document exists. It does not repeat the rules. `AGENTS.md` owns the
rules.

Language note: this document uses short sentences and the active voice, in
the style of ASD-STE100 Simplified Technical English. The STE dictionary is
licensed, and the writer of this document could not read it. Do not read this
note as a claim of STE compliance.

---

## 1. The rule that shapes every document

Each fact has one owner. One document holds the fact. Every other document
links to it.

`AGENTS.md` calls this the anti-duplication rule.

The reason is cost. This repository is written by many agents across long
gaps of time. A copied fact does not stay a copy. One agent corrects the
first copy, and the second copy becomes a lie. The repository has paid for
this many times. `AGENTS.md` records the largest cases in its Anti-Pattern
Registry.

Three consequences apply to you:

1. Do not copy a fact into a second document. Link to the owner instead.
2. If two documents disagree, find the owner. The owner wins.
3. If a document tells you that another document owns a subject, stop reading
   and open that document. The pointer is deliberate. It is not laziness.

---

## 2. Where to start

`AGENTS.md` owns the read order. Follow the "Session Bootstrap" section of
that document. Do not build your own order.

The order puts the rules first and the state last. The reason is that state
changes every day and rules almost never change. An agent that reads the
state first will apply it with the wrong rules.

`AGENTS.md` also gives two fast paths. Use them when your task is a single
pull-request comment. A full bootstrap for a one-line comment wastes tokens.

`HANDOFF_PROMPT.md` holds two things. It holds the checks that you run after
you read the bootstrap files. It holds the checklist that you follow when you
stop work. It holds no rules, and it points to `AGENTS.md` for all of them.

---

## 3. The document groups

| Group | Documents | Open it when |
|-------|-----------|--------------|
| Rules | `AGENTS.md` | Always. First. |
| Session procedure | `HANDOFF_PROMPT.md` | You start or end a session. |
| Work order | `PLAYBOOK.md` | You need the next action or the recent history. |
| Batch scope | `BATCH21_DEFINITION.md` | You work inside the active batch. |
| State | `.claude/SESSION_CONTEXT.md` | You need the test count, the module list, or the dependency graph. |
| Owner context | `AGENT_NOTES.md` | You need a preference, the local setup, or a known constraint. |
| Findings | `FINDINGS.md` | Your task names an `F-` identifier, or a P0 or P1 item. |
| Architecture | `docs/ARCHITECTURE.md` | You need a diagram of the system or the pipelines. |
| History | `docs/history/` | A log entry or a task sends you to a dated document. |

Two notes on this table.

`FINDINGS.md` is not part of the bootstrap set. Open it on demand. The file
is long, and most tasks do not need it.

The batch definition moves. A definition file at the repository root belongs
to an open batch. A definition file under `docs/history/definitions/` belongs
to a closed batch. Use the location to tell the two apart. `PLAYBOOK.md`
Section 3 is the authority when you are not sure.

---

## 4. Documents for humans

Some documents at the repository root are for people, not for agents. They
give you no authority. Do not quote them as a rule.

| Document | Audience |
|----------|----------|
| `README.md` | The user and the developer. Product and setup. |
| `DEVELOPMENT.md` | The reader who wants the reasoning behind the project. |
| `DEPLOY.md` | The person who deploys the application. |
| `CONTRIBUTING.md` | The outside contributor. |
| `CODE_OF_CONDUCT.md` | The community. |

`DEVELOPMENT.md` states this limit in its own opening. It explains how the
project was built. It grants no agent authority.

`README.md` is the one exception to the "do not edit" instinct. `AGENTS.md`
requires you to update it when your change affects setup or visible
behaviour. Read the exception in `AGENTS.md` first, because an active batch
can defer README work to a dedicated work package.

---

## 5. How to read an audit

An audit in this repository moves through six steps. The SWE principles
audit is the worked example.

1. **The charter.** The owner writes what to audit, how to grade, and what
   result stops the work. Example: `docs/SWE_AUDIT_CHARTER.md`.
2. **The execution.** One agent runs the charter in a dedicated session.
3. **The report.** The agent writes a dated report under
   `docs/history/reports/`. Example:
   `docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md`.
4. **The findings.** New problems become items in `FINDINGS.md`. Each item
   gets an `F-` identifier.
5. **The log entry.** A dated entry goes into `PLAYBOOK.md` Section 4, in the
   same commit as the report.
6. **The retirement.** The charter stays in the repository. Its status line
   says that it is retired, and it names the report.

### Why the charter stays after the audit ends

The report tells you what the agent found. The charter tells you what the
agent was asked to find. You need both to judge the report. A finding that
is absent from a report can mean that the code is clean, or it can mean that
the charter put that code out of scope. Only the charter answers that.

### Why a dated report is never edited

A dated report records what was true on that date. If you edit the body, the
record disappears, and no one can tell what the audit concluded.

Corrections go into a new section at the top of the report. The body stays as
written.

`docs/history/reports/SWE_PRINCIPLES_AUDIT_2026-08-20.md` shows the pattern.
It has an "Owner review" section. That section states that one finding in the
body is partly wrong. The wrong text is still there, below it. Read the
correction section before you trust the body.

### An audit report is not current truth

An audit report is a measurement of one day. Three things can make it stale:

- The code changed after the audit ran.
- The owner overruled a finding.
- The audit was wrong.

The third case is real. The SWE report filed one finding on a false premise.
The owner corrected it.

When a report and the source code disagree, the code wins. `docs/ARCHITECTURE.md`
states the same rule for the diagrams.

### Where the other audits are

`docs/history/reports/` holds every dated report. The names carry the date.
`FINDINGS.md` lists the important ones under "Source documents".

---

## 6. How to read the findings

`FINDINGS.md` holds the open items. `docs/history/findings/FINDINGS_ARCHIVE.md`
holds the closed items. Nothing is deleted. The archive keeps the search
history.

Read the identifier first. The format is `F-<context>-<number>`. The context
is a batch tag, such as `B21`, or a source tag, such as `SWE` or `DOCSYNC`.
`AGENTS.md` owns the list of valid tags and the rules for writing a finding.

Three properties matter when you navigate:

- **The identifier never changes.** It stays with the item when the item
  moves to the archive. Old documents that cite the identifier stay correct.
  Do not renumber a finding.
- **The severity sets the order, not the truth.** P0, P1, P2, and Info tell
  you when the owner plans to act. A P2 item is still a real defect.
- **The section tells you the state.** An item under "Resolved this batch" is
  closed but not yet archived. Rotation moves it later.

Do not add a finding as a side effect of another task. `AGENTS.md` owns the
rules for writing one, and a finding that skips them costs a review round.

---

## 7. Traps in this repository

These are navigation hazards. Each one has caught an agent before.

**Three paths hold the same archive name.** Only one holds content:
`docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md`. The two paths under
`docs/history/` are pointer stubs. They exist so that old references still
resolve. Read `docs/logarchive/README.md` for the lookup map.

**Dated entries are records.** A dated entry in `PLAYBOOK.md` Section 4, and
a dated report under `docs/history/`, both describe one moment. Do not
correct them when the facts change. Correct the live document instead.
`AGENTS.md` states this exception inside its Anti-Pattern Registry.

**Part of the state document is machine-written.** `.claude/SESSION_CONTEXT.md`
contains a managed block. `scripts/doc_state_sync.py` writes it from
`PLAYBOOK.md`. Do not edit the block by hand. Do not move an entry across a
`DOCSYNC` marker by hand.

**Numbers in documents go stale.** Test counts, module counts, and coverage
figures are copies. Run the measuring command before you repeat a number. A
coverage figure in this repository was wrong for five months because agents
copied it forward.

**A green tool run is not proof.** `pre-commit run --all-files` saves and
restores your unstaged changes. That cycle has reverted files that nobody
edited, while every hook reported a pass. Compare the files before and after
the run. After you commit, read the file back out of the commit.

**`.github/agents/` is off limits.** `AGENTS.md` forbids it. The directory
does not exist today, so the rule is a guard against a future conflict of
rule sources.

**Copilot loads two files of its own.** `.github/copilot-instructions.md` and
`.github/instructions/mermaid.instructions.md` cover diagram work only.
`AGENTS.md` is still the ruleset.

---

## 8. Before you change a document

`AGENTS.md` owns the gates. Its "Commit Rules" section gives the order, and
its "Doc Sync Rules" section gives the sync step. Follow them there.

Two points of that procedure surprise new agents, so they are named here with
their reasons:

- **You write the documentation first, then run the gates.** One gate checks
  the documentation. A gate that runs before the update cannot check it.
- **You stage files by name.** Bulk staging is forbidden, even when every
  changed file belongs to your work. The command is the hazard, because it
  collects whatever else sits in the tree.

`scripts/doc_state_sync.py` validates the live documents and returns numbered
`DOC` diagnostics. `scripts/docsync/integrity.py` defines each code and the
rule it enforces. Read the diagnostic text; it names the repair.

---

## 9. If two documents disagree

Work through this order:

1. Find the owner of the fact in the "Document Roles" table in `AGENTS.md`.
   The owner wins.
2. If neither document owns the fact, prefer the source code. Code is not a
   copy.
3. If the disagreement is about the next action, prefer `PLAYBOOK.md`
   Section 3.
4. If the disagreement changes what you are about to do, and the steps above
   do not settle it, stop and ask the owner. Do not merge two rule sources
   yourself.

Then repair the loser in the same commit as your work. A disagreement that
you leave behind becomes the next agent's review round.
