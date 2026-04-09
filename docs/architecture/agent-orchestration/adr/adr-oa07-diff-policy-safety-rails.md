---
title: "ADR-OA07: Diff-Policy + Safety Rails"
description: "Defines the bootstrap safety model for worktree isolation, branch-scoped rollback, and agent authority boundaries in maintained agent orchestration."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: proposed
created: "2026-04-05"
related_adrs:
  - "adr-oa01.1-conductor-strategy-v2.md"
  - "adr-oa03-agent-runner-architecture.md"
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa04.2-runner-contract.md"
  - "adr-oa04.3-provenance-run-artifact-contract.md"
  - "adr-oa04.4-policy-enforcement-contract.md"
---

# ADR-OA07: Diff-Policy + Safety Rails

Defines the bootstrap safety model for worktree isolation, branch-scoped rollback, and agent authority boundaries in maintained agent orchestration.

- **Filename**: `adr-oa07-diff-policy-safety-rails.md`
- **Heading**: `# ADR-OA07: Diff-Policy + Safety Rails`
- **Status**: Proposed
- **Type**: Design Detail
- **Date**: 2026-04-05
- **Author**: Aaron Solomon, GPT-5 Codex
- **Owner**: aaronksolomon

---

## Context

[ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) reserves OA07 for diff-policy and safety-rail decisions. [ADR-OA03](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md) recommends kernel-mandated worktrees, and [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md) plus [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md) assume worktree-scoped execution and `ROLLBACK(pre_run)` semantics.

OA07 does not replace OA04. OA04.x freezes the execution-contract layer; OA07.x freezes the bootstrap safety and mutable-workspace operating model required to execute those contracts safely in practice.

What remains unfrozen is the maintained contract for:

- the boundary between run artifacts and mutable execution workspace,
- the authority delegated to agents during bootstrap,
- the concrete rollback model for operational MVP runs,
- the diff-policy checks that make agent autonomy safe enough for routine PR creation.

This gap matters because the fastest path to bootstrap is not the full prompt-program/control-plane surface. It is one operational loop that can safely:

- create an isolated branch/worktree,
- let an agent edit, test, and validate inside that worktree,
- preserve enough provenance to review, recover, and iterate,
- keep merges to protected branches human-only.

The full OA07 bootstrap authority envelope includes commit, push, and PR update actions. The first runtime bootstrap milestone does not need to exercise every action in that envelope immediately, provided the worktree-isolated mutable loop is real and later review automation can build directly on it.

Without this contract, the maintained runtime risks conflating the canonical run directory with the mutable repository workspace, weakening rollback and making policy enforcement mostly descriptive rather than operational.

---

## Decision

### 1. Bootstrap Authority Envelope

For bootstrap operation, agents are allowed to perform the following actions only on conductor-managed work branches and worktrees:

- edit repository files,
- run tests and deterministic validation,
- create local commits,
- push their work branch,
- open or update a GitHub PR,
- respond to review comments and bot feedback on that PR.

Protected-branch merge remains human-only. Agent flows may advance a PR to review-ready state, but they may not merge to `main`, `master`, or any configured protected branch.

These actions define the allowed bootstrap authority envelope, not the minimum bar for the first operational runtime milestone. A maintained local/headless loop may land first, followed by commit/push/PR automation in a later OA07 implementation slice.

Bootstrap prioritizes one active PR/worktree per workflow run. Stacked PR orchestration and multi-agent branch coordination are deferred.

### 2. Workspace Isolation Is Kernel / Control-Plane Owned

All mutable orchestration runs that can change repository state MUST execute in a dedicated git worktree on a non-protected branch.

The maintained meaning of `working_directory` in runner and validation contracts is:

- the repository worktree root used for mutable execution,
- not the canonical run-artifact directory,
- not an adapter-local scratch directory.

Run artifacts and mutable workspace are distinct:

- the canonical run directory is the provenance and artifact boundary,
- the worktree is the mutable code-execution boundary.

### 3. Bootstrap Rollback Is Branch-Scoped

The required `ROLLBACK(pre_run)` capability for bootstrap is defined as rollback to the recorded pre-run base commit for the managed worktree branch.

For bootstrap, rollback semantics are branch-scoped rather than file-scoped:

- `pre_run` MUST always be available,
- `pre_run` resolves to the recorded `base_sha` for the worktree,
- rollback SHOULD prefer discarding and recreating the managed worktree from `base_sha` over ad hoc file restoration,
- `pre_step` and named checkpoints remain deferred.

This keeps rollback simple, deterministic, and compatible with one-PR-at-a-time operation.

### 4. Diff-Policy Safety Rails

The maintained bootstrap runtime MUST enforce safety rails across both native runner controls and post-step kernel checks.

Minimum enforced categories:

- protected-branch mutation is forbidden,
- edits outside allowed scope are forbidden when path policy is present,
- explicitly forbidden paths and operations are hard failures,
- dependency-manifest and lockfile changes must be explicitly allowed by policy or routed through review/gate handling,
- adapter inability to honor requested execution guarantees must fail fast rather than silently weakening policy.

Safety-rail enforcement is allowed to tighten requested policy. It may not loosen it.

### 5. Provenance Requirements for Workspace Safety

Each mutable run MUST persist enough workspace context to reconstruct the safety boundary for review and recovery.

Bootstrap-required workspace context includes:

- repository root,
- worktree path,
- branch name,
- `base_ref`,
- `base_sha`.

Recommended additional fields:

- current `head_sha`,
- PR number or URL,
- remote branch name.

The canonical run directory remains the execution-source artifact set, but workspace identity must be traceable from that run directory.

---

## Consequences

### Positive

- Aligns the maintained runtime with the existing architecture intent in OA03 and OA04.
- Gives bootstrap a simple operational target: one worktree, one branch, and a clear path to one PR with human-only merge.
- Makes rollback practical without requiring fine-grained undo machinery.
- Lets agents perform useful end-to-end development work while keeping protected-branch control with the human maintainer.
- Clarifies the missing boundary between canonical run artifacts and mutable repository state.

### Negative

- Adds real workspace-management work to the control plane and runtime.
- Defers richer recovery semantics such as `pre_step` rollback and named checkpoints.
- Defers stacked-PR and multi-agent branch coordination even if later workflows need them.
- Requires repository/GitHub integration work beyond the current runner and artifact contracts.

---

## Alternatives Considered

### A. Use the run-artifact directory as the mutable execution directory

Rejected: breaks the OA04.2 meaning of `working_directory`, weakens rollback, and confuses provenance with mutable state.

### B. Run agents directly in the main working tree and rely on commits for rollback

Rejected: too easy to contaminate ongoing human work, too hard to recover uncommitted or mixed changes, and misaligned with the existing worktree-first design intent.

### C. Let each adapter choose its own isolation model

Rejected for bootstrap: increases drift between agents and moves too much safety-critical behavior out of the kernel/control-plane boundary.

---

## Open Questions

1. Should bootstrap branch naming be frozen in this ADR family, or left to implementation config?
2. Should PR lifecycle events become canonical run events in a later OA07 decimal ADR, or remain metadata/artifact-only at first?
3. Should dependency-file policy be modeled as first-class structured policy, or start as a conventional path-based rule?

---

## Related ADRs

- [ADR-OA01.1: Conductor Strategy v2](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- [ADR-OA03: Agent Runner Architecture](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md)
- [ADR-OA04: Workflow Execution Contracts](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- [ADR-OA04.1: MVP Runtime Build-Out Sequence](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
- [ADR-OA04.2: Runner Contract](/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md)
- [ADR-OA04.3: Provenance and Run-Artifact Contract](/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
- [ADR-OA04.4: Policy Enforcement Contract](/architecture/agent-orchestration/adr/adr-oa04.4-policy-enforcement-contract.md)
