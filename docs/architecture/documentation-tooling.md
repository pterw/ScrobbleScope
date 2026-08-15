# Documentation and tooling architecture

This diagram is the canonical owner of the repository documentation, docsync,
worktree-guard, pre-commit, and CI relationships.

```mermaid
flowchart TD
    A[AGENTS.md<br/>rules] --> H[HANDOFF_PROMPT.md]
    A --> P[PLAYBOOK.md<br/>work order + execution log]
    P --> B[BATCH21_DEFINITION.md<br/>scope + acceptance criteria]
    P --> S[SESSION_CONTEXT.md<br/>current-state dashboard]
    P --> BL[docs/history/logs/<br/>tagged Batch N entries]
    P --> LA[docs/logarchive/<br/>rotated side-task entries]

    D[doc_state_sync.py] --> CLI[docsync.cli]
    CLI --> Integrity[docsync.integrity]
    CLI --> Logic[docsync.logic]
    CLI --> Models[docsync.models]
    Integrity --> Logic
    Integrity --> Models
    Integrity --> Parser[docsync.parser]
    Integrity --> Render[docsync.renderer]
    Logic --> Models
    Logic --> Parser
    Logic --> Render
    Render --> Models
    Render --> Parser
    Parser --> Models

    D -. reads and rewrites .-> P
    D -. refreshes managed blocks .-> S
    D -. rotates tagged entries into .-> BL
    D -. rotates untagged entries into .-> LA

    G[check_worktree_alignment.py] --> Guard[dev/worktree_guard<br/>public facade]
    Guard --> Diag
    Guard --> Inspect
    Guard --> Lineage
    Guard --> Runner
    Guard --> Types
    Guard --> Venv
    Inspect[_worktree_guard_inspection] --> Diag
    Inspect --> Lineage[_worktree_guard_lineage]
    Inspect --> Runner[_worktree_guard_runner]
    Inspect --> Types
    Inspect --> Venv[_worktree_guard_venv]
    Lineage --> Diag
    Lineage --> Types
    Venv --> Diag
    Venv --> Types
    Runner --> Types
    Diag[_worktree_guard_diagnostics] --> Types[_worktree_guard_types<br/>stdlib-only leaf]
    Guard -. parses Branch metadata from .-> P

    PC[pre-commit] -. runs .-> D
    CI[GitHub Actions Quality Gate] -. runs .-> PC

    classDef doc fill:#f5efe2,stroke:#6a4baf,color:#1a1820
    classDef tool fill:#eee7fb,stroke:#6a4baf,color:#1a1820
    classDef gate fill:#e5f1e8,stroke:#4d7a5a,color:#1a1820
    class A,H,P,B,S,BL,LA doc
    class D,CLI,Integrity,Logic,Models,Parser,Render,G,Guard,Inspect,Lineage,Runner,Venv,Diag,Types tool
    class PC,CI gate
```

The facade re-exports all six guard modules. `doc_state_sync.py` imports only
`docsync.cli`; the lower-level package remains acyclic. Pre-commit runs docsync,
and CI runs pre-commit plus pytest, coverage, and advisory pip-audit.
