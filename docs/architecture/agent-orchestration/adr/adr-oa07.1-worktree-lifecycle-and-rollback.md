---
title: "ADR-OA07.1: Worktree Lifecycle and Rollback"
description: "Bootstrap implementation guide for managed worktree creation, run-directory separation, and branch-scoped rollback in maintained agent orchestration."
type: "implementation-guide"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: proposed
created: "2026-04-05"
parent_adr: "adr-oa07-diff-policy-safety-rails.md"
related_adrs:
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa04.2-runner-contract.md"
  - "adr-oa04.3-provenance-run-artifact-contract.md"
  - "adr-oa04.4-policy-enforcement-contract.md"
---

# ADR-OA07.1: Worktree Lifecycle and Rollback

Bootstrap implementation guide for managed worktree creation, run-directory separation, and branch-scoped rollback in maintained agent orchestration.

- **Filename**: `adr-oa07.1-worktree-lifecycle-and-rollback.md`
- **Heading**: `# ADR-OA07.1: Worktree Lifecycle and Rollback`
- **Status**: Proposed
- **Date**: 2026-04-05
- **Author**: Aaron Solomon, GPT-5 Codex
- **Owner**: aaronksolomon
- **Parent ADR**: [ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md)

---

## Context

[ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md) freezes the bootstrap safety model, but implementation still needs a concrete path for:

- how a managed worktree is created,
- how the worktree is connected to the canonical run directory,
- what `ROLLBACK(pre_run)` means operationally,
- what constitutes bootstrap completion.

The goal is to reach an operational MVP quickly. That means the first maintained implementation should optimize for one reliable local/headless workflow loop rather than for maximal flexibility or immediate GitHub automation.

---

## Decision

### 1. Bootstrap Workspace Context

Bootstrap runs should materialize an explicit workspace context distinct from run-artifact paths.

Minimum context fields:

- `repo_root`
- `worktree_path`
- `branch_name`
- `base_ref`
- `base_sha`

Recommended additional fields:

- `head_sha`
- `remote_branch`
- `pr_url`

This context should be persisted as a canonical run artifact or run metadata extension before mutable execution begins.

### 2. Separation of Boundaries

Bootstrap MUST keep these two boundaries distinct:

- canonical run directory: provenance, manifests, events, captured artifacts,
- mutable worktree directory: repository checkout used by `RUN_AGENT` and `RUN_VALIDATION`.

The worktree path MUST NOT be nested under the canonical run directory.

The maintained `working_directory` passed to runners and validation backends MUST be the worktree root.

### 3. Runtime Bootstrap MVP

The first operational milestone for OA07.1 is a maintained local/headless runtime loop.

That runtime bootstrap MVP should:

1. Resolve `base_ref` for the run.
2. Resolve the corresponding committed `base_sha`.
3. Create a managed branch for the run from `base_sha`.
4. Create a dedicated worktree for that branch.
5. Persist workspace context into the canonical run directory.
6. Execute mutable workflow steps against the worktree root.
7. Persist canonical artifacts, manifests, and events into the run directory.
8. Support `ROLLBACK(pre_run)` by restoring the managed worktree to `base_sha`.
9. Return final state and provenance through one maintained headless entry point.

Bootstrap should not require the operator's current working tree to be clean, provided the conductor creates a separate worktree from an explicit committed base ref.

### 4. Review Automation Follow-On

Once the runtime bootstrap MVP exists, the next OA07-aligned follow-on may extend the same managed branch/worktree flow to:

- create local commits,
- push the managed work branch,
- open or update a GitHub PR,
- respond to PR review or bot feedback.

This follow-on remains inside the OA07 authority envelope. Protected-branch merge stays human-only.

### 5. Rollback Semantics

For bootstrap, `ROLLBACK(pre_run)` means:

- the run records `base_sha` before any mutable step,
- rollback returns the managed branch/worktree to that `base_sha`,
- the preferred bootstrap implementation is to discard and recreate the worktree from `base_sha` rather than attempt in-place file restoration.

This choice is deliberate:

- it is simpler than step-granular undo,
- it avoids coupling rollback to incidental file-system state,
- it matches the one-PR-at-a-time bootstrap model.

`pre_step` and `checkpoint:<id>` remain deferred.

### 6. Completion Criteria

Runtime bootstrap MVP is complete when one maintained headless flow can:

- create a managed worktree from a committed base ref,
- materialize and persist explicit workspace context before mutable execution,
- run a workflow with `RUN_AGENT`, `RUN_VALIDATION`, and optional `EVALUATE`/`GATE`,
- pass the worktree root as `working_directory` for mutable step execution,
- write canonical run artifacts and provenance to the run directory,
- perform `ROLLBACK(pre_run)` by discarding and recreating the managed worktree at the recorded base state.

Review automation follow-on is complete when that same flow can additionally:

- create local commits on the managed branch,
- push the work branch,
- open or update a PR.

### 7. Explicit Deferrals Beyond Runtime Bootstrap MVP

The following are deferred beyond the first runtime bootstrap milestone:

- commit/push/PR automation if it does not fit cleanly in the initial implementation slice,
- stacked PR orchestration,
- multiple mutable agents sharing one branch/worktree,
- named checkpoints,
- in-place partial rollback,
- full OA05 compile-validation enforcement,
- full OA06 evaluator fixture coverage beyond the bootstrap decision path,
- non-script harness backends.

---

## Consequences

### Positive

- Narrows bootstrap implementation to one operationally valuable loop.
- Makes the missing workspace service work concrete and testable.
- Prevents further drift between runner contracts and actual execution directories.
- Keeps rollback understandable for both human operators and future automation.

### Negative

- Leaves some planned flexibility explicitly out of the first operational slice.
- Requires follow-on ADR work if stacked PRs or shared multi-agent worktrees become first-class.
- Adds Git lifecycle work to the bootstrap path and leaves GitHub automation as a near follow-on.

---

## Alternatives Considered

### A. Require full prompt-library and planner integration before bootstrap

Rejected: too slow for the stated goal. Bootstrap should land an operational development loop first, then deepen the prompt-program surface using the working system.

### B. Support `pre_step` rollback in the first operational slice

Rejected: higher complexity than the bootstrap target needs.

### C. Require PR creation and update in the first runtime milestone

Rejected: this would slow the first operational slice unnecessarily. GitHub automation remains inside the OA07 authority envelope, but it does not need to block the first worktree-isolated runtime loop.

---

## Open Questions

1. Should workspace context live in `metadata.json`, a dedicated canonical artifact, or both?
2. Should branch cleanup after abandoned runs be automated in bootstrap, or deferred to a later workflow slice?
3. Should PR creation be a first-class opcode later, or remain a control-plane action around OA04 opcodes?

---

## Related ADRs

- [ADR-OA04.1: MVP Runtime Build-Out Sequence](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
- [ADR-OA04.2: Runner Contract](/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md)
- [ADR-OA04.3: Provenance and Run-Artifact Contract](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
- [ADR-OA04.4: Policy Enforcement Contract](/architecture/agent-orchestration/adr/adr-oa04.4-policy-enforcement-contract.md)
- [ADR-OA07: Diff-Policy + Safety Rails](/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md)
