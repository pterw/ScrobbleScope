# AI-driven development cycle

This diagram is the canonical owner of the agent-assisted development loop.
Canonical context establishes scope, bounded work packages drive changes, and
validation feeds the next iteration.

```mermaid
flowchart TD
    Request([Owner request, issue, or review finding]) --> Triage{Review finding<br/>or comment job?}
    Triage -->|No| Context[Read canonical context<br/>AGENTS.md, PLAYBOOK.md, batch definition,<br/>SESSION_CONTEXT.md, AGENT_NOTES.md]
    Triage -->|Yes| Fetch[Fetch the thread or comments first]
    Fetch --> Actionable{Comment job with<br/>nothing actionable?}
    Actionable -->|Yes| Stop([Stop without full bootstrap])
    Actionable -->|No| Scoped[Read only the scoped file<br/>and related tests or config<br/>Open batch or history docs only when<br/>the comment depends on them]
    Scoped --> Implement
    Context --> Align[Refresh origin and run<br/>check_worktree_alignment.py]
    Align --> Baseline[Confirm baseline gates<br/>pytest and pre-commit]
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
    Commit --> Authorize{Push authorized?}
    Authorize -->|WP or batch commit, any session| Pause([Pause after the commit])
    Authorize -->|Review-fix commit on an open PR<br/>Claude Code or Codex session only| PR
    Authorize -->|Review-fix commit, any other agent<br/>Copilot, Jules, and the rest| Pause
    Pause -->|Owner says push| PR[Open or update the pull request]
    PR --> CI[GitHub Actions Quality Gate]
    CI --> Decision{CI or review outcome}
    Decision -->|Failure or actionable feedback| Diagnose[Reproduce, find root cause,<br/>and repair the issue class]
    Diagnose --> Implement
    Decision -->|Green| OwnerReview[Owner review in the browser]
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
    class Align,Baseline,Targeted,Gates,SelfReview,CI,Authorize gate
    class Decision,Diagnose feedback
    class Current current
```

Because `main` accepts linear-history merges, a merge can leave the source
branch SHA-diverged from `origin/main` with an identical tree. The guard
reports `WT004`; `AGENTS.md` owns the tree-equality precondition for realignment.

`AGENTS.md` owns the push rule; this diagram only routes it. The direct
review-fix path is a standing exception granted to Claude Code and Codex
sessions alone. Every other agent, including GitHub Copilot task sessions and
their subagents, pauses for owner instruction on a review-fix commit like any
other commit. Three actions always need explicit instruction whatever the
session: force-pushes, history rewrites, and anything targeting `main`. A
Copilot session that has been authorized to push uses the platform progress
tool rather than shell `git` or `gh`.
