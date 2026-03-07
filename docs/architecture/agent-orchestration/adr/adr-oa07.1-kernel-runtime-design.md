---
title: "ADR-OA07.1: Kernel Runtime Design"
description: "Defines the maintained kernel subsystem for tnh-conductor MVP, including package boundary, internal collaborators, and ownership of workflow execution semantics."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: accepted
created: "2026-03-06"
parent_adr: "adr-oa07-mvp-runtime-architecture-strategy.md"
related_adrs:
  - "adr-oa04-workflow-schema-opcode-semantics.md"
  - "adr-oa04.1-implementation-notes-mvp-buildout.md"
  - "adr-oa04.2-mvp-hardening-compliance-plan.md"
  - "adr-os01-object-service-architecture-v3.md"
---

# ADR-OA07.1: Kernel Runtime Design

Defines the maintained kernel subsystem for tnh-conductor MVP, including package boundary, internal collaborators, and ownership of workflow execution semantics.

- **Status**: Accepted
- **Type**: Design Detail
- **Date**: 2026-03-06
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-mvp-runtime-architecture-strategy.md)
- **Related ADRs**:
  - [ADR-OA04](/architecture/agent-orchestration/adr/adr-oa04-workflow-schema-opcode-semantics.md)
  - [ADR-OA04.1](/architecture/agent-orchestration/adr/adr-oa04.1-implementation-notes-mvp-buildout.md)
  - [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-mvp-hardening-compliance-plan.md)
  - [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA04 defines the workflow schema and deterministic opcode semantics. ADR-OA07 establishes that the maintained MVP runtime will be organized into explicit subsystems, with `kernel/` as the deterministic execution core.

The current prototype kernel lives primarily in `conductor_mvp/`, especially:

- `models.py`
- `service.py`
- `adapters/workflow_loader.py`

The existing code proves the execution loop, but its package boundary and collaborator structure are still prototype-shaped:

- schema models, graph indexing, validation, runtime dispatch, trace state, and artifact result building are mixed too closely
- the kernel service directly knows too much about runner/validation result details
- several helper responsibilities are embedded as private methods instead of explicit kernel collaborators

Before runner and validation redesign proceeds, the kernel boundary must be fixed. Otherwise later subsystems will anchor to an unstable core.

### Kernel Definition

For agent-orchestration, the kernel means:

> the deterministic execution core that interprets validated workflow bytecode, dispatches opcode behavior to external collaborators, and advances workflow state according to OA04 rules.

The kernel is not:

- a runner implementation
- a validator implementation
- a workspace implementation
- an artifact persistence implementation
- a planner intelligence layer

It coordinates those capabilities through typed protocols, but it does not absorb their domain logic.

### Implementation Guidance

Within the kernel subsystem, favor the lightest collaborator structure that keeps OA04 semantics explicit and testable.

That means:

- split responsibilities where ownership is genuinely distinct
- avoid adding extra layers simply to mirror external object-service patterns
- keep kernel-internal helpers simple if they do not cross unstable boundaries

---

## Decision

### 1. The maintained kernel package is `agent_orchestration/kernel/`

`conductor_mvp/` is a prototype implementation package. The maintained execution core will live under `agent_orchestration/kernel/`.

This package owns:

- workflow domain models required by deterministic execution
- workflow loading and normalization adapters
- graph/catalog helpers
- workflow static validation
- kernel runtime state
- step dispatch and transition logic
- kernel run result assembly

### 2. The kernel will be decomposed into explicit collaborators

The current `service.py` prototype combines too many responsibilities. The maintained kernel will instead use explicit collaborators with narrow concerns.

Minimum required collaborator set:

#### A. `WorkflowCatalog`

Owns indexed access to workflow graph structure.

Responsibilities:

- step lookup by id
- route target lookup
- transition target enumeration
- graph traversal helpers

This is a read-only structural helper over `WorkflowDefinition`.

#### B. `WorkflowValidator`

Owns static validation of workflow definitions before execution.

Responsibilities:

- entry step validation
- unique id validation
- route target validation
- `EVALUATE` contract validation
- reachability validation
- static golden/gate constraints

This collaborator must enforce OA04 workflow invariants, not runtime outcomes.

#### C. `KernelState`

Owns mutable execution progress as an immutable typed value.

Responsibilities:

- current step id
- runtime flags required for deterministic routing constraints
- trace entries

It must not carry infrastructure-specific payloads or external collaborator state.

#### D. `StepExecutor`

Owns opcode dispatch at runtime.

Responsibilities:

- invoke the correct external collaborator for each executable step type
- translate collaborator results into kernel transition decisions
- apply route transitions using `WorkflowCatalog`
- enforce runtime-only kernel rules

It must not perform static workflow validation or artifact persistence policy outside its kernel obligations.

#### E. `KernelRunService`

Owns top-level execution orchestration.

Responsibilities:

- validate workflow before execution
- create run-scoped kernel context
- iterate the execution loop
- stop on terminal state
- persist kernel-owned run outputs through artifact protocols

This is the maintained replacement for the current monolithic `ConductorKernelService`.

### 3. The kernel owns deterministic workflow semantics only

The kernel owns:

- opcode dispatch
- route resolution
- state transitions
- `STOP` termination
- deterministic enforcement of OA04 routing rules
- runtime gating constraints that follow from workflow semantics

The kernel does not own:

- subprocess command construction
- CLI invocation mechanics
- validator execution mechanics
- git implementation details
- event formatting policy beyond kernel-owned events
- planner reasoning internals

### 4. The kernel depends on typed subsystem protocols

The kernel must depend only on typed protocols for external execution surfaces.

Required protocol families:

- runner protocol(s) for `RUN_AGENT`
- validation protocol(s) for `RUN_VALIDATION`
- planner-evaluator protocol for `EVALUATE`
- gate-approver protocol for `GATE`
- workspace protocol for rollback/checkpoint behavior
- run-artifact protocol for kernel-owned persistence
- clock and run-id protocols

No low-level transport shapes such as argv lists, subprocess payloads, or raw dict transport objects may cross into the kernel package boundary.

MVP guidance for the thin kernel-boundary protocols:

- `ClockProtocol`: returns the current timestamp only
- `RunIdGeneratorProtocol`: derives a run id from typed time input only
- `GateApproverProtocol`: accepts typed gate context and returns a typed gate outcome only

These should remain narrow typed protocols, not separate subsystem designs, unless later implementation pressure proves they need more structure.

### 5. Workflow loading remains an adapter concern, but under kernel ownership

Workflow YAML loading belongs with the kernel because it translates external workflow documents into kernel-owned workflow models.

However:

- normalization logic must remain confined to the adapter layer
- semantic validation belongs to `WorkflowValidator`, not the loader
- the loader should produce typed kernel models as quickly as possible

Implementation note from current repo survey:

- TNH Scholar does not currently have a generalized YAML subsystem to reuse here
- existing YAML usage is light and mostly follows the same pattern: `yaml.safe_load(...)` followed quickly by validation into typed models
- the maintained kernel loader should follow that same thin-adapter pattern rather than introducing a new generic YAML utility prematurely

### 6. Kernel models should represent execution semantics, not downstream provider internals

Kernel-owned models should include:

- opcode enums
- planner statuses
- gate outcomes
- step definitions
- workflow definitions
- kernel state
- kernel run result

Kernel models should not include infrastructure detail that belongs to subsystem-specific domains unless that detail is required for deterministic kernel behavior.

This has an important consequence:

- typed validator command objects should not live in `kernel/`
- typed runner command objects should not live in `kernel/`

The kernel may refer only to subsystem-level runner and validator request/result contracts at protocol boundaries. Based on OA07.2, that means:

- the kernel may depend on minimal typed runner request/result models
- the kernel must not depend on subprocess-oriented execution models
- richer runner-internal request/result or output-normalization models stay inside `runners/`
- the same rule is expected to apply to validation once OA07.3 is defined

### 7. Runtime golden-gate enforcement remains kernel-owned

The current runtime rule:

- if generated goldens are proposed and the planner emits a success path directly to `STOP`, the workflow must fail because the path did not pass through `GATE`

belongs in the kernel.

Rationale:

- it is a deterministic workflow-governance rule
- it derives from workflow semantics, not validator internals
- it should not be delegated to the planner or validator subsystem

### 8. Kernel decomposition should preserve OA04 semantics without re-deciding them

`OA07.1` does not change:

- supported opcode set
- route semantics
- planner status semantics
- `RUN_VALIDATION` as an opcode
- `GATE` or `ROLLBACK` meaning

It only defines where those semantics are implemented and enforced in the maintained codebase.

---

## Target Package Shape

The maintained kernel should converge on a shape like:

```text
agent_orchestration/kernel/
  __init__.py
  models.py                 # workflow + kernel-owned runtime models
  protocols.py              # kernel-facing subsystem protocols only
  errors.py                 # kernel exceptions
  catalog.py                # WorkflowCatalog
  validator.py              # WorkflowValidator
  state.py                  # KernelState and trace helpers
  executor.py               # StepExecutor
  service.py                # KernelRunService
  adapters/
    __init__.py
    workflow_loader.py      # YAML -> typed workflow models
```

Notes:

- `errors.py` is separated so validation/runtime errors stop living in `service.py`
- `executor.py` exists to keep opcode dispatch out of the top-level run loop
- `protocols.py` should stay small and only declare what the kernel actually needs from external subsystems

---

## Consequences

### Positive

- Gives the maintained runtime a clear deterministic core before subsystem migration proceeds.
- Prevents runner/validation redesign from coupling to a prototype-shaped kernel.
- Makes OA04 semantic ownership explicit and reviewable.
- Reduces the size and cognitive load of the current `conductor_mvp/service.py` implementation.

### Negative

- Introduces package churn before feature growth continues.
- Forces a deliberate migration from `conductor_mvp/` to `kernel/`.
- Requires careful boundary discipline so execution-specific models do not leak back into the kernel.

---

## Alternatives Considered

### 1. Keep `conductor_mvp/` as the maintained kernel package

Rejected. The name reflects prototype history rather than maintained subsystem responsibility.

### 2. Keep catalog, validation, and execution logic together in one service module

Rejected. This preserves the current low-cohesion prototype structure.

### 3. Move workflow loading outside the kernel package

Rejected. Loading workflow documents into kernel-owned models is part of the kernel boundary, even if it remains an adapter concern.

---

## Open Questions

1. Which minimal runner/validation result fields should be visible to the kernel as stable protocol contracts, and which should remain subsystem-private implementation detail?
2. Should kernel trace remain a simple list of strings in MVP, or move immediately to a typed event/trace entry model?
