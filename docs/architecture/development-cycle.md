# AI-driven development cycle

This diagram is the canonical owner of the agent-assisted development loop.
Canonical context establishes scope, bounded work packages drive changes, and
validation feeds the next iteration.

```mermaid
flowchart TD
    Request([Owner request, issue, or review finding]) --> Context[Read canonical context<br/>AGENTS.md, PLAYBOOK.md, batch definition,<br/>SESSION_CONTEXT.md, AGENT_NOTES.md]
    Context --> Align[Refresh origin and run<br/>check_worktree_alignment.py]
    Align --> Baseline[Confirm baseline gates<br/>pytest, pre-commit, docsync]
    Baseline --> Scope[Select the active batch and bounded WP<br/>with acceptance criteria and exclusions]
    Scope --> Explore[Trace code, tests, docs,<br/>dependencies, and linked findings]
    Explore --> Design[Design the smallest coherent change<br/>with acyclic dependencies and real tests]
    Design --> Implement[Implement one work package<br/>with tests and required docs]
    Implement --> Targeted[Run targeted and adversarial checks]
    Targeted --> Docs[Update source-of-truth documents<br/>and the dated execution log]
    Docs --> Sync[Run doc_state_sync.py --fix]
    Sync --> Gates[Run full validation gates]
    Gates --> SelfReview[Read changed files whole<br/>and sweep sibling claims]
    SelfReview --> Commit[Create one conventional commit<br/>with specific staged paths]
    Commit --> PR[Open or update the pull request]
    PR --> CI[GitHub Actions Quality Gate]
    CI --> Decision{CI or review outcome}
    Decision -->|Failure or actionable feedback| Diagnose[Reproduce, find root cause,<br/>and repair the issue class]
    Diagnose --> Implement
    Decision -->|Green| OwnerReview[Owner review and required E2E]
    OwnerReview -->|Issue found| Diagnose
    OwnerReview -->|Approved| Close[Merge or close the WP<br/>and update handoff state]
    Close --> Realign[Realign the source branch after merge]
    Realign --> Context

    Current[Current Batch 21 order<br/>F-SWE-1 audit, then WP-1] -.-> Scope

    classDef source fill:#f5efe2,stroke:#6a4baf,color:#1a1820
    classDef gate fill:#eee7fb,stroke:#6a4baf,color:#1a1820
    classDef feedback fill:#f9e5dd,stroke:#a64b39,color:#1a1820
    classDef current fill:#e5f1e8,stroke:#4d7a5a,color:#1a1820
    class Context,Scope,Docs,Sync source
    class Align,Baseline,Targeted,Gates,SelfReview,CI gate
    class Decision,Diagnose feedback
    class Current current
```

Because `main` accepts linear-history merges, a merge can leave the source
branch SHA-diverged from `origin/main` with an identical tree. The guard
reports `WT004`; `AGENTS.md` owns the tree-equality precondition for realignment.
