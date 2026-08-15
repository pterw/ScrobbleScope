# ScrobbleScope: development cycle and runtime architecture

Canonical index for the development, runtime, pipeline, and repository-tooling
diagrams. Each linked document owns one diagram so corrections have one place
to land. The code remains authoritative when a diagram and implementation
disagree.

Last verified against the tree on 2026-08-15.

**Arrow semantics.** Solid arrows between Python modules are imports. Between
other participants they are requests, calls, or containment. Dotted arrows are
runtime edges that are not imports, including responses, polls, deployment,
and dispatch through an injected callable. Sequence arrows are calls and
returns. Each detail document calls out omitted import edges.

## 1. AI-driven development cycle

Bootstrap, bounded work, validation, review, merge, and post-merge realignment:
[AI-driven development cycle](architecture/development-cycle.md).

## 2. Full-stack application architecture

Browser, Flask runtime, background pipelines, state, external services, and
deployment: [Full-stack application architecture](architecture/runtime-system.md).

## 3. Top Albums request and enrichment sequence

Job admission, Last.fm retrieval, Spotify/cache enrichment, result storage,
and polling: [Top Albums sequence](architecture/top-albums-sequence.md).

## 4. Heatmap request and rendering sequence

Job admission, partial-data handling, UTC aggregation, polling, and rendering:
[Heatmap sequence](architecture/heatmap-sequence.md).

## 5. Documentation and tooling architecture

Canonical documents, docsync, the worktree guard, pre-commit, and CI:
[Documentation and tooling architecture](architecture/documentation-tooling.md).

## Source references

- Rules and bootstrap order: `AGENTS.md`
- Active work and handoff state: `PLAYBOOK.md`, Sections 3 and 4
- Batch scope: `BATCH21_DEFINITION.md`
- Complete module graph: `.claude/SESSION_CONTEXT.md`, Sections 3 and 4
- Product overview: `README.md`, Architecture
- CI gate: `.github/workflows/test.yml`
- Diagram workflow: `.github/instructions/mermaid.instructions.md`
