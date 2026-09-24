# Global Business Logic Rules

This repository is a fast-moving, spec-driven development environment. Cheap
context or fast execution never excuses structural regression. These rules bind
every code change. `AGENTS.md` owns session procedure, commit format and the
anti-pattern registry; this file owns the architectural invariants those
procedures exist to protect.

Each rule below says how it is checked. A rule checked only by review is still
binding -- it means a human or a reviewing agent is the gate, not that the rule
is optional.

## Why these rules exist, and what wins when two of them conflict

The control plane was not built for tidiness. It was built because the same
classes of failure kept reappearing in agent-written code, and because the
spec-driven work of establishing what was already true was being redone from
scratch every session. Both rules below follow from that, and both decide
conflicts:

- **A wrong green is worse than a red.** A gate that passes while the corpus is
  inconsistent teaches every later agent to trust something false.
- **Write for the agent that arrives cold.** The next reader has none of this
  session's context and must not have to re-derive it.

When two rules genuinely conflict, apply them in this order. Higher wins.

1. **Corpus and state safety (Rule 7).** Never guess, never force a green,
   never write non-atomically. If obeying another rule would require the engine
   to infer intent or leave a partial write, the other rule yields.
2. **Single source of truth (Rule 1).** A second copy of a fact is a future
   contradiction. Prefer deleting a copy and linking over keeping both in sync.
3. **Isolation of external volatility (Rules 4 and 2).** Keep an upstream
   provider's quirks inside its own module. Isolation beats compression.
4. **The duplication buffer (Rule 3).** Duplication is the correct answer until
   the third occurrence. A reviewer, a linter or a complexity score asking for
   an abstraction at the second occurrence is asking for a deviation, and may
   be declined by citing this rule.
5. **Simplicity of runtime code (Rule 5).** Push complexity into the gates, not
   into the application.

Two things that are never tie-breakers: how cheap a change is, and how fast it
can be executed. Cost decides scheduling, never correctness. A stale or
unpublished review carries no authority against current on-disk code.

**When the conflict is with a rule's own text, stop.** If following a rule
would require changing that rule, or two rules cannot both hold as written,
that is an owner decision. Report it and continue with everything else. Do not
resolve it silently, and do not document an exception into existence while the
prohibition it contradicts stays absolute -- that leaves two live documents
disagreeing, which is the failure this whole file exists to prevent.

Worked examples, all real:

| Conflict | Resolution |
|---|---|
| A reviewer asked to merge two near-identical provider helpers | Declined. The providers detect rate limits in three different dialects, so merging would pull foreign semantics into a shared layer. Rule 4 beat the DRY request; the duplication inside one module was extracted instead. |
| The commit preflight refuses commits that change the checker, but skipping hooks is forbidden | Escalated to the owner rather than resolved. The outcome kept the prohibition absolute and used a narrower mechanism that skips one named hook. |
| A faster fix existed for a non-atomic write path | Rejected. Rule 7 outranks execution cost. |

## 1. Single Source of Truth (SSoT)

- Each fact has one owner. One document holds the fact.
- Do not copy a fact into a second document. Link to the owner instead.
- If two documents disagree, the owner document wins.
- Stale data and unpublished reviews are irrelevant. Current on-disk code is
  current truth. A review that was never written to the repository cannot be
  superseded by one that was, so it carries no authority at all.

Named owners, because "design" and "defects" each name more than one document
here:

| Fact | Owner | Also holds a copy |
|------|-------|-------------------|
| Open defect status | `docs/agents/FINDINGS.md` | `docs/history/findings/FINDINGS_ARCHIVE.md` keeps the same record under the same F-ID after resolution. The GitHub issue mirror is a convenience index and is not maintained; `docs/agents/FINDINGS.md` wins on any disagreement. |
| System and runtime architecture | `docs/ARCHITECTURE.md` and its `docs/architecture/*.md` diagrams | -- |
| The visual design system | `docs/design/README.md`, with `docs/design/RECONCILIATION.md` as the override ledger | `DESIGN.md` at the repository root states the same design facts and must be kept declared, not duplicated silently. |
| Agent rules and session procedure | `AGENTS.md` | -- |

**How this is checked.** `scripts/doc_state_sync.py` re-checks every fact that
has been declared in `config/docsync.toml` -- values that must agree across sites
(DOC009), citations that must resolve (DOC010), and claims that must not
survive (DOC011). It cannot discover a new duplicate on its own. When a fact
starts living in two places, declare it in the same commit that copies it. That
declaration step is the rule; the tool only holds the line afterwards.

## 2. Separation of Concerns and Single Responsibility

- Keep logical layers decoupled.
- The data transport layer must not know the presentation layer.
- Route handlers parse the request, trigger the pipeline, and return a
  response. Nothing else.
- Never put raw network fetching or third-party JSON parsing inside a route.
- Dedicate exactly one isolated service module to each external API.

**How this is checked.** Review, plus the dependency graph in
`.claude/SESSION_CONTEXT.md`, which any new cross-module import must be
reflected in.

## 3. The Rule of Three duplication buffer

- Isolation matters more than compression.
- Duplicating a parser, a utility path or a helper across separate API modules
  is allowed up to two occurrences.
- Do not abstract shared logic until the same pattern appears a third time.
- The buffer exists so that one integration changing does not break the others
  through an abstraction built too early.

A reviewer asking for consolidation at the second occurrence is asking for a
deviation from this rule, and may be declined by citing it.

**How this is checked.** Review.

## 4. Anti-Corruption Layer and the Law of Demeter

- External volatility must never cross the application border.
- Translate and flatten an upstream payload into a native contract at the
  moment it enters the system.
- Controllers, business logic and templates stay oblivious to foreign
  terminology.
- No deep drilling such as `response["data"]["provider"]["id"]` in the core.
- When an upstream structure changes, repair it inside the translation layer
  only. Downstream consumers stay untouched.

**How this is checked.** Review.

## 5. Real-world KISS

- Keep runtime application code flat, boring and predictable.
- Simple runtime code is earned by strict verification gates in the tooling
  layer, which is why the tooling is larger than the application it checks.
- `scripts/dev/frontend_gate.py` checks layout integrity across the full
  viewport spectrum: mobile, 1080p, 1440p and 4K. Mobile is the breakpoint of
  concern.
- Changes to templates or assets must pass that gate at every size.
- Do not build internal workarounds for layout or network edge cases. Let the
  gates catch failures.

**How this is checked.** The frontend gate, in CI and before commit.

## 6. Distributed network defence

- Be conservative in what is sent and liberal in what is accepted.
- Parse inbound data defensively through fallback accessors. Ignore unexpected
  new upstream fields rather than raising.
- Network drops and timeouts happen mid-pipeline and cause retries.
- Every state-changing pipeline request carries a deterministic idempotency
  key, so a retry cannot create a duplicate mutation upstream.

**How this is checked.** Review and the service-level test suites.

## 7. Rigid logic and deterministic diagnostics

- Verify behaviour before mutating structure. Do not refactor code that lacks
  test coverage of the paths being changed.
- The engine is an invariant checker. When it detects a structural
  contradiction it raises a unique, typed diagnostic code and stops.
- It must never guess semantic intent, invent a missing fact, or resolve a
  contradiction in order to force a green state. Where two sides disagree, both
  may be the history worth keeping, so it reports and halts.
- The engine may rewrite only what it can derive deterministically from facts a
  human already authored: relocating a log entry, repaginating an archive,
  recomputing an aggregate from its source. That is rendering, not repair, and
  it never changes the exit code a real diagnostic produced.
- Any operation that updates recorded state, logs progress, or closes an
  execution phase publishes as a single atomic unit, under an exclusive lock,
  with pre-image journaling, so a crash mid-session cannot leave a partial
  corpus.

**How this is checked.** The typed diagnostics DOC001 onward, and the
publication transaction in `scripts/docsync/transaction.py`. The catalogue and
the recovery behaviour are documented in
`docs/architecture/documentation-tooling.md`.
