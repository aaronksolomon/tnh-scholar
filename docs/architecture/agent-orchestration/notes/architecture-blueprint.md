---
title: "Architecture Blueprint"
description: "High-level blueprint of the agent orchestration system, its maintained core subsystems, and the current flow of control."
owner: ""
author: "aaronksolomon, Codex"
status: draft
created: "2026-04-10"
updated: "2026-04-10"
---
# Architecture Blueprint

## Purpose

This note is a high-level architecture blueprint for new designers and engineers working in TNH Scholar agent orchestration.

It is meant to make system evaluation and directional planning faster by answering three questions:

1. what the system is trying to be,
2. which parts are the current maintained core,
3. how control and evidence actually flow through the runtime today.

This note is not an ADR and does not freeze design decisions. It should be read alongside the direction memo at [/docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md](/docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md).

## Orientation

The architectural center of gravity comes from four sources:

- [/docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md](/docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)
- [/docs/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md](/docs/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- [/docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md](/docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
- [/docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md](/docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md)

The short version:

- the system is a prompt-program runtime, not an autonomous agent shell,
- the kernel owns execution, capture, policy enforcement, and provenance,
- semantic judgment belongs in `EVALUATE` and `GATE`, not in ad hoc app logic,
- mutable execution must happen in a managed git worktree, not in the canonical run-artifact directory,
- bootstrap is the first strategic threshold because it makes the system operational rather than preparatory.

## System Thesis

At a high level, agent orchestration is trying to do this:

```text
workflow definition + prompts + policies
                |
                v
      deterministic kernel execution
                |
                v
 managed workspace + agent runs + validation
                |
                v
 canonical artifacts + provenance + reviewable result
```

The design intent is that English-defined workflows and prompts determine behavior, while code provides the execution substrate:

- workflow loading,
- step routing,
- policy assembly and hard-failure checks,
- agent invocation,
- validation execution,
- workspace lifecycle,
- artifact persistence,
- provenance capture.

## Architectural Layers

The current maintained path follows the OS01 split:

```text
Application / CLI
  -> thin bootstrap service and composition root
Domain orchestration
  -> kernel workflow execution and subsystem protocols
Infrastructure adapters
  -> git worktree service, CLI runner adapters, filesystem artifact store,
     subprocess execution, validation backends
```

In practical repo terms:

| Layer | Responsibility | Primary modules |
| --- | --- | --- |
| Application | headless entry surface, typed config, runtime profile assembly | `src/tnh_scholar/agent_orchestration/app/`, `src/tnh_scholar/cli_tools/tnh_conductor/` |
| Domain orchestration | workflow execution, step semantics, routing, policy/provenance coordination | `src/tnh_scholar/agent_orchestration/kernel/` |
| Workspace boundary | managed worktree lifecycle and rollback | `src/tnh_scholar/agent_orchestration/workspace/` |
| Agent execution | agent-neutral runner service and CLI-specific adapters | `src/tnh_scholar/agent_orchestration/runners/` |
| Validation | builtin validators, generated harness execution, harness report merging | `src/tnh_scholar/agent_orchestration/validation/` |
| Policy assembly | requested versus effective execution policy and hard violations | `src/tnh_scholar/agent_orchestration/execution_policy/` |
| Artifact persistence | canonical run directory, manifests, event log, terminal metadata | `src/tnh_scholar/agent_orchestration/run_artifacts/` |
| Execution substrate | subprocess execution and low-level invocation shaping | `src/tnh_scholar/agent_orchestration/execution/` |

## Maintained Core Systems

### 1. Headless Application Surface

The current maintained entry point is `tnh-conductor`.

Its job is intentionally small:

- accept one workflow path and repo-root context,
- choose the bootstrap runtime profile,
- construct typed bootstrap config,
- invoke one maintained service,
- emit a typed run summary.

This is the current bootstrap composition root, not the place where workflow semantics should accumulate.

### 2. Kernel Runtime

The kernel is the main orchestration engine.

It owns:

- workflow validation,
- run creation and run-id generation,
- per-step execution,
- deterministic route resolution,
- policy summary persistence and hard-failure checks,
- artifact recording,
- terminal metadata and final-state persistence.

Conceptually, the kernel is the narrow waist of the system. Almost every major subsystem meets there.

### 3. Workspace Service

The workspace service is the mutable repository boundary.

The maintained git-backed implementation:

- resolves `base_ref` to `base_sha`,
- creates a managed branch,
- creates a dedicated git worktree,
- records workspace context,
- provides workspace snapshots and diff summaries,
- implements `ROLLBACK(pre_run)` by discarding and recreating the worktree at `base_sha`.

This is the key OA07.1 safety boundary. The worktree is where code changes happen. It is not the artifact store.

### 4. Runner Subsystem

The runner subsystem normalizes CLI-facing agent execution.

Its shape is:

- a delegating runner service,
- agent-neutral request and result models,
- CLI-specific adapters for Codex and Claude,
- normalized output back to the kernel.

The kernel should not know the details of Codex CLI flags or Claude CLI capture formats. Adapters absorb that variance.

### 5. Validation Subsystem

The validation subsystem executes deterministic checks after or between agent steps.

It currently supports:

- builtin validator identifiers mapped to trusted local commands,
- generated harness execution through a script backend,
- structured harness report loading,
- stdout, stderr, and captured-artifact aggregation.

This is the maintained mechanism for test and harness evidence. It is part of the refinement loop, not an afterthought.

### 6. Artifact and Provenance Boundary

The artifact subsystem creates the canonical run directory and step manifests.

This boundary matters because later evaluation and review should resolve evidence through canonical roles and manifests rather than incidental filenames.

The maintained run directory shape is:

```text
<runs_root>/<run_id>/
  metadata.json
  final-state.txt
  events.ndjson
  artifacts/
    <step_id>/
      manifest.json
      ...
```

### 7. Execution Policy Layer

The execution policy layer assembles requested and effective policy and records violations before a step runs.

Right now the strongest enforced runtime guard is simple and important:

- mutable execution on protected branches is a hard violation.

This layer is where future path policy, capability tightening, and safety enforcement will continue to concentrate.

## High-Level Flow of Control

The current maintained bootstrap path works like this:

1. A user or higher-level tool invokes `tnh-conductor run --workflow <path> --repo-root <path>`.
2. The CLI builds storage config and the explicit bootstrap runtime profile.
3. `HeadlessBootstrapService` loads the workflow document.
4. The bootstrap service rejects unsupported semantic-control steps early. Today that means `EVALUATE` and `GATE` fail closed in the maintained bootstrap entry.
5. The bootstrap factory assembles the maintained kernel bundle:
   - kernel service,
   - git worktree workspace service,
   - filesystem artifact store,
   - delegating runner service,
   - validation service,
   - workflow validator,
   - temporary fail-closed evaluator and gate collaborators.
6. The kernel validates the workflow and creates a new canonical run directory.
7. Before mutable execution, the workspace service creates a managed branch and worktree from the committed base ref and returns `WorkspaceContext`.
8. The kernel writes run metadata including workspace context into the canonical run directory.
9. For each workflow step, the kernel:
   - assembles and persists policy summary,
   - enforces hard policy violations,
   - dispatches the step by opcode,
   - records step artifacts and manifest entries,
   - appends provenance events,
   - routes deterministically to the next step.
10. When the workflow reaches `STOP`, or when it fails terminally, the kernel writes terminal metadata and `final-state.txt`.
11. The headless app service returns a typed summary including run paths and workspace context.

## Step Execution Model

The kernel currently understands six opcodes conceptually:

- `RUN_AGENT`
- `RUN_VALIDATION`
- `EVALUATE`
- `GATE`
- `ROLLBACK`
- `STOP`

The current maintained bootstrap slice supports a smaller operational subset:

- `RUN_AGENT`
- `RUN_VALIDATION`
- `ROLLBACK(pre_run)`
- `STOP`

Bootstrap intentionally fails closed on:

- `EVALUATE`
- `GATE`

That is an important current-state fact for designers: the semantic control surface is architecturally central, but not yet part of the maintained bootstrap entry path.

## Evidence and Boundary Model

There are two major runtime boundaries that must remain distinct.

### Canonical Run Directory

This is the durable execution record.

It contains:

- run metadata,
- final state,
- ordered events,
- step manifests,
- canonical artifacts by role.

Consumers should resolve evidence from manifests and artifact roles, not by guessing filenames.

### Managed Worktree

This is the mutable execution boundary.

It contains:

- the checked-out repository state for the run,
- agent edits,
- validator execution context,
- rollback target state through the recorded base commit.

The system is healthier when these boundaries stay clean:

- the run directory is for review, provenance, and later evaluation,
- the worktree is for mutation and execution.

## Current Maintained Blueprint

If a new engineer wants the shortest accurate picture of the system today, it is this:

```text
tnh-conductor CLI
  -> HeadlessBootstrapService
    -> BootstrapKernelFactory
      -> KernelRunService
        -> GitWorktreeWorkspaceService
        -> DelegatingRunnerService
          -> Codex CLI adapter / Claude CLI adapter
        -> ValidationService
          -> builtin command resolver / harness backend
        -> FilesystemRunArtifactStore
        -> ExecutionPolicyAssembler
```

This is the maintained vertical slice that now matters most.

## Maintained Versus Non-Maintained Areas

New design work should distinguish clearly between the current maintained bootstrap line and older or reference-only areas.

### Primary Maintained Line

- `app/`
- `kernel/`
- `workspace/`
- `runners/`
- `validation/`
- `run_artifacts/`
- `execution_policy/`
- `execution/`
- `cli_tools/tnh_conductor/`

### Reference, Spike, or Transitional Areas

- `spike/` is preserved exploratory code from earlier protocol work.
- `codex_harness/` is a paused spike surface, not the maintained bootstrap runtime.
- `cli_tools/tnh_conductor_spike/` is a spike CLI, not the maintained entry point.
- `conductor_mvp/` represents an earlier orchestration line and is useful for historical context and tests, but it is not the preferred current entry surface for bootstrap work.

This distinction matters because architectural evaluation can get muddy if reference-only lines are treated as equal to the maintained runtime.

## What This Blueprint Suggests for Design Evaluation

When evaluating proposed work, the first questions should be:

1. does this strengthen the real maintained bootstrap line, or only add architecture around it,
2. which boundary is it changing: app, kernel, workspace, runners, validation, policy, or artifacts,
3. does it preserve the run-directory versus worktree separation,
4. does it improve the system's eventual ability to do long-horizon, repository-native engineering work,
5. is it a bootstrap-critical addition, or a follow-on surface that should wait until the maintained loop is exercised more.

That lens keeps this blueprint aligned with the direction memo instead of turning it into another abstract subsystem catalog.

## Suggested Reading Order

For fast onboarding, read in this order:

1. [/docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md](/docs/architecture/agent-orchestration/notes/bootstrap-direction-design-memo.md)
2. [/docs/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md](/docs/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
3. [/docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md](/docs/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
4. [/docs/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md](/docs/architecture/agent-orchestration/adr/adr-oa04.2-runner-contract.md)
5. [/docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md](/docs/architecture/agent-orchestration/adr/adr-oa04.3-provenance-run-artifact-contract.md)
6. [/docs/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md](/docs/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)
7. [/docs/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md](/docs/architecture/agent-orchestration/adr/adr-oa07-diff-policy-safety-rails.md)
8. [/docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md](/docs/architecture/agent-orchestration/adr/adr-oa07.1-worktree-lifecycle-and-rollback.md)

## Closing View

The most important thing to understand is that the architecture is no longer just a conceptual conductor diagram.

It now has a real maintained spine:

- one headless CLI,
- one thin app-layer bootstrap service,
- one deterministic kernel,
- one canonical artifact contract,
- one managed worktree boundary,
- one normalized runner and validation path.

That spine is still intentionally incomplete on semantic control, prompt-library runtime depth, and PR automation. But it is now coherent enough that future design work can be judged against a real executable architecture rather than against a theoretical platform.
